"""Phase 6 decision-pack workflow and coverage tests."""

import json
from pathlib import Path

import pytest

from spendguard.decision_packs import REQUIRED_FIELDS, build_decision_pack, pack_for_analysis
from spendguard.models import AnalysisResult, ExternalFact, ResearchResult


def analysis(intent: str, *, researched: bool = False) -> AnalysisResult:
    research = ResearchResult.not_needed()
    sources: list[ExternalFact] = []
    if researched:
        research = ResearchResult(
            needed=True,
            status="completed",
            official_source_confirmed=True,
            note="Current facts were verified.",
        )
        sources = [
            ExternalFact(
                value="Current listed price",
                source_name="Official source",
                source_url="https://example.com/official",
                retrieved_at="2026-09-19T00:00:00+00:00",
            )
        ]
    return AnalysisResult(
        intent=intent,
        summary="Agent explanation is separate from facts and calculations.",
        known_facts=["User-provided fact"],
        missing_fields=[],
        assumptions=["No unstated preference was assumed."],
        research=research,
        external_facts=sources,
    )


async def fake_mcp(tool: str, data: dict[str, object]) -> dict[str, object]:
    return {
        "inputs": data,
        "formula": f"existing {tool}",
        "intermediate": {},
        "result": {"currency": str(data.get("currency", "KRW"))},
    }


SCENARIOS = [
    ("lowest_price", "purchase", {"target": "phone", "purpose": "work", "price": "100", "options": [{"name": "A", "total_cost": "100"}, {"name": "B", "total_cost": "120"}]}),
    ("subscription_diet", "recurring_cost", {"item": "streaming", "current_cost": "10", "period_months": "1", "options": [{"name": "A", "total_cost": "10"}, {"name": "B", "total_cost": "8"}]}),
    ("telecom_review", "recurring_cost", {"item": "mobile plan", "current_cost": "80", "period_months": "1"}),
    ("insurance_overlap", "recurring_cost", {"item": "insurance", "current_cost": "30", "period_months": "1", "options": [{"name": "A", "total_cost": "30"}, {"name": "B", "total_cost": "25"}]}),
    ("card_benefits", "budget_optimization", {"budget": "500", "options": [{"name": "A", "total_cost": "490"}, {"name": "B", "total_cost": "510"}]}),
    ("impulse_purchase", "purchase", {"target": "headphones", "purpose": "music", "price_confirmation_needed": True, "total_cost": "120", "units": "12"}),
    ("grocery_budget", "budget_optimization", {"budget": "200", "options": [{"name": "A", "total_cost": "180"}, {"name": "B", "total_cost": "210"}]}),
    ("travel_budget", "budget_optimization", {"budget": "1000", "options": [{"name": "A", "total_cost": "950"}, {"name": "B", "total_cost": "1100"}]}),
    ("vehicle_ownership", "ownership_cost", {"target": "car", "ownership_months": 36, "purchase_cost": "20000", "monthly_ownership_cost": "300", "additional_cost": "500"}),
    ("installment_vs_cash", "finance_cost", {"amount": "1000", "term_months": 12, "rate_or_comparison": "installment", "principal": "1000", "annual_interest_rate_pct": "5"}),
    ("refinance", "finance_cost", {"amount": "1000", "term_months": 12, "rate_or_comparison": "refinance", "remaining_principal": "1000", "current_annual_interest_rate_pct": "5", "current_remaining_months": 12, "new_annual_interest_rate_pct": "3", "new_term_months": 12, "refinancing_fee": "10"}),
    ("quote_overcharge", "quote_audit", {"quote_items": [{"name": "repair"}], "options": [{"name": "quote", "total_cost": "120"}, {"name": "market", "total_cost": "100"}]}),
    ("price_negotiation", "quote_audit", {"quote_items": [{"name": "work"}], "options": [{"name": "quote", "total_cost": "120"}, {"name": "market", "total_cost": "100"}]}),
    ("annual_leak", "budget_optimization", {"expenses": [{"name": "subscription"}], "amount": "20", "period_months": "1"}),
    ("purchase_review", "purchase", {"target": "laptop", "purpose": "study", "price": "1000", "options": [{"name": "new", "total_cost": "1000"}, {"name": "used", "total_cost": "700"}]}),
]


@pytest.mark.anyio
@pytest.mark.parametrize(("scenario", "intent", "data"), SCENARIOS)
async def test_initial_saving_scenarios_use_their_intent_routed_pack(
    scenario: str, intent: str, data: dict[str, object]
) -> None:
    result = await build_decision_pack(analysis(intent, researched=scenario in {"lowest_price", "telecom_review", "travel_budget", "quote_overcharge", "price_negotiation"}), data, mcp_caller=fake_mcp)

    assert result.pack == intent
    assert result.status == "ready"
    assert result.missing_fields == []
    assert result.facts == ["User-provided fact"]
    assert result.assumptions == ["No unstated preference was assumed."]
    if scenario in {"lowest_price", "telecom_review", "travel_budget", "quote_overcharge", "price_negotiation"}:
        assert result.sources[0].source_url == "https://example.com/official"


@pytest.mark.anyio
@pytest.mark.parametrize("intent", list(REQUIRED_FIELDS))
async def test_each_pack_returns_code_owned_missing_required_fields(intent: str) -> None:
    result = await build_decision_pack(analysis(intent), {}, mcp_caller=fake_mcp)

    assert result.pack == intent
    assert result.status == "needs_input"
    assert result.missing_fields
    assert result.calculations == []


@pytest.mark.anyio
async def test_unknown_and_ambiguous_input_never_routes_from_jev_confidence() -> None:
    cases = json.loads((Path(__file__).parents[1] / "evals" / "phase1_cases.json").read_text(encoding="utf-8"))
    ambiguous_case = next(case for case in cases if case["id"] == "ambiguous-001")
    result = await build_decision_pack(analysis("unknown"), {}, mcp_caller=fake_mcp)

    assert ambiguous_case == {"id": "ambiguous-001", "input": "돈을 아끼고 싶어요.", "expected_intent": "unknown"}
    assert pack_for_analysis(analysis("unknown")) is None
    assert result.pack is None
    assert result.status == "needs_input"
    assert "ambiguous" in result.risks[0].lower()


@pytest.mark.anyio
async def test_tool_error_does_not_create_a_confirmed_decision() -> None:
    async def failing_mcp(tool: str, data: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("stdio failure")

    result = await build_decision_pack(
        analysis("finance_cost"),
        {"amount": "1000", "term_months": 12, "rate_or_comparison": "installment", "principal": "1000", "annual_interest_rate_pct": "5"},
        mcp_caller=failing_mcp,
    )

    assert result.status == "tool_error"
    assert result.calculations == []
    assert "no decision was confirmed" in result.conclusion


@pytest.mark.anyio
async def test_mcp_only_receives_existing_calculation_tool_names() -> None:
    calls: list[str] = []

    async def recording_mcp(tool: str, data: dict[str, object]) -> dict[str, object]:
        calls.append(tool)
        return await fake_mcp(tool, data)

    await build_decision_pack(
        analysis("ownership_cost"),
        {"target": "car", "ownership_months": 12, "purchase_cost": "100", "monthly_ownership_cost": "10", "additional_cost": "0"},
        mcp_caller=recording_mcp,
    )

    assert calls == ["calculate_tco"]


TOOL_ERROR_CASES = [
    ("purchase", SCENARIOS[0][2]),
    ("recurring_cost", SCENARIOS[1][2]),
    ("finance_cost", SCENARIOS[9][2]),
    ("ownership_cost", SCENARIOS[8][2]),
    ("quote_audit", SCENARIOS[11][2]),
    ("budget_optimization", SCENARIOS[4][2]),
]


@pytest.mark.anyio
@pytest.mark.parametrize(("intent", "data"), TOOL_ERROR_CASES)
async def test_each_pack_handles_a_calculation_tool_error(intent: str, data: dict[str, object]) -> None:
    async def failing_mcp(tool: str, calculation_data: dict[str, object]) -> dict[str, object]:
        raise RuntimeError("stdio failure")

    result = await build_decision_pack(analysis(intent), data, mcp_caller=failing_mcp)

    assert result.pack == intent
    assert result.status == "tool_error"
    assert result.sources == []


@pytest.mark.anyio
@pytest.mark.parametrize(("intent", "data"), TOOL_ERROR_CASES)
async def test_each_pack_keeps_phase_five_sources_separate(intent: str, data: dict[str, object]) -> None:
    result = await build_decision_pack(analysis(intent, researched=True), data, mcp_caller=fake_mcp)

    assert result.status == "ready"
    assert result.sources[0].source_name == "Official source"
    assert result.sources[0].source_url == "https://example.com/official"
    assert "Current listed price" not in result.facts
