import json
from pathlib import Path

from spendguard.models import AnalysisResult


def test_fixed_evaluation_cases_cover_phase_one_requirements() -> None:
    cases = json.loads(Path("evals/phase1_cases.json").read_text(encoding="utf-8"))
    intents = {case["expected_intent"] for case in cases}

    assert len(cases) == 17
    assert intents == set(AnalysisResult.model_fields["intent"].annotation.__args__)
    assert any(case["id"].startswith("ambiguous") for case in cases)
    assert any(case["id"].startswith("complete") for case in cases)
    assert any(case["id"].startswith("missing") for case in cases)
    assert any(case["id"].startswith("out-of-scope") for case in cases)
