"""Run the fixed Phase 2 Jev intent evaluation."""

import json
from pathlib import Path

from spendguard.jev import JevIntentClassifier
from spendguard.phase2_evaluation import evaluate_cases


CASES_PATH = Path("evals/phase1_cases.json")


def main() -> None:
    """Jev evaluation entry point."""

    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    classifier = JevIntentClassifier()
    try:
        report = evaluate_cases(cases, classifier)
    finally:
        classifier.close()

    print(report.model_dump_json(indent=2))
    if not report.evaluation_success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
