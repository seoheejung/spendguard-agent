"""Runtime boundaries that must work without spending a Codex allowance."""

import asyncio
import sys
from pathlib import Path

import httpx
import pytest

from spendguard.codex_runtime import CodexResult, CodexRunner, CodexUsageLimitError
from spendguard import main as main_module
from spendguard.main import app
from spendguard.calculations import CostComparisonInput, compare_costs


def test_cli_overrides_are_scoped_to_spendguard(monkeypatch):
    monkeypatch.delenv("SPENDGUARD_CODEX_MODEL", raising=False)
    monkeypatch.delenv("SPENDGUARD_CODEX_REASONING_EFFORT", raising=False)
    runner = CodexRunner()
    fresh = runner._command(Path("C:/temporary"))
    resumed = runner._command(Path("C:/temporary"), thread_id="previous-thread", search=False)

    assert fresh[fresh.index("-m") + 1] == "gpt-6-luna"
    assert "model_reasoning_effort='low'" in fresh
    assert "web_search='live'" in fresh
    assert "--ephemeral" not in fresh
    assert "resume" in resumed
    assert "previous-thread" in resumed
    assert "web_search='disabled'" in resumed


def test_usage_limit_reset_parses_cli_message():
    message = "You've hit your usage limit. try again at Sep 25th, 2026 1:50 AM."
    reset_at = CodexRunner._usage_limit_reset(message)
    assert reset_at is not None
    assert reset_at.startswith("2026-09-25T01:50:00")
    assert CodexRunner._usage_limit_reset("try again later") is None


def test_usage_limit_is_429_without_raw_cli_message(monkeypatch):
    class LimitedRunner:
        async def run(self, *_args, **_kwargs):
            raise CodexUsageLimitError("2026-09-25T01:50:00+09:00")

    async def call():
        async def wait_forever(_request):
            await asyncio.sleep(3600)

        monkeypatch.setattr(main_module, "wait_for_disconnect", wait_forever)
        app.state.codex_runner = LimitedRunner()
        app.state.decision_progress = {}
        app.state.decision_sessions = {}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            return await client.post("/api/decisions", json={"question": "S26 가격 비교"})

    response = asyncio.run(call())

    assert response.status_code == 429
    assert response.json()["detail"] == {
        "code": "codex_usage_limit",
        "message": "현재 Codex 사용 한도에 도달했습니다. 초기화 후 다시 시도해 주세요.",
        "reset_at": "2026-09-25T01:50:00+09:00",
    }


def test_follow_up_resumes_saved_thread_without_replaying_history(monkeypatch):
    class RecordingRunner:
        def __init__(self):
            self.calls = []

        async def run(self, _question, **kwargs):
            self.calls.append(kwargs)
            return CodexResult(answer="답변", latency_ms=1, thread_id="codex-thread", resumed=bool(kwargs["thread_id"]))

    runner = RecordingRunner()

    async def call():
        async def wait_forever(_request):
            await asyncio.sleep(3600)

        monkeypatch.setattr(main_module, "wait_for_disconnect", wait_forever)
        app.state.codex_runner = runner
        app.state.decision_progress = {}
        app.state.decision_sessions = {}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            first = (await client.post("/api/decisions", json={"question": "S26 가격 비교"})).json()
            second = (await client.post("/api/decisions", json={
                "question": "S25와 차이", "conversation_id": first["metadata"]["conversation_id"],
                "history": [{"question": "S26 가격 비교", "answer": "이전 답변"}],
            })).json()
        return second

    second = asyncio.run(call())

    assert runner.calls[0]["thread_id"] is None
    assert runner.calls[1]["thread_id"] == "codex-thread"
    assert second["metadata"]["resumed"] is True


def test_search_budget_resumes_without_search_and_follow_up_reuses_thread(tmp_path):
    cli = tmp_path / "fake_codex.py"
    cli.write_text(
        "import json, sys, time\n"
        "prompt = sys.stdin.read()\n"
        "print(json.dumps({'type': 'thread.started', 'thread_id': 'saved-thread'}), flush=True)\n"
        "if sys.argv[1] == 'new':\n"
        "    for index in range(4):\n"
        "        print(json.dumps({'type': 'item.started', 'item': {'type': 'web_search'}}), flush=True)\n"
        "        if index < 3:\n"
        "            print(json.dumps({'type': 'item.completed', 'item': {'type': 'web_search', 'action': {'type': 'search'}, 'results': []}}), flush=True)\n"
        "    time.sleep(20)\n"
        "elif sys.argv[2] == 'no-search' and 'refresh current price' in prompt:\n"
        "    print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'SPENDGUARD_NEEDS_FRESH_SEARCH'}}), flush=True)\n"
        "    print(json.dumps({'type': 'turn.completed'}), flush=True)\n"
        "else:\n"
        "    if sys.argv[2] == 'search':\n"
        "        print(json.dumps({'type': 'item.completed', 'item': {'type': 'web_search', 'action': {'type': 'search'}, 'results': []}}), flush=True)\n"
        "    print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': '최종 답변'}}), flush=True)\n"
        "    print(json.dumps({'type': 'turn.completed'}), flush=True)\n",
        encoding="utf-8",
    )

    class FakeRunner(CodexRunner):
        def _command(self, _workdir, *, thread_id=None, search=True):
            self.commands.append((thread_id, search))
            return [sys.executable, str(cli), thread_id or "new", "search" if search else "no-search"]

    async def call():
        runner = FakeRunner(timeout_seconds=10)
        runner.executable = sys.executable
        runner.commands = []
        first = await runner.run("삼성 S26 비교")
        follow_up = await runner.run("S25와 차이", thread_id=first.thread_id)
        refreshed = await runner.run("refresh current price", thread_id=first.thread_id)
        return first, follow_up, refreshed, runner.commands

    first, follow_up, refreshed, commands = asyncio.run(call())
    assert first.search_calls <= 4
    assert first.codex_runs == 2
    assert first.thread_id == "saved-thread"
    assert first.resumed is False
    assert follow_up.search_calls == 0
    assert follow_up.codex_runs == 1
    assert follow_up.resumed is True
    assert commands[-3:] == [("saved-thread", False), ("saved-thread", False), ("saved-thread", True)]
    assert refreshed.search_calls == 1
    assert refreshed.codex_runs == 2


def test_cli_usage_limit_is_detected_without_retry(tmp_path):
    cli = tmp_path / "limit.py"
    cli.write_text(
        "import sys\n"
        "sys.stdin.read()\n"
        "sys.stderr.write(\"You've hit your usage limit. try again at Sep 25th, 2026 1:50 AM.\\n\")\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )

    class FakeRunner(CodexRunner):
        def _command(self, _workdir, *, thread_id=None, search=True):
            return [sys.executable, str(cli)]

    runner = FakeRunner(timeout_seconds=5)
    runner.executable = sys.executable
    with pytest.raises(CodexUsageLimitError) as captured:
        asyncio.run(runner.run("추가 질문"))
    assert captured.value.reset_at.startswith("2026-09-25T01:50:00")


def test_fresh_and_resumed_processes_use_runtime_workspace(tmp_path):
    cli = tmp_path / "cwd.py"
    cli.write_text(
        "import json, os, sys\n"
        "sys.stdin.read()\n"
        "print(json.dumps({'type': 'thread.started', 'thread_id': 'fixture-thread'}), flush=True)\n"
        "print(json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': json.dumps({'answer': os.getcwd(), 'suggested_followups': ['한 번 더 알려줘'], 'sources': []})}}), flush=True)\n"
        "print(json.dumps({'type': 'turn.completed'}), flush=True)\n",
        encoding="utf-8",
    )

    class FakeRunner(CodexRunner):
        def _command(self, _workdir, *, thread_id=None, search=True):
            return [sys.executable, str(cli)]

    async def call():
        runner = FakeRunner(timeout_seconds=5)
        runner.executable = sys.executable
        first = await runner.run("fixture question")
        second = await runner.run("fixture follow-up", thread_id=first.thread_id)
        return first, second

    first, second = asyncio.run(call())
    assert first.answer == second.answer
    assert first.answer.endswith("spendguard-codex-runtime")
    assert first.suggested_followups == ["한 번 더 알려줘"]
    assert second.resumed is True


def test_suggestions_are_separate_from_answer():
    import json

    response = {"answer": "구매는 미루세요.\n\n**이어서 물어볼 만한 질문**\n- 여행비를 먼저 계산해볼까?",
                "suggested_followups": ["여행비를 먼저 계산해볼까?"], "sources": []}
    events = b"\n".join(json.dumps(item, ensure_ascii=False).encode("utf-8") for item in [
        {"type": "item.completed", "item": {"type": "agent_message", "text": json.dumps(response, ensure_ascii=False)}},
        {"type": "turn.completed"},
    ])
    result = CodexRunner._parse_events(events, 100)
    assert result.answer == "구매는 미루세요."
    assert result.suggested_followups == ["여행비를 먼저 계산해볼까?"]


def test_calculation_trace_rejects_changed_mcp_amount():
    data = {"currency": "KRW", "options": [
        {"name": "기본", "total_cost": 154230}, {"name": "추가 기능", "total_cost": 193030},
    ]}
    observed = compare_costs(CostComparisonInput.model_validate(data)).model_dump(mode="json")
    call = {"tool": "compare_costs", "status": "completed", "arguments": {"data": data}, "result": observed}
    assert main_module.verify_calculation_trace([call]) == 1
    observed["result"]["difference_from_추가 기능"] = "38801.00"
    with pytest.raises(main_module.CodexRuntimeError):
        main_module.verify_calculation_trace([call])


def test_cashflow_claim_uses_signed_code_result():
    answer = "수입 130,000원이 들어와도 월세를 내고 나면 0원입니다. 구매를 미루세요."
    checked, corrected = main_module.align_cashflow_claim(
        answer, {"cashflow_after_fixed_expenses": "-40000"},
    )
    assert corrected is True
    assert "40,000원이 부족합니다" in checked
    assert "0원입니다" not in checked
