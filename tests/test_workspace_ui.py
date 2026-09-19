"""Decision Workspace user-first UX contract tests."""

from pathlib import Path


STATIC_DIR = Path(__file__).parents[1] / "src" / "spendguard" / "static"


def test_workspace_has_one_question_flow_without_developer_controls() -> None:
    page = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert page.count('<textarea id="question"') == 1
    assert 'id="decision-form"' in page
    assert 'id="required-data-form"' in page
    assert 'id="decision-data"' not in page
    assert 'id="calculation-form"' not in page
    assert 'id="agent-result"' not in page
    assert "Direct Function" not in page
    assert "MCP" not in page
    assert "Phase" not in page
    assert "JSON" not in page
    assert 'id="inspector"' in page
    assert "Technical details" not in page
    assert 'role="alert"' in page
    assert "skip-link" in page


def test_workspace_builds_required_fields_and_runs_existing_decision_flow() -> None:
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert "missing_fields" in script
    assert "renderRequiredData" in script
    assert "required-data-fields" in script
    assert 'fetch("/api/decisions"' in script
    assert 'fetch("/api/research-needed"' in script
    assert 'fetch("/api/analyze"' not in script
    assert "/api/calculations/" not in script
    assert "calculate_usage_cost" in script
    assert "quote_items" in script
    assert "price or price_confirmation_needed" in script
    assert "Researching" in script
    assert "Calculating" not in script


def test_workspace_prioritizes_result_and_keeps_traceability_in_inspector() -> None:
    page = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="decision-result"' in page
    assert "CONCLUSION" in script
    assert "Key numbers" in script
    assert "Options" in script
    assert "Risks" in script
    assert "Next actions" in script
    assert "Facts" in script
    assert "Calculations" in script
    assert "Sources" in script
    assert "Assumptions" in script
    assert "Technical details" in script
    assert "source_url" in script
    assert "retrieved_at" in script
    assert "calculation.calculation.formula" in script


def test_workspace_responsive_and_reduced_motion_styles() -> None:
    stylesheet = (STATIC_DIR / "styles.css").read_text(encoding="utf-8")

    assert "@media (max-width: 1120px)" in stylesheet
    assert "@media (max-width: 760px)" in stylesheet
    assert "overflow-wrap: anywhere" in stylesheet
    assert "prefers-reduced-motion: no-preference" in stylesheet
    assert "backdrop-filter" not in stylesheet
    assert ".input-unit { position: absolute" in stylesheet
