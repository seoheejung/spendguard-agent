import json
from pathlib import Path
from types import SimpleNamespace

from spendguard.decision_prototype import JUDGMENT_DEFINITIONS, append_sanitized_log, fixture_sha256, judge


class StubClient:
    def __init__(self, response):
        self.response = response
        self.questions = []

    def system_one(self, *, state, questions):
        self.questions.append(questions)
        return self.response


def response(answer):
    return SimpleNamespace(answers={"judgment":answer},usage=SimpleNamespace(input_tokens=10,output_tokens=2))


def test_four_judgments_are_independent_and_have_abstain_or_review_paths():
    assert set(JUDGMENT_DEFINITIONS) == {
        "additional_information","current_information_search","search_result_relevance","decision_result_review"
    }
    assert {item["automation_level"] for item in JUDGMENT_DEFINITIONS.values()} == {"L1","L2"}
    client=StubClient(response(SimpleNamespace(noul=0.5,confidence=None)))
    result=judge("additional_information",{"safe_fixture":"state"},client=client)
    assert len(client.questions) == 1 and len(client.questions[0]) == 1
    assert result.typed_result == "needs_review" and result.abstained
    assert result.selected_path == "agent_review"


def test_relevance_choice_includes_unknown_and_is_agent_reviewed():
    client=StubClient(response(SimpleNamespace(choice="unknown",confidence=0.99)))
    result=judge("search_result_relevance",{"safe_fixture":"state"},client=client)
    assert set(client.questions[0]["judgment"].criteria) == {"relevant","not_relevant","unknown"}
    assert result.abstained and result.selected_path == "agent_review"


def test_sanitized_log_omits_state_and_secrets(tmp_path: Path):
    client=StubClient(response(SimpleNamespace(noul=0.9,confidence=None)))
    result=judge("current_information_search",{"secret":"must not be logged"},client=client)
    log=tmp_path/"events.jsonl"
    append_sanitized_log(log,case_id="case-1",result=result,expected="yes")
    row=json.loads(log.read_text(encoding="utf-8"))
    assert "must not be logged" not in log.read_text(encoding="utf-8")
    assert row["typed_result"] == "yes" and row["score"] == 0.9


def test_track_a_eval_fixtures_are_frozen():
    assert fixture_sha256(Path("evals/track_a_cases.json")) == "d711144f2972c2eb202eb0bc71d0d77bdd426dc9c74cf93fdc817cdeea8794f9"
    assert fixture_sha256(Path("evals/track_a_workflow_cases.json")) == "e66ed149212b366aa80ecb4fa64ba8cbe856001b3146621b2f64f7020a003613"
