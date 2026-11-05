"""Live Groq tool-selection evaluation; never executes a GitHub tool."""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from client.mcp_client import GitHubMCPClient
from evaluation.test_cases import TEST_CASES

load_dotenv()
PREDICTIONS_FILE = Path(__file__).parent / "results.json"
DEFAULT_MIN_ACCURACY = 90.0


def threshold():
    value = float(os.getenv("EVALUATION_MIN_ACCURACY", "90"))
    if not math.isfinite(value) or not 90 <= value <= 100:
        raise ValueError("Evaluation threshold must be between 90 and 100")
    return value


async def get_available_tools(client):
    return [{"type": "function", "function": {
        "name": t["name"], "description": t["description"],
        "parameters": t["input_schema"],
    }} for t in await client.list_tools()]


def predict_tool(groq, tools, question):
    catalog = [{"name": t["function"]["name"],
                "description": t["function"]["description"]} for t in tools]
    response = groq.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
        messages=[
            {"role": "system", "content": (
                'Select exactly one tool for the request. Do not execute it. '
                'Return only JSON with exactly one key: {"tool":"exact_tool_name"}. '
                'Available tools: ' + json.dumps(catalog, sort_keys=True))},
            {"role": "user", "content": question},
        ], temperature=0, seed=42, reasoning_effort="low", max_completion_tokens=4096,
        response_format={"type": "json_schema", "json_schema": {
            "name": "tool_selection", "strict": True,
            "schema": {"type": "object", "properties": {
                "tool": {"type": "string", "enum": sorted(t["function"]["name"] for t in tools)}
            }, "required": ["tool"], "additionalProperties": False},
        }},
    )
    result = json.loads(response.choices[0].message.content or "")
    valid = {t["function"]["name"] for t in tools}
    if (not isinstance(result, dict) or set(result) != {"tool"}
            or not isinstance(result["tool"], str) or result["tool"] not in valid):
        raise ValueError("Invalid tool-selection response")
    return result["tool"]


def evaluate_cases(predict, cases, minimum=90.0):
    if not math.isfinite(minimum) or not 90 <= minimum <= 100:
        raise ValueError("Evaluation threshold must be between 90 and 100")
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Cases must be nonempty with unique IDs")
    results = []
    for case in cases:
        predicted = None
        error = None
        try:
            predicted = predict(case["question"])
            if not isinstance(predicted, str) or not predicted:
                raise ValueError("Missing prediction")
            status = "correct" if predicted == case["expected_tool"] else "wrong"
        except Exception as exc:
            # Exception text and raw provider responses may contain sensitive data.
            error = type(exc).__name__
            status = "error"
        results.append({**case, "predicted_tool": predicted, "status": status,
                        "error_type": error})
        detail = f" ({error})" if error else ""
        print(f"Case {case['id']}: {status}{detail}", flush=True)
    correct = sum(r["status"] == "correct" for r in results)
    errors = sum(r["status"] == "error" for r in results)
    rate = correct * 100 / len(cases)
    return {"total": len(cases), "correct": correct,
            "wrong": len(cases) - correct - errors, "errors": errors,
            "pass_rate": rate, "minimum": minimum,
            "passed": errors == 0 and rate >= minimum, "cases": results}


async def run_evaluation():
    # Remove stale success evidence before any startup operation can fail.
    PREDICTIONS_FILE.unlink(missing_ok=True)
    minimum = threshold()
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    # SDK retries connection errors, 408, 409, 429 and 5xx twice with backoff.
    with Groq(api_key=key, timeout=30.0, max_retries=2) as groq:
        if model not in {m.id for m in groq.models.list().data}:
            raise RuntimeError("Configured model is unavailable to this account")
        client = GitHubMCPClient()
        try:
            await asyncio.wait_for(client.connect(), timeout=60)
            tools = await asyncio.wait_for(get_available_tools(client), timeout=30)
            names = {t["function"]["name"] for t in tools}
            if not {c["expected_tool"] for c in TEST_CASES} <= names:
                raise RuntimeError("Tool catalog does not cover the evaluation cases; use full local catalog")
            report = evaluate_cases(lambda q: predict_tool(groq, tools, q), TEST_CASES, minimum)
            report.update({"mode": "live", "model": model, "seed": 42,
                           "temperature": 0, "reasoning_effort": "low", "max_completion_tokens": 4096, "response_format": "strict_json_schema", "timestamp": datetime.now(timezone.utc).isoformat(),
                           "cases_sha256": hashlib.sha256(json.dumps(TEST_CASES, sort_keys=True).encode()).hexdigest(),
                           "catalog_sha256": hashlib.sha256(json.dumps(tools, sort_keys=True).encode()).hexdigest()})
            PREDICTIONS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
            return report["passed"]
        finally:
            await client.close()


def main():
    try:
        passed = asyncio.run(run_evaluation())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        print(f"Evaluation infrastructure failure: {type(exc).__name__}")
        raise SystemExit(1)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
