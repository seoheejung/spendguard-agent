"""Final monetary claims use deterministic amounts."""

import asyncio

import httpx

from spendguard import main as main_module
from spendguard.calculations import CostComparisonInput, compare_costs
from spendguard.codex_runtime import CodexResult
from spendguard.numeric_consistency import correct_numeric_answer


def test_corrects_difference_in_prose_and_table_without_changing_coupon_amounts():
    answer = (
        "공개가 75,700원, 예약가 73,429원, 차액 2,671원입니다.\n"
        "쿠폰가 68,130원과 예약가 73,429원의 차이 5,299원입니다.\n"
        "| 공개가 | 예약가 | 차액 |\n"
        "| --- | --- | --- |\n"
        "| 75,700원 | 73,429원 | 2,671원 |\n"
        "출처: [공개 상품 페이지](https://example.com/nagoya-tour)\n"
    )
    checked, count = correct_numeric_answer(answer, [])
    assert count == 2
    assert checked.count("2,271원") == 2
    assert "2,671원" not in checked
    assert "68,130원" in checked and "5,299원" in checked
    assert "[공개 상품 페이지](https://example.com/nagoya-tour)" in checked


def test_corrects_price_difference_using_labeled_prices_across_answer():
    answer = (
        "| 항목 | 가격과 조건 |\n"
        "| --- | --- |\n"
        "| 예약 내역 | 73,429원. 사용자 제공 정보 |\n"
        "| 공개가 | 75,700원, 10% 쿠폰 적용 시 68,130원부터 |\n\n"
        "예약 가격이 5,299원 높고, 쿠폰을 쓰지 않는 기본 표시가와 비교하면 예약가가 2,671원 낮습니다."
    )
    checked, count = correct_numeric_answer(answer, [])
    assert count == 1
    assert "예약가가 2,271원 낮습니다" in checked
    assert "5,299원 높고" in checked


def test_uses_mcp_total_and_annual_amount_without_touching_source_prices():
    calls = [
        {"tool": "sum_costs", "status": "completed", "result": {"result": {"total_cost": "250.00"}}},
        {"tool": "annualize_expense", "status": "completed", "result": {"result": {"annual_amount": "1200.00"}}},
    ]
    answer = "월 비용 100원, 연간 1,300원입니다. 두 항목의 합계는 300원입니다."
    checked, count = correct_numeric_answer(answer, calls)
    assert count == 2
    assert "월 비용 100원" in checked
    assert "연간 1,200원" in checked
    assert "합계는 250원" in checked


def test_keeps_unrelated_prices_when_relation_is_not_identified():
    answer = "후보는 75,700원, 73,429원, 68,130원입니다. 배송비는 2,671원입니다."
    assert correct_numeric_answer(answer, []) == (answer, 0)


def test_does_not_replace_an_unrelated_amount_with_the_same_digits():
    answer = "공개가 75,700원, 예약가 73,429원, 차액 2,671원입니다. 배송비 2,671원은 별도입니다."
    checked, count = correct_numeric_answer(answer, [])
    assert count == 1
    assert "차액 2,271원" in checked
    assert "배송비 2,671원" in checked


def test_api_corrects_final_difference_after_verifying_mcp(monkeypatch):
    data = {"currency": "KRW", "options": [
        {"name": "공개가", "total_cost": 120500},
        {"name": "예약가", "total_cost": 113201},
    ]}
    calculation = compare_costs(CostComparisonInput.model_validate(data)).model_dump(mode="json")

    class Runner:
        async def run(self, *_args, **_kwargs):
            return CodexResult(
                answer="공개가 120,500원, 예약가 113,201원, 차액 7,699원입니다.",
                latency_ms=1, thread_id="numeric-fixture",
                mcp_calls=[{"tool": "compare_costs", "status": "completed",
                            "arguments": {"data": data}, "result": calculation}],
            )

    async def call():
        async def wait_forever(_request):
            await asyncio.sleep(3600)

        monkeypatch.setattr(main_module, "wait_for_disconnect", wait_forever)
        main_module.app.state.codex_runner = Runner()
        main_module.app.state.decision_sessions = {}
        main_module.app.state.decision_progress = {}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=main_module.app), base_url="http://test") as client:
            return await client.post("/api/decisions", json={"question": "공개가와 예약가를 비교해줘"})

    response = asyncio.run(call())
    assert response.status_code == 200
    assert "7,299원" in response.json()["answer"]
    assert "7,699원" not in response.json()["answer"]
    assert response.json()["metadata"]["numeric_corrections"] == 1
