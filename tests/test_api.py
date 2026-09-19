from fastapi.testclient import TestClient

from spendguard.agent import AgentExecutionError, OpenAIAnalyzer, ResearchExecutionError
from spendguard.main import app
from spendguard.models import AnalysisResult


class StubAnalyzer:
    async def analyze(self, question: str) -> AnalysisResult:
        assert question == "월 8만원 통신비를 줄이고 싶어요."
        return AnalysisResult(
            intent="recurring_cost",
            summary="통신비 절감 질문입니다.",
            known_facts=["월 통신비: 8만원"],
            missing_fields=["현재 요금제 구성"],
            assumptions=[],
        )


class FailingAnalyzer:
    async def analyze(self, question: str) -> AnalysisResult:
        raise AgentExecutionError("The agent could not analyze this question.")


class FailingResearchAnalyzer:
    async def analyze(self, question: str) -> AnalysisResult:
        raise ResearchExecutionError("Current information research could not be completed.")


def test_analyze_returns_structured_output() -> None:
    with TestClient(app) as client:
        app.state.analyzer = StubAnalyzer()
        response = client.post("/api/analyze", json={"question": "월 8만원 통신비를 줄이고 싶어요."})

    assert response.status_code == 200
    assert response.json()["intent"] == "recurring_cost"
    assert response.json()["missing_fields"] == ["현재 요금제 구성"]


def test_analyze_rejects_empty_question() -> None:
    with TestClient(app) as client:
        response = client.post("/api/analyze", json={"question": ""})

    assert response.status_code == 422


def test_analyze_returns_agent_error() -> None:
    with TestClient(app) as client:
        app.state.analyzer = FailingAnalyzer()
        response = client.post("/api/analyze", json={"question": "질문"})

    assert response.status_code == 502


def test_analyze_returns_research_tool_error() -> None:
    with TestClient(app) as client:
        app.state.analyzer = FailingResearchAnalyzer()
        response = client.post("/api/analyze", json={"question": "현재 가격"})

    assert response.status_code == 502
    assert response.json()["detail"] == "Current information research could not be completed."


def test_research_needed_keeps_calculations_and_user_values_offline() -> None:
    with TestClient(app) as client:
        current_price = client.post("/api/research-needed", json={"question": "현재 아이폰 가격"})
        calculation = client.post(
            "/api/research-needed", json={"question": "100만원을 24개월 할부로 계산해줘"}
        )

    assert current_price.json() == {"needed": True}
    assert calculation.json() == {"needed": False}


def test_decision_pack_endpoint_reuses_mcp_calculation() -> None:
    with TestClient(app) as client:
        app.state.analyzer = StubAnalyzer()
        response = client.post(
            "/api/decisions",
            json={
                "question": "월 8만원 통신비를 줄이고 싶어요.",
                "data": {"item": "mobile plan", "current_cost": "80", "period_months": "1"},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["pack"] == "recurring_cost"
    assert body["status"] == "ready"
    assert body["calculations"][0]["execution"] == "mcp"
    assert body["calculations"][0]["tool"] == "annualize_expense"


def test_analyze_returns_configuration_error_without_openai_settings(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr("spendguard.agent.load_project_env", lambda: None)
    with TestClient(app) as client:
        app.state.analyzer = OpenAIAnalyzer()
        response = client.post("/api/analyze", json={"question": "질문"})

    assert response.status_code == 503
    assert response.json()["detail"] == "OPENAI_MODEL is required."


def test_direct_calculation_returns_phase_three_result() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/calculations/direct",
            json={
                "tool": "calculate_usage_cost",
                "data": {"total_cost": "10", "units": "3", "currency": "USD"},
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "tool": "calculate_usage_cost",
        "execution": "direct",
        "calculation": {
            "inputs": {"total_cost": "10", "units": "3", "currency": "USD"},
            "formula": "cost_per_unit = total_cost / units",
            "intermediate": {"units": "3"},
            "result": {"cost_per_unit": "3.33", "currency": "USD"},
        },
    }


def test_mcp_calculation_returns_phase_four_result() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/calculations/mcp",
            json={
                "tool": "calculate_usage_cost",
                "data": {"total_cost": "10", "units": "3", "currency": "USD"},
            },
        )

    assert response.status_code == 200
    assert response.json()["execution"] == "mcp"
    assert response.json()["calculation"]["result"] == {"cost_per_unit": "3.33", "currency": "USD"}


def test_calculation_returns_validation_error() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/calculations/direct",
            json={
                "tool": "calculate_usage_cost",
                "data": {"total_cost": "10", "units": "0", "currency": "USD"},
            },
        )

    assert response.status_code == 422
