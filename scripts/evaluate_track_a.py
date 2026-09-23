"""Run the isolated Track A judgment evaluation against its frozen fixture."""

import json
import statistics
from collections import defaultdict
from pathlib import Path

from spendguard.decision_prototype import (
    PrototypeExecutionError,
    append_sanitized_log,
    build_prototype_client,
    fixture_sha256,
    judge,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals" / "track_a_cases.json"
LOG = ROOT / "docs" / "results" / "track-a-jev-decisions.jsonl"


def main() -> None:
    dataset = json.loads(FIXTURE.read_text(encoding="utf-8"))
    client = build_prototype_client()
    groups: dict[str, list[dict[str, object]]] = defaultdict(list)
    total_input = total_output = 0
    failures = 0
    try:
        for case in dataset["cases"]:
            try:
                result = judge(case["judgment_id"], case["state"], client=client)
            except PrototypeExecutionError as error:
                failures += 1
                groups[case["judgment_id"]].append(
                    {
                        "id": case["id"],
                        "expected": case["expected"],
                        "actual": "unknown",
                        "abstained": True,
                        "latency_ms": None,
                        "input_tokens": None,
                        "output_tokens": None,
                        "cost_usd": None,
                        "error_type": error.cause_type,
                        "status_code": error.status_code,
                    }
                )
                continue
            append_sanitized_log(LOG, case_id=case["id"], result=result, expected=case["expected"])
            actual = result.typed_result
            groups[case["judgment_id"]].append(
                {
                    "id": case["id"],
                    "expected": case["expected"],
                    "actual": actual,
                    "abstained": result.abstained,
                    "score": result.score,
                    "confidence": result.confidence,
                    "latency_ms": result.latency_ms,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "cost_usd": result.estimated_cost_usd,
                }
            )
            total_input += result.input_tokens or 0
            total_output += result.output_tokens or 0
    finally:
        client.close()

    judgment_reports = {}
    for judgment_id, outcomes in groups.items():
        compared = [
            row for row in outcomes
            if row["actual"] != "needs_review" and row.get("error_type") is None
        ]
        correct = sum(
            row["expected"] == row["actual"]
            for row in outcomes
            if row.get("error_type") is None
        )
        fp = sum(row["expected"] in {"no", "not_relevant"} and row["actual"] in {"yes", "relevant"} for row in compared)
        fn = sum(row["expected"] in {"yes", "relevant"} and row["actual"] in {"no", "not_relevant"} for row in compared)
        latency = [row["latency_ms"] for row in outcomes if row["latency_ms"] is not None]
        noul_rows = [row for row in outcomes if row.get("score") is not None and row.get("error_type") is None]
        brier = (
            sum(
                (row["score"] - (1.0 if row["expected"] == "yes" else 0.0)) ** 2
                for row in noul_rows
            ) / len(noul_rows)
            if noul_rows
            else None
        )
        judgment_reports[judgment_id] = {
            "cases": len(outcomes),
            "correct": correct,
            "accuracy": correct / len(outcomes) if outcomes else None,
            "selective_accuracy": correct / len(compared) if compared else None,
            "false_positive": fp,
            "false_negative": fn,
            "abstain_rate": sum(row["abstained"] for row in outcomes) / len(outcomes),
            "mean_latency_ms": statistics.mean(latency) if latency else None,
            "noul_brier_score": brier,
            "outcomes": outcomes,
        }
    print(
        json.dumps(
            {
                "dataset_version": dataset["dataset_version"],
                "fixture_sha256": fixture_sha256(FIXTURE),
                "judgments": judgment_reports,
                "provider_failures": failures,
                "usage": {"input_tokens": total_input, "output_tokens": total_output},
                "cost": {
                    "input_cost_usd": total_input * 0.042 / 1_000_000,
                    "output_cost_usd": 0.0,
                    "total_cost_usd": total_input * 0.042 / 1_000_000,
                    "price_source": "https://typesafe.ai/blog/introducing-system-one-models-and-jev",
                    "price_checked": "2026-09-23",
                },
                "workflow": {"details": "See evaluate_track_a_workflow.py; this command evaluates isolated judgments only."},
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
