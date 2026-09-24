"""Validate the frozen sparse-question fixture and score later, annotated runs offline.

Optional observations JSON:
{
  "dataset_version": "chapter-b-sparse-v1",
  "fixture_sha256": "<hash from fixture-only report>",
  "runs": [{
    "case_id": "price-comparison-001",
    "status": "result",
    "answer": "<actual user-facing answer>",
    "search_called": true,
    "mcp_called": true,
    "must_include_checks": {"current_offers": true, "price_difference": true},
    "failure_condition_checks": {"required_data_block": false, "unsupported_offer": false}
  }]
}

Checks are human-reviewed observations, not inferred from the answer text.
Missing runs remain not_run and are never counted as passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evals" / "chapter_b_sparse_v1.json"
SCENARIOS = {
    "price-comparison",
    "subscription-audit",
    "mobile-plan",
    "insurance-overlap",
    "card-benefits",
    "impulse-purchase",
    "grocery-budget",
    "travel-budget",
    "car-ownership",
    "installment",
    "refinance",
    "quote-audit",
    "price-negotiation",
    "annual-leaks",
    "purchase-review",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    require(isinstance(data, dict), f"{path}: expected JSON object")
    return data, hashlib.sha256(raw).hexdigest()


def check_text_list(value: object, label: str) -> None:
    require(isinstance(value, list) and bool(value), f"{label}: expected nonempty list")
    require(all(isinstance(item, str) and item.strip() for item in value), f"{label}: expected nonempty strings")


def criterion_ids(value: object, label: str) -> set[str]:
    require(isinstance(value, list) and bool(value), f"{label}: expected nonempty list")
    ids: list[str] = []
    for item in value:
        require(isinstance(item, dict), f"{label}: expected criterion object")
        require(isinstance(item.get("id"), str) and bool(item["id"].strip()), f"{label}: missing id")
        require(isinstance(item.get("criterion"), str) and bool(item["criterion"].strip()), f"{label}: missing criterion")
        ids.append(item["id"])
    require(len(ids) == len(set(ids)), f"{label}: duplicate criterion id")
    return set(ids)


def validate_cases(data: dict) -> dict[str, dict]:
    require(data.get("dataset_version") == "chapter-b-sparse-v1", "unexpected dataset version")
    cases = data.get("cases")
    require(isinstance(cases, list) and len(cases) == 15, "expected exactly 15 cases")
    by_id: dict[str, dict] = {}
    scenarios: set[str] = set()
    for case in cases:
        require(isinstance(case, dict), "case must be an object")
        case_id = case.get("id")
        require(isinstance(case_id, str) and bool(case_id.strip()), "case missing id")
        scenario = case_id.rsplit("-", 1)[0]
        require(case_id not in by_id, f"duplicate case id: {case_id}")
        require(scenario in SCENARIOS, f"{case_id}: unknown scenario")
        require(scenario not in scenarios, f"duplicate scenario: {scenario}")
        require(case_id.startswith(f"{scenario}-"), f"{case_id}: id/scenario mismatch")
        for key in ("scenario", "question"):
            require(isinstance(case.get(key), str) and bool(case[key].strip()), f"{case_id}: missing {key}")
        for key in ("user_facts", "allowed_assumptions"):
            check_text_list(case.get(key), f"{case_id}.{key}")
        for key in ("search_needed", "mcp_needed"):
            require(type(case.get(key)) is bool, f"{case_id}.{key}: expected bool")
        criterion_ids(case.get("must_include"), f"{case_id}.must_include")
        failures = criterion_ids(case.get("failure_conditions"), f"{case_id}.failure_conditions")
        require("required_data_block" in failures, f"{case_id}: missing required_data_block failure")
        by_id[case_id] = case
        scenarios.add(scenario)
    require(scenarios == SCENARIOS, f"scenario coverage mismatch: {sorted(SCENARIOS - scenarios)}")
    return by_id


def check_flags(value: object, expected: set[str], label: str) -> dict[str, bool]:
    require(isinstance(value, dict) and set(value) == expected, f"{label}: check ids do not match fixture")
    require(all(type(flag) is bool for flag in value.values()), f"{label}: expected boolean checks")
    return value


def evaluate_run(run: dict, case: dict) -> dict:
    case_id = case["id"]
    require(run.get("status") in {"result", "needs_input", "error"}, f"{case_id}: invalid status")
    require(isinstance(run.get("answer"), str), f"{case_id}: answer must be a string")
    if run["status"] == "result":
        require(bool(run["answer"].strip()), f"{case_id}: result needs actual answer text")
    for key in ("search_called", "mcp_called"):
        require(type(run.get(key)) is bool, f"{case_id}.{key}: expected bool")
    must = check_flags(
        run.get("must_include_checks"),
        criterion_ids(case["must_include"], f"{case_id}.must_include"),
        f"{case_id}.must_include_checks",
    )
    failures = check_flags(
        run.get("failure_condition_checks"),
        criterion_ids(case["failure_conditions"], f"{case_id}.failure_conditions"),
        f"{case_id}.failure_condition_checks",
    )
    reasons = []
    if run["status"] != "result":
        reasons.append(f"status:{run['status']}")
    reasons.extend(f"missing:{key}" for key, passed in must.items() if not passed)
    reasons.extend(f"failure:{key}" for key, occurred in failures.items() if occurred)
    for tool in ("search", "mcp"):
        if run[f"{tool}_called"] != case[f"{tool}_needed"]:
            reasons.append(f"{tool}_call_mismatch")
    return {"case_id": case_id, "scenario": case["scenario"], "outcome": "pass" if not reasons else "fail", "reasons": reasons}


def build_report(cases_data: dict, fixture_hash: str, observations: dict | None) -> dict:
    cases = validate_cases(cases_data)
    runs: dict[str, dict] = {}
    if observations is not None:
        require(observations.get("dataset_version") == cases_data["dataset_version"], "observation dataset version mismatch")
        require(observations.get("fixture_sha256") == fixture_hash, "observation fixture hash mismatch")
        raw_runs = observations.get("runs")
        require(isinstance(raw_runs, list), "observations.runs must be a list")
        for run in raw_runs:
            require(isinstance(run, dict), "run must be an object")
            case_id = run.get("case_id")
            require(case_id in cases, f"unknown case id: {case_id}")
            require(case_id not in runs, f"duplicate run: {case_id}")
            runs[case_id] = run
    results = [
        evaluate_run(runs[case_id], case) if case_id in runs else
        {"case_id": case_id, "scenario": case["scenario"], "outcome": "not_run", "reasons": []}
        for case_id, case in cases.items()
    ]
    return {
        "dataset_version": cases_data["dataset_version"],
        "fixture_sha256": fixture_hash,
        "status": "observations_scored" if runs else "fixture_valid_unmeasured",
        "summary": {
            "cases": len(results),
            "pass": sum(item["outcome"] == "pass" for item in results),
            "fail": sum(item["outcome"] == "fail" for item in results),
            "not_run": sum(item["outcome"] == "not_run" for item in results),
        },
        "results": results,
    }


def build_runtime_report(cases_data: dict, fixture_hash: str, runtime: dict, reviews: dict | None) -> dict:
    """Score observed Codex runs with separate human criterion checks."""

    cases = validate_cases(cases_data)
    require(runtime.get("fixture_sha256") == fixture_hash, "runtime fixture hash mismatch")
    require(runtime.get("mode") in {"baseline", "jev"}, "invalid runtime mode")
    raw_runs = runtime.get("runs")
    require(isinstance(raw_runs, list), "runtime.runs must be a list")
    by_id = {run["case_id"]: run for run in raw_runs}
    require(len(by_id) == len(raw_runs), "duplicate runtime case id")
    require(set(by_id) <= set(cases), "unknown runtime case id")
    reviewed = {}
    if reviews is not None:
        require(reviews.get("fixture_sha256") == fixture_hash, "review fixture hash mismatch")
        raw_reviews = reviews.get("reviews")
        require(isinstance(raw_reviews, list), "reviews must be a list")
        reviewed = {review["case_id"]: review for review in raw_reviews}
        require(len(reviewed) == len(raw_reviews), "duplicate review case id")
        require(set(reviewed) <= set(cases), "unknown review case id")
    results = []
    for case_id, case in cases.items():
        row = by_id.get(case_id)
        if row is None:
            results.append({"case_id": case_id, "outcome": "not_run"})
            continue
        metadata = row.get("metadata") or {}
        mcp_calls = metadata.get("mcp_calls") or []
        review = reviewed.get(case_id)
        metrics = {
            "e2e_latency_ms": row.get("e2e_latency_ms"),
            "codex_runs": metadata.get("codex_runs", 1),
            "search_calls": metadata.get("search_calls"),
            "mcp_calls": len(mcp_calls),
            "mcp_failures": sum(call.get("status") == "failed" or call.get("result") is None for call in mcp_calls),
            "jev_calls": metadata.get("jev_calls", 0),
            "jev_judgment": metadata.get("jev_judgment"),
            "attempts": row.get("attempts", 1),
            "timeout": "timed out" in str(row.get("error") or ""),
            "error": row.get("error"),
            "search_trace": [event for event in row.get("trace", []) if event.get("type") == "web_search"],
        }
        if review is None:
            results.append({"case_id": case_id, "scenario": case["scenario"], "outcome": "unreviewed", "metrics": metrics})
            continue
        observation = {
            "case_id": case_id,
            "status": "result" if row.get("status") == "ready" else "error",
            "answer": row.get("answer", ""),
            "search_called": bool(metadata.get("search_calls")),
            "mcp_called": bool(mcp_calls),
            "must_include_checks": review.get("must_include_checks"),
            "failure_condition_checks": review.get("failure_condition_checks"),
        }
        scored = evaluate_run(observation, case)
        scored["metrics"] = metrics
        scored["quality_note"] = review.get("quality_note", "")
        scored["jev_judgment_correct"] = review.get("jev_judgment_correct")
        results.append(scored)
    latencies = [row["e2e_latency_ms"] for row in raw_runs if isinstance(row.get("e2e_latency_ms"), int)]
    judgments = [result["jev_judgment_correct"] for result in results if result.get("jev_judgment_correct") is not None]
    return {
        "dataset_version": cases_data["dataset_version"],
        "fixture_sha256": fixture_hash,
        "mode": runtime["mode"],
        "summary": {
            "cases": len(cases),
            "pass": sum(result["outcome"] == "pass" for result in results),
            "fail": sum(result["outcome"] == "fail" for result in results),
            "unreviewed": sum(result["outcome"] == "unreviewed" for result in results),
            "not_run": sum(result["outcome"] == "not_run" for result in results),
            "search_calls": sum((row.get("metadata") or {}).get("search_calls") or 0 for row in raw_runs),
            "mcp_calls": sum(len((row.get("metadata") or {}).get("mcp_calls") or []) for row in raw_runs),
            "jev_calls": sum((row.get("metadata") or {}).get("jev_calls") or 0 for row in raw_runs),
            "codex_runs": sum((row.get("metadata") or {}).get("codex_runs", 1) for row in raw_runs),
            "median_e2e_latency_ms": statistics.median(latencies) if latencies else None,
            "total_e2e_latency_ms": sum(latencies),
            "timeouts": sum("timed out" in str(row.get("error") or "") for row in raw_runs),
            "errors": sum(row.get("status") != "ready" for row in raw_runs),
            "retries": sum(max(0, row.get("attempts", 1) - 1) for row in raw_runs),
            "jev_judgments_reviewed": len(judgments),
            "jev_judgments_correct": sum(judgments),
        },
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--runtime-results", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        cases, fixture_hash = read_json(args.cases)
        observations = read_json(args.observations)[0] if args.observations else None
        if args.runtime_results:
            runtime = read_json(args.runtime_results)[0]
            reviews = read_json(args.reviews)[0] if args.reviews else None
            report = build_runtime_report(cases, fixture_hash, runtime, reviews)
        else:
            report = build_report(cases, fixture_hash, observations)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Fixture/evaluation invalid: {exc}", file=sys.stderr)
        return 2
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
