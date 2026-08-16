import asyncio
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

from client.mcp_client import GitHubMCPClient
from evaluation.test_cases import TEST_CASES


load_dotenv()


PREDICTIONS_FILE = Path(__file__).parent / "predictions.json"

MODEL = "llama-3.1-8b-instant"


# ============================================================
# Groq Tool Selection
# ============================================================

async def get_available_tools(
    client: GitHubMCPClient,
) -> list[dict[str, Any]]:

    mcp_tools = await client.list_tools()

    tools = []

    for tool in mcp_tools:

        tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"],
                },
            }
        )

    return tools


def predict_tool(
    groq: Groq,
    tools: list[dict[str, Any]],
    question: str,
) -> str | None:

    tool_descriptions = []

    for tool in tools:

        function = tool["function"]

        tool_descriptions.append(
            {
                "name": function["name"],
                "description": function["description"],
            }
        )

    system_prompt = f"""
You are evaluating a GitHub MCP server.

Your ONLY task is to select the single best MCP tool
for the user's request.

You must choose EXACTLY ONE tool from this list:

{json.dumps(tool_descriptions, indent=2)}

Rules:

1. Select ONLY a tool whose exact name appears in the list.
2. Never invent, modify, prefix, suffix, or rename a tool.
3. Do not execute the tool.
4. Do not answer the user's question.
5. Return ONLY valid JSON.
6. The JSON must have exactly this format:

{{"tool": "exact_tool_name"}}

Example:

{{"tool": "get_repository"}}

Do not return Markdown.
Do not return explanations.
"""

    response = groq.chat.completions.create(
        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],

        temperature=0,
    )

    content = response.choices[0].message.content

    if not content:
        return None

    try:

        result = json.loads(content)

    except json.JSONDecodeError:

        # Try to recover JSON if the model accidentally
        # wrapped it in extra text.
        start = content.find("{")
        end = content.rfind("}")

        if start == -1 or end == -1:
            return None

        try:
            result = json.loads(
                content[start:end + 1]
            )
        except json.JSONDecodeError:
            return None

    predicted_tool = result.get("tool")

    valid_tools = {
        tool["function"]["name"]
        for tool in tools
    }

    if predicted_tool not in valid_tools:
        print(
            f"  Invalid tool selected: "
            f"{predicted_tool}"
        )

        return None

    return predicted_tool


# ============================================================
# Evaluation
# ============================================================

async def run_evaluation():

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    groq = Groq(api_key=api_key)

    client = GitHubMCPClient()

    await client.connect()

    try:

        tools = await get_available_tools(client)

        print("=" * 60)
        print(
            "GitHub MCP Server Tool Selection Evaluation"
        )
        print("=" * 60)

        print(
            f"Total test cases : {len(TEST_CASES)}"
        )

        predictions = []

        correct = 0
        wrong = 0
        failed = 0

        for case in TEST_CASES:

            case_id = case["id"]

            question = case["question"]

            expected_tool = case["expected_tool"]

            print(
                f"\n[{case_id}/"
                f"{len(TEST_CASES)}] "
                f"{question}"
            )

            try:

                predicted_tool = predict_tool(
                    groq,
                    tools,
                    question,
                )

            except Exception as exc:

                print(
                    f"  ERROR: {exc}"
                )

                predicted_tool = None

            # --------------------------------------------
            # Determine result
            # --------------------------------------------

            if predicted_tool is None:

                status = "TOOL_FAILED"

                failed += 1

            elif predicted_tool == expected_tool:

                status = "CORRECT"

                correct += 1

            else:

                status = "WRONG_TOOL"

                wrong += 1

            print(
                f"  Expected : {expected_tool}"
            )

            print(
                f"  Predicted: {predicted_tool}"
            )

            print(
                f"  Status   : {status}"
            )

            predictions.append(
                {
                    "id": case_id,
                    "predicted_tool": predicted_tool,
                }
            )

        # --------------------------------------------
        # Save predictions
        # --------------------------------------------

        with open(
            PREDICTIONS_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                predictions,
                file,
                indent=4,
            )

        evaluated = (
            correct
            + wrong
            + failed
        )

        accuracy = (
            (correct / evaluated) * 100
            if evaluated
            else 0
        )

        # --------------------------------------------
        # Summary
        # --------------------------------------------

        print("\n")

        print("=" * 60)
        print(
            "Evaluation Complete"
        )
        print("=" * 60)

        print(
            f"Total test cases : {len(TEST_CASES)}"
        )

        print(
            f"Evaluated        : {evaluated}"
        )

        print(
            f"Correct          : {correct}"
        )

        print(
            f"Wrong Tool       : {wrong}"
        )

        print(
            f"Tool Failed      : {failed}"
        )

        print(
            f"Accuracy         : {accuracy:.2f}%"
        )

        print("=" * 60)

        print(
            f"\nPredictions saved to:"
        )

        print(
            PREDICTIONS_FILE
        )

    finally:

        await client.close()


# ============================================================
# Entry Point
# ============================================================

def main():

    try:

        asyncio.run(
            run_evaluation()
        )

    except KeyboardInterrupt:

        print(
            "\nEvaluation stopped."
        )


if __name__ == "__main__":

    main()