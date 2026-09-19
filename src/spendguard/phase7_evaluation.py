"""Phase 7 deterministic end-to-end evaluation harness."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from spendguard.decision_packs import build_decision_pack
from spendguard.main import CALCULATION_TOOLS
from spendguard.mcp_client import call_calculation_tool
from spendguard.models import AnalysisResult, ExternalFact, ResearchResult


DATASET_PATH = Path(__file__).resolve().parents[2] / "evals" / "phase7_end_to_end_v1.json"
McpCaller = Callable[[str, dict[str, Any]], Awaitable[dict[str, Any]]]


def load_fixed_dataset(path: Path = DATASET_PATH) -> dict[str, Any]:
    """Load the frozen Phase 7 workflow cases without editing prior eval data."""

    return json.loads(path.read_text(encoding="utf-8"))


def _analysis_for(case: dict[str, Any]) -> AnalysisResult:
    research_kind = case.get("research")
    if research_kind is None:
        research = ResearchResult.not_needed()
        sources: list[ExternalFact] = []
    elif research_kind == "completed":
        research = ResearchResult(
            needed=True,
            status="completed",
            queries=["fixture current official price query"],
            official_source_confirmed=True,
            note="A source trace is present in this deterministic fixture.",
        )
        sources = [
            ExternalFact(
                value="Fixture source-trace value",
                source_name="Apple",
                source_url="https://www.apple.com/kr/iphone/",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            )
        ]
    else:
        research = ResearchResult(
            needed=True,
            status="no_results",
            note="The fixed evaluation simulates a no-results research response.",
        )
        sources = []
    return AnalysisResult(
        intent=case["intent"],
        summary="Fixed evaluation agent explanation.",
        known_facts=["Fixed user-provided input."],
        missing_fields=[],
        assumptions=["No unstated preference was assumed."],
        research=research,
        external_facts=sources,
    )


async def evaluate_fixed_workflow(
    dataset: dict[str, Any],
    *,
    mcp_caller: McpCaller = call_calculation_tool,
    clock: Callable[[], float] = time.perf_counter,
) -> dict[str, Any]:
    """Run the frozen Decision Pack cases through the existing MCP boundary."""

    outcomes: list[dict[str, Any]] = []
    mcp_calls = 0
    started_at = clock()

    async def counted_mcp(tool: str, data: dict[str, Any]) -> dict[str, Any]:
        nonlocal mcp_calls
        mcp_calls += 1
        return await mcp_caller(tool, data)

    async def failing_mcp(tool: str, data: dict[str, Any]) -> dict[str, Any]:
        nonlocal mcp_calls
        mcp_calls += 1
        raise RuntimeError("fixed MCP failure")

    workflow_cases = [case for case in dataset["cases"] if not case.get("api_error")]
    for case in workflow_cases:
        case_started_at = clock()
        expected = case["expected"]
        result = await build_decision_pack(
            _analysis_for(case),
            case["data"],
            mcp_caller=failing_mcp if case.get("mcp_error") else counted_mcp,
        )
        expected_calculation = expected.get("calculation")
        calculation_match = True
        direct_mcp_match = True
        if expected_calculation:
            calculation_match = (
                len(result.calculations) == 1
                and result.calculations[0].tool == expected_calculation["tool"]
                and result.calculations[0].calculation.model_dump(mode="json")["result"]
                == expected_calculation["result"]
            )
            if result.calculations:
                tool = result.calculations[0].tool
                model_type, calculator = CALCULATION_TOOLS[tool]
                mcp_calculation = result.calculations[0].calculation.model_dump(mode="json")
                direct_mcp_match = (
                    calculator(model_type.model_validate(mcp_calculation["inputs"])).model_dump(mode="json")
                    == mcp_calculation
                )
        source_required = bool(expected.get("source_required"))
        source_trace_match = not source_required or (
            bool(result.sources)
            and all(
                fact.value
                and fact.source_name
                and fact.source_url
                and fact.retrieved_at
                and fact.value not in result.facts
                for fact in result.sources
            )
        )
        matches = (
            result.pack == expected["pack"]
            and result.status == expected["status"]
            and result.missing_fields == expected["missing_fields"]
            and calculation_match
            and direct_mcp_match
            and source_trace_match
        )
        outcomes.append(
            {
                "id": case["id"],
                "expected_pack": expected["pack"],
                "actual_pack": result.pack,
                "expected_status": expected["status"],
                "actual_status": result.status,
                "routing_correct": result.pack == expected["pack"],
                "required_data_correct": result.missing_fields == expected["missing_fields"],
                "calculation_correct": calculation_match and direct_mcp_match,
                "calculation_expected": bool(expected_calculation),
                "source_trace_correct": source_trace_match,
                "source_required": source_required,
                "tool_error_handled": (not case.get("mcp_error")) or result.status == "tool_error",
                "unsupported_fact_count": sum(
                    not (fact.value and fact.source_name and fact.source_url and fact.retrieved_at)
                    for fact in result.sources
                ),
                "latency_ms": (clock() - case_started_at) * 1_000,
                "success": matches,
            }
        )

    total = len(outcomes)
    calculated = [outcome for outcome in outcomes if outcome["calculation_expected"]]
    sourced = [outcome for outcome in outcomes if outcome["source_required"]]
    tool_errors = [outcome for outcome in outcomes if outcome["expected_status"] == "tool_error"]
    return {
        "dataset_version": dataset["dataset_version"],
        "dataset_cases": len(dataset["cases"]),
        "api_error_cases": len(dataset["cases"]) - len(workflow_cases),
        "total_cases": total,
        "outcomes": outcomes,
        "routing_accuracy": sum(outcome["routing_correct"] for outcome in outcomes) / total,
        "calculation_accuracy": sum(outcome["calculation_correct"] for outcome in calculated) / len(calculated),
        "required_data_accuracy": sum(outcome["required_data_correct"] for outcome in outcomes) / total,
        "source_coverage": sum(outcome["source_trace_correct"] for outcome in sourced) / len(sourced),
        "unsupported_fact_count": sum(outcome["unsupported_fact_count"] for outcome in outcomes),
        "tool_error_handling": sum(outcome["tool_error_handled"] for outcome in tool_errors) / len(tool_errors),
        "end_to_end_success": sum(outcome["success"] for outcome in outcomes) / total,
        "latency": {
            "total_ms": (clock() - started_at) * 1_000,
            "per_case_ms": {outcome["id"]: outcome["latency_ms"] for outcome in outcomes},
        },
        "calls": {"jev": 0, "openai": 0, "web_search": 0, "mcp": mcp_calls},
        "usage": {"status": "not available: deterministic local evaluation uses no model provider"},
        "cost": {"status": "not available: deterministic local evaluation uses no billable provider"},
    }
