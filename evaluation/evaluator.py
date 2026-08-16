import json
from pathlib import Path

from evaluation.test_cases import TEST_CASES


PREDICTIONS_FILE = Path(__file__).parent / "predictions.json"


def evaluate(predictions: list[dict]) -> None:
    expected = {
        case["id"]: case["expected_tool"]
        for case in TEST_CASES
    }

    total = len(TEST_CASES)
    correct = 0
    wrong = 0
    failed = 0

    results = []

    for prediction in predictions:

        case_id = prediction.get("id")
        predicted_tool = prediction.get(
            "predicted_tool"
        )

        if case_id not in expected:
            continue

        expected_tool = expected[case_id]

        if not predicted_tool:
            status = "TOOL_FAILED"
            failed += 1

        elif predicted_tool == expected_tool:
            status = "CORRECT"
            correct += 1

        else:
            status = "WRONG_TOOL"
            wrong += 1

        results.append(
            {
                "id": case_id,
                "expected_tool": expected_tool,
                "predicted_tool": predicted_tool,
                "status": status,
            }
        )

    evaluated = correct + wrong + failed

    accuracy = (
        (correct / evaluated) * 100
        if evaluated
        else 0
    )

    print("=" * 60)
    print("GitHub MCP Server Tool Selection Evaluation")
    print("=" * 60)

    print(f"Total test cases : {total}")
    print(f"Evaluated        : {evaluated}")
    print(f"Correct          : {correct}")
    print(f"Wrong Tool       : {wrong}")
    print(f"Tool Failed      : {failed}")
    print(f"Accuracy         : {accuracy:.2f}%")

    print("=" * 60)

    for result in results:
        print(
            f"[{result['status']}] "
            f"#{result['id']} "
            f"expected={result['expected_tool']} "
            f"predicted={result['predicted_tool']}"
        )


def main() -> None:

    if not PREDICTIONS_FILE.exists():
        print(
            "predictions.json not found."
        )
        print(
            "Create evaluation/predictions.json "
            "before running the evaluator."
        )
        return

    with open(
        PREDICTIONS_FILE,
        "r",
        encoding="utf-8",
    ) as file:
        predictions = json.load(file)

    evaluate(predictions)


if __name__ == "__main__":
    main()