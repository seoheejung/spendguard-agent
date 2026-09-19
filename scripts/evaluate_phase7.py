"""Run the reproducible Phase 7 end-to-end workflow evaluation."""

import asyncio
import json

from spendguard.phase7_evaluation import evaluate_fixed_workflow, load_fixed_dataset


if __name__ == "__main__":
    report = asyncio.run(evaluate_fixed_workflow(load_fixed_dataset()))
    print(json.dumps(report, ensure_ascii=False, indent=2))
