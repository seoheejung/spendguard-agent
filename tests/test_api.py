from fastapi.testclient import TestClient

from spendguard.agent import AgentExecutionError, OpenAIAnalyzer
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
