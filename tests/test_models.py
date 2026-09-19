import pytest
from pydantic import ValidationError

from spendguard.models import AnalysisResult


def test_analysis_result_accepts_required_structured_output() -> None:
    result = AnalysisResult(
        intent="purchase",
        summary="노트북 구매 질문입니다.",
        known_facts=["예산: 189만원"],
        missing_fields=["사용 목적"],
        assumptions=[],
    )

    assert result.intent == "purchase"


def test_analysis_result_rejects_invalid_intent() -> None:
    with pytest.raises(ValidationError):
        AnalysisResult(intent="calculation", summary="잘못된 intent")
