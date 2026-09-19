"""Run the fixed Phase 1 intent evaluation against the configured OpenAI agent."""

import asyncio
import json
from pathlib import Path

from spendguard.agent import AgentExecutionError, OpenAIAnalyzer


CASES_PATH = Path("evals/phase1_cases.json")


async def main() -> None:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    analyzer = OpenAIAnalyzer()
    outcomes = []
    api_errors = []

    for case in cases:
        try:
            result = await analyzer.analyze(case["input"])
        except AgentExecutionError as error:
            outcomes.append(
                {
                    "id": case["id"],
                    "expected_intent": case["expected_intent"],
                    "actual_intent": None,
                    "correct": False,
                }
            )
            api_errors.append(
                {
                    "id": case["id"],
                    "error_type": type(error.__cause__).__name__ if error.__cause__ else type(error).__name__,
                    "message": str(error),
                }
            )
            continue
        outcomes.append(
            {
                "id": case["id"],
                "expected_intent": case["expected_intent"],
                "actual_intent": result.intent,
                "correct": result.intent == case["expected_intent"],
            }
        )

    correct = sum(outcome["correct"] for outcome in outcomes)
    report = {
        "total_cases": len(outcomes),
        "correct_intents": correct,
        "accuracy": correct / len(outcomes),
        "failures": [outcome for outcome in outcomes if not outcome["correct"]],
        "api_errors": api_errors,
        "evaluation_success": len(api_errors) == 0 and len(outcomes) == len(cases),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["evaluation_success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
