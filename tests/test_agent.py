import pytest

from spendguard.agent import AgentConfigurationError, INSTRUCTIONS, build_agent, load_project_env
from spendguard.models import AnalysisResult


def test_agent_instructions_cover_phase_one_intents_and_exclusions() -> None:
    for intent in AnalysisResult.model_fields["intent"].annotation.__args__:
        assert intent in INSTRUCTIONS
    assert "does not calculate" in INSTRUCTIONS
    assert "search the web" in INSTRUCTIONS
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
