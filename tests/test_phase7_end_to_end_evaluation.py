"""Phase 7 fixed end-to-end workflow evaluation."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from spendguard.agent import ResearchExecutionError
from spendguard.main import app
from spendguard.phase7_evaluation import evaluate_fixed_workflow, load_fixed_dataset


@pytest.mark.anyio
async def test_phase_seven_fixed_workflow_metrics_and_mcp_consistency() -> None:
    report = await evaluate_fixed_workflow(load_fixed_dataset())

    assert report["dataset_version"] == "phase7-v1"
    assert report["dataset_cases"] == 21
    assert report["api_error_cases"] == 1
    assert report["total_cases"] == 20
    assert report["routing_accuracy"] == 1
    assert report["calculation_accuracy"] == 1
    assert report["required_data_accuracy"] == 1
    assert report["source_coverage"] == 1
    assert report["unsupported_fact_count"] == 0
    assert report["tool_error_handling"] == 1
    assert report["end_to_end_success"] == 1
    assert report["calls"] == {"jev": 0, "openai": 0, "web_search": 0, "mcp": 10}
    assert {outcome["actual_pack"] for outcome in report["outcomes"]} >= {
        "purchase",
        "recurring_cost",
        "finance_cost",
        "ownership_cost",
        "quote_audit",
        "budget_optimization",
        None,
    }
    assert {outcome["id"] for outcome in report["outcomes"] if outcome["calculation_expected"]} == {
        "purchase-ready-001",
        "purchase-research-001",
        "purchase-usage-ready-001",
        "recurring-ready-001",
        "finance-installment-ready-001",
        "finance-refinance-ready-001",
        "ownership-ready-001",
        "quote-ready-001",
        "budget-ready-001",
    }


def test_phase_seven_keeps_ambiguous_001_expected_intent_unchanged() -> None:
    phase_one_cases = json.loads(
        (Path(__file__).parents[1] / "evals" / "phase1_cases.json").read_text(encoding="utf-8")
    )
    ambiguous = next(case for case in phase_one_cases if case["id"] == "ambiguous-001")
    phase_seven_case = next(
        case for case in load_fixed_dataset()["cases"] if case["id"] == "ambiguous-001"
    )

    assert ambiguous["expected_intent"] == "unknown"
    assert phase_seven_case["intent"] == "unknown"
    assert phase_seven_case["expected"]["pack"] is None


def test_phase_seven_web_search_failure_is_returned_by_decision_api() -> None:
    class FailingResearchAnalyzer:
        async def analyze(self, question: str):
            raise ResearchExecutionError("Current information research could not be completed.")

    case = next(
        item for item in load_fixed_dataset()["cases"] if item["id"] == "web-search-error-001"
    )
    with TestClient(app) as client:
        app.state.analyzer = FailingResearchAnalyzer()
        response = client.post(
            "/api/decisions",
            json={"question": case["question"], "data": case["data"]},
        )

    assert response.status_code == case["expected"]["http_status"]
    assert response.json()["detail"] == case["expected"]["detail"]


def test_phase_seven_workspace_contract_remains_available() -> None:
    static_dir = Path(__file__).parents[1] / "src" / "spendguard" / "static"
    page = (static_dir / "index.html").read_text(encoding="utf-8")
    script = (static_dir / "app.js").read_text(encoding="utf-8")

    for required in ("decision-form", "required-data-form", "decision-result", "inspector", "skip-link"):
        assert required in page
    for required in ("Researching", "renderDecisionResult", "renderRequiredData", "source_url", "retrieved_at"):
        assert required in script
