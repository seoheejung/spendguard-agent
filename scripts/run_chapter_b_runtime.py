"""Run the frozen 15 questions through the live /api/decisions route."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from spendguard.main import app


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "evals" / "chapter_b_sparse_v1.json"
JEV_ITEMS = {
    "subscription-audit-001": ("subscription_audit", "디즈니플러스 구독"),
    "quote-audit-001": ("quote_audit", "배관 1m당 3만원"),
    "annual-leaks-001": ("annual_leaks", "월 20만원 배달앱 지출"),
    "purchase-review-001": ("purchase_review", "다른 일본 도시 항공권 대안"),
}


def source_digest() -> str:
    paths = [ROOT / "AGENTS.md", ROOT / "pyproject.toml", ROOT / ".env.example", ROOT / ".project" / "plan.md"]
    paths.extend(sorted((ROOT / "src").rglob("*")))
    paths.extend([ROOT / ".git" / "HEAD", ROOT / ".git" / "index"])
    digest = hashlib.sha256()
    for path in paths:
        if path.is_file() and "__pycache__" not in path.parts:
            digest.update(str(path.relative_to(ROOT)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("baseline", "jev"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case", action="append", default=[])
    args = parser.parse_args()
    raw = FIXTURE.read_bytes()
    cases = json.loads(raw)["cases"]
    if args.case:
        cases = [case for case in cases if case["id"] in args.case]
    output = args.output if args.output.is_absolute() else ROOT / args.output
    artifact = {
        "dataset_version": "chapter-b-sparse-v1",
        "fixture_sha256": hashlib.sha256(raw).hexdigest(),
        "mode": args.mode,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "runs": [],
    }
    if output.exists():
        existing = json.loads(output.read_text(encoding="utf-8"))
        if existing.get("fixture_sha256") != artifact["fixture_sha256"] or existing.get("mode") != args.mode:
            raise ValueError("Existing output belongs to a different fixture or mode.")
        artifact = existing
    completed = {run["case_id"] for run in artifact["runs"]}
    before = source_digest()
    with TestClient(app) as client:
        for case in cases:
            if case["id"] in completed:
                continue
            payload = {"question": case["question"], "mode": args.mode}
            if args.mode == "jev" and case["id"] in JEV_ITEMS:
                payload["jev_candidate"], payload["candidate_text"] = JEV_ITEMS[case["id"]]
            started = time.perf_counter()
            try:
                response = client.post("/api/decisions", json=payload)
                body = response.json()
                status_code = response.status_code
            except Exception as error:
                status_code = 0
                body = {"detail": type(error).__name__}
            row = {
                "case_id": case["id"],
                "http_status": status_code,
                "status": body.get("status", "error") if status_code == 200 else "error",
                "answer": body.get("answer", ""),
                "metadata": body.get("metadata", {}),
                "trace": list(app.state.codex_runner.last_trace),
                "error": body.get("detail") if status_code != 200 else None,
                "exit_diagnostic": app.state.codex_runner.last_failure if status_code != 200 else None,
                "e2e_latency_ms": round((time.perf_counter() - started) * 1000),
                "attempts": 1,
            }
            artifact["runs"].append(row)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"case_id": row["case_id"], "status": row["status"], "latency_ms": row["e2e_latency_ms"], "search": row["metadata"].get("search_calls"), "mcp": len(row["metadata"].get("mcp_calls", [])), "jev": row["metadata"].get("jev_calls")}, ensure_ascii=True), flush=True)
    artifact["finished_at"] = datetime.now(timezone.utc).isoformat()
    artifact["repository_unchanged"] = source_digest() == before
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    print("repository_unchanged", artifact["repository_unchanged"], flush=True)


if __name__ == "__main__":
    main()
