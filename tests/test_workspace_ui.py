"""Phase 4.5 Decision Workspace UI contract tests."""

from pathlib import Path


STATIC_DIR = Path(__file__).parents[1] / "src" / "spendguard" / "static"


def test_workspace_uses_phase_five_research_state_and_sources() -> None:
    page = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "Researching" in script
    assert "Needs Input" in page
    assert "Calculating" in script
    assert "Review" in script
    assert "Ready" in script
    assert 'href="#sources"' in page
    assert 'id="sources"' in page
    assert "Decision Pack" not in page
    assert 'role="alert"' in page
    assert "skip-link" in page


def test_workspace_renders_agent_and_calculation_api_outputs() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'fetch("/api/analyze"' in script
    assert 'fetch(`/api/calculations/${execution}`' in script
    assert "known_facts" in script
    assert "missing_fields" in script
    assert "calculation.intermediate" in script
    assert "calculation.result" in script
    assert "toolDefinitions" in script
    assert 'fetch("/api/research-needed"' in script
    assert "renderSources" in script
    assert "external_facts" in script
    assert "source_url" in script
    assert "retrieved_at" in script


def test_workspace_responsive_and_reduced_motion_styles() -> None:
    stylesheet = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

    assert "@media (max-width: 760px)" in stylesheet
    assert "overflow-wrap: anywhere" in stylesheet
    assert "prefers-reduced-motion: no-preference" in stylesheet
    assert "backdrop-filter" not in stylesheet
    assert "position: absolute" not in stylesheet
