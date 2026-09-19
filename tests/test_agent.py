from types import SimpleNamespace

import pytest

from spendguard.agent import (
    AgentConfigurationError,
    INSTRUCTIONS,
    OpenAIAnalyzer,
    ResearchExecutionError,
    build_agent,
    load_project_env,
    needs_current_information,
)
from spendguard.models import AnalysisResult


def test_agent_instructions_cover_intents_and_research_boundaries() -> None:
    for intent in AnalysisResult.model_fields["intent"].annotation.__args__:
        assert intent in INSTRUCTIONS
    assert "Do not calculate" in INSTRUCTIONS
    assert "WebSearchTool" in INSTRUCTIONS
    assert "MCP" in INSTRUCTIONS


def test_load_project_env_sets_only_unset_values(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text('OPENAI_API_KEY=from-file\nOPENAI_MODEL="from-file-model"\n', encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "from-environment")

    load_project_env(env_file)

    assert __import__("os").environ["OPENAI_API_KEY"] == "from-file"
    assert __import__("os").environ["OPENAI_MODEL"] == "from-environment"


def test_build_agent_requires_explicit_openai_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.setattr("spendguard.agent.load_project_env", lambda: None)

    with pytest.raises(AgentConfigurationError, match="OPENAI_MODEL"):
        build_agent()


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("아이폰 17의 현재 판매 가격을 알려줘", True),
        ("What is the latest Netflix subscription price?", True),
        ("월 8만원 통신비를 12개월로 계산해줘", False),
        ("100만원을 24개월 할부하면 이자가 얼마야?", False),
        ("내 예산은 200만원이야", False),
    ],
)
def test_needs_current_information_only_for_mutable_external_facts(question: str, expected: bool) -> None:
    assert needs_current_information(question) is expected


def test_research_agent_uses_hosted_web_search_only_when_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr("spendguard.agent.load_project_env", lambda: None)

    research_agent = build_agent(research_enabled=True)
    intake_agent = build_agent(research_enabled=False)

    assert research_agent.tools[0].name == "web_search"
    assert research_agent.model_settings.tool_choice == "required"
    assert research_agent.model_settings.response_include == ["web_search_call.action.sources"]
    assert intake_agent.tools == []


def _research_result(
    *, sources: bool = True, conflicting: bool = False, freshness_confirmed: bool = True
) -> SimpleNamespace:
    source_url = "https://www.apple.com/kr/iphone/"
    search = SimpleNamespace(
        type="web_search_call",
        action=SimpleNamespace(
            type="search",
            queries=["Apple iPhone Korea current price"],
            query=None,
            sources=[SimpleNamespace(url=source_url)] if sources else [],
        ),
    )
    annotations = [SimpleNamespace(type="url_citation", url=source_url, title="Apple iPhone")] if sources else []
    message = SimpleNamespace(type="message", content=[SimpleNamespace(annotations=annotations)])
    return SimpleNamespace(
        final_output={
            "intent": "purchase",
            "summary": "외부 확인 사실은 출처 영역에 분리했습니다.",
            "known_facts": [],
            "missing_fields": [],
            "assumptions": [],
            "external_facts": [
                {"value": "Current listed price", "source_url": source_url},
                {"value": "Unsupported value", "source_url": "https://example.invalid/value"},
            ],
            "official_source_urls": [source_url] if sources else [],
            "conflicting_sources": conflicting,
            "freshness_confirmed": freshness_confirmed,
        },
        raw_responses=[SimpleNamespace(output=[search, message])],
    )


@pytest.mark.anyio
async def test_research_normalizes_only_actual_cited_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_build_agent(*, research_enabled: bool):
        captured["research_enabled"] = research_enabled
        return object()

    async def fake_run(*args):
        return _research_result()

    monkeypatch.setattr("spendguard.agent.build_agent", fake_build_agent)
    monkeypatch.setattr("spendguard.agent.Runner.run", fake_run)

    result = await OpenAIAnalyzer().analyze("아이폰 17의 현재 가격을 알려줘")

    assert captured["research_enabled"] is True
    assert result.research.status == "completed"
    assert result.research.official_source_confirmed is True
    assert result.research.queries == ["Apple iPhone Korea current price"]
    assert len(result.external_facts) == 1
    assert result.external_facts[0].source_name == "Apple iPhone"
    assert result.external_facts[0].source_url == "https://www.apple.com/kr/iphone/"
    assert result.external_facts[0].retrieved_at.endswith("+00:00")


@pytest.mark.anyio
async def test_research_handles_no_results_and_tool_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("spendguard.agent.build_agent", lambda **kwargs: object())

    async def no_results(*args):
        return _research_result(sources=False)

    monkeypatch.setattr("spendguard.agent.Runner.run", no_results)
    result = await OpenAIAnalyzer().analyze("현재 아이폰 가격을 알려줘")
    assert result.research.status == "no_results"
    assert result.external_facts == []

    async def fails(*args):
        raise RuntimeError("web search failed")

    monkeypatch.setattr("spendguard.agent.Runner.run", fails)
    with pytest.raises(ResearchExecutionError):
        await OpenAIAnalyzer().analyze("현재 아이폰 가격을 알려줘")


@pytest.mark.anyio
async def test_research_marks_unconfirmed_official_and_conflicting_sources(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("spendguard.agent.build_agent", lambda **kwargs: object())

    raw_result = _research_result()
    raw_result.final_output["official_source_urls"] = []

    async def fake_run(*args):
        return raw_result

    monkeypatch.setattr("spendguard.agent.Runner.run", fake_run)
    result = await OpenAIAnalyzer().analyze("현재 아이폰 가격을 알려줘")
    assert result.research.status == "official_source_unconfirmed"
    assert result.research.official_source_confirmed is False

    raw_result.final_output["conflicting_sources"] = True
    result = await OpenAIAnalyzer().analyze("현재 아이폰 가격을 알려줘")
    assert result.research.status == "conflicting"
    assert result.research.official_source_confirmed is False
    assert result.external_facts == []


@pytest.mark.anyio
async def test_research_does_not_confirm_a_value_when_freshness_is_unverifiable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("spendguard.agent.build_agent", lambda **kwargs: object())

    async def fake_run(*args):
        return _research_result(freshness_confirmed=False)

    monkeypatch.setattr("spendguard.agent.Runner.run", fake_run)
    result = await OpenAIAnalyzer().analyze("현재 아이폰 가격을 알려줘")

    assert result.research.status == "freshness_unverifiable"
    assert result.external_facts == []
