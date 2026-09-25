"""Minimum Jev inputs and judgment reuse with synthetic fixtures."""

import asyncio

import httpx

from spendguard import decision_state
from spendguard.decision_state import DecisionDelta, JUDGMENTS, extract_money_facts, persist_decision_result, update_state
from spendguard.codex_runtime import CodexResult
from spendguard import main as main_module


def test_minimum_judgment_payload_and_incremental_reuse(tmp_path, monkeypatch):
    transmitted = []

    def fake_judge(inputs):
        transmitted.append(inputs)
        return {name: {"value": 0.5 if JUDGMENTS[name][0] == "noul" else 2.0 if JUDGMENTS[name][0] == "score" else "wait", "confidence": 0.7}
                for name in inputs}

    monkeypatch.setattr(decision_state, "_judge", fake_judge)
    path = tmp_path / "decision.json"
    initial_delta = DecisionDelta(
        user_facts={
            "name": "Fixture Person", "question": "Do not send this original question.",
        },
        current_facts={"purchase_price": 229000},
        calculations={"alternative_price": 199000},
        sources={"seller": "https://example.com/private-search-result"},
        judgment_facts={
            "current_product_age_months": 36, "current_product_functional": True,
            "reported_problems": ["battery"], "requested_upgrade_features": ["noise_cancellation"],
            "available_cash": 430000, "upcoming_income": 130000,
            "purchase_price": 229000, "alternative_price": 199000,
        },
    )
    first = update_state(path, initial_delta)
    assert not path.exists()
    assert first["update"]["jev_calls"] == 1
    outbound = transmitted[0]
    assert set(outbound) == set(JUDGMENTS)
    assert outbound["cashflow_harmed"] == {
        "available_cash": 430000, "purchase_price": 229000, "upcoming_income": 130000,
    }
    assert "available_cash" not in outbound["replacement_needed"]
    assert "source" not in str(outbound).lower()
    assert "Fixture Person" not in str(outbound)
    assert "private-search-result" not in str(outbound)

    persist_decision_result(path, initial_delta, first)
    rent_delta = DecisionDelta(judgment_facts={"upcoming_fixed_expense": 600000})
    second = update_state(path, rent_delta)
    assert second["update"]["jev_calls"] == 1
    assert set(transmitted[1]) == {
        "cashflow_harmed", "purchase_burden_score", "purchase_choice", "key_factor",
    }
    assert set(second["update"]["reused_judgments"]) == set(JUDGMENTS) - set(transmitted[1])
    persist_decision_result(path, rent_delta, second)
    third = update_state(path, DecisionDelta())
    assert third["update"]["jev_calls"] == 0
    assert len(transmitted) == 2


def test_code_extracts_only_labeled_money_facts():
    assert extract_money_facts(
        "여행 예산이 50만원이고 다음 달 월세가 60만원이야. 쓸 수 있는 돈은 43만원, 수입은 13만원이야."
    ) == {
        "budget": 500000, "upcoming_fixed_expense": 600000,
        "available_cash": 430000, "upcoming_income": 130000,
    }
    assert extract_money_facts("비행기에서 ANC가 유용할까?") == {}


def test_unknown_retries_only_when_relevant_evidence_changes(tmp_path, monkeypatch):
    transmitted = []
    monkeypatch.setattr(decision_state, "_judge", lambda inputs: (
        transmitted.append(inputs) or {name: {"value": "unknown", "confidence": 0.0} for name in inputs}
    ))
    path = tmp_path / "sparse.json"
    initial_delta = DecisionDelta(judgment_facts={"current_product_functional": True})
    first = update_state(path, initial_delta)
    assert first["jev_results"]["cashflow_harmed"]["value"] == "unknown"
    persist_decision_result(path, initial_delta, first)
    update_state(path, DecisionDelta(assumptions={"unrelated_note": "fixture"}))
    assert len(transmitted) == 1
    update_state(path, DecisionDelta(judgment_facts={"available_cash": 100000, "purchase_price": 80000}))
    assert "cashflow_harmed" in transmitted[-1]


def test_fastapi_stores_readonly_jev_result_between_turns(tmp_path, monkeypatch):
    seen = []

    def fake_judge(inputs):
        seen.append(set(inputs))
        return {name: {"value": 0.5 if JUDGMENTS[name][0] == "noul" else 1.0 if JUDGMENTS[name][0] == "score" else "wait", "confidence": 0.5}
                for name in inputs}

    monkeypatch.setattr(decision_state, "_judge", fake_judge)

    class FixtureRunner:
        async def run(self, _question, **kwargs):
            first = kwargs["thread_id"] is None
            if not first:
                assert kwargs["precomputed_decision"] is not None
                return CodexResult(answer="fixture follow-up", latency_ms=1, thread_id="fixture-thread", resumed=True)
            delta = DecisionDelta(judgment_facts={
                "current_product_functional": True, "reported_problems": ["battery"],
                "purchase_price": 193030,
            })
            evaluated = update_state(kwargs["state_path"], delta)
            return CodexResult(
                answer="fixture answer", latency_ms=1, thread_id="fixture-thread", resumed=not first,
                decision_delta=delta.model_dump(mode="json"),
                mcp_calls=[{"tool": "update_decision_state", "status": "completed", "result": evaluated}],
            )

    async def call():
        async def wait_forever(_request):
            await asyncio.sleep(3600)

        monkeypatch.setattr(main_module, "wait_for_disconnect", wait_forever)
        main_module.app.state.codex_runner = FixtureRunner()
        main_module.app.state.decision_progress = {}
        main_module.app.state.decision_sessions = {}
        main_module.app.state.decision_state_dir = tmp_path
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main_module.app), base_url="http://test") as client:
            first = (await client.post("/api/decisions", json={"question": "fixture", "mode": "jev"})).json()
            second = (await client.post("/api/decisions", json={
                "question": "쓸 수 있는 돈은 43만원이고 다음 달 월세는 60만원이야.", "mode": "jev",
                "conversation_id": first["metadata"]["conversation_id"],
            })).json()
            unchanged = (await client.post("/api/decisions", json={
                "question": "쓸 수 있는 돈 43만원이면 어떻게 돼?", "mode": "jev",
                "conversation_id": first["metadata"]["conversation_id"],
            })).json()
        return first, second, unchanged

    first, second, unchanged = asyncio.run(call())
    assert first["metadata"]["jev_calls"] == 1
    assert second["metadata"]["resumed"] is True
    assert second["metadata"]["jev_calls"] == 1
    assert second["metadata"]["mcp_calls"] == []
    assert set(seen[1]) == {"cashflow_harmed", "purchase_burden_score", "purchase_choice", "key_factor"}
    assert unchanged["metadata"]["jev_calls"] == 0
    assert unchanged["metadata"]["mcp_calls"] == []
    assert len(seen) == 2
    assert list(tmp_path.glob("*.json"))
