"""Decision Workspace user-first UX contract tests."""

from pathlib import Path


STATIC_DIR = Path(__file__).parents[1] / "src" / "spendguard" / "static"


def test_workspace_has_one_question_flow_without_developer_controls() -> None:
    page = (STATIC_DIR / "index.html").read_text(encoding="utf-8")

    assert page.count('<textarea id="question"') == 1
    assert 'id="processing-blocker"' in page
    assert 'id="processing-message"' in page
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
    assert "sidebar" not in page
    assert "progress-panel" not in page
    assert "app-shell" not in page
    assert "SPEND WITH CLARITY" not in page
    assert "돈 쓰기 전에" in page
    assert "비교하고 계산해, 더 나은 선택을" in page


def test_workspace_uses_canonical_prompts_and_user_scenario_groups() -> None:
    page = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    for prompt in (
        "[제품명]을 사려고 해. 같은 제품뿐 아니라 비슷한 대안까지 찾아서 가격과 조건을 비교해줘.",
        "결제 중인 구독 목록을 아래에 붙여넣을게. 기능이 겹치거나 거의 쓰지 않는 서비스를 찾아서 무엇부터 정리하면 좋을지 알려줘.",
        "현재 요금제와 월 데이터 사용량을 줄게. 필요 이상으로 내고 있는 비용이 있는지 보고, 더 맞는 요금제가 있는지 비교해줘.",
        "가입한 보험의 보장 내용과 보험료를 아래에 붙여넣을게. 서로 겹치는 보장과 필요 이상으로 많이 들어간 부분이 있는지 구분해줘.",
        "최근 한 달 소비내역을 아래에 붙여넣을게. 내 지출 패턴에서 실제로 받을 수 있는 카드 혜택을 비교하고 어디서 가장 많이 아낄 수 있는지 계산해줘.",
        "[제품명]을 [가격]원에 살까 고민 중이야. 얼마나 자주 쓸지, 대체할 방법은 없는지, 이 돈을 다른 데 썼을 때까지 고려해서 사도 괜찮은지 따져줘.",
        "일주일 식비는 [예산]원이고 [인원]명이 먹어. 재료를 최대한 돌려 쓰면서 예산 안에서 장볼 목록과 식단을 짜줘.",
        "[여행지]로 [기간] 동안 여행할 거야. 여행 만족도는 크게 떨어뜨리지 않으면서 항공숙박교통식비를 줄일 수 있는 방법을 찾아줘.",
        "[차량]을 보유하면 보험료, 세금, 연료비, 정비비, 감가상각까지 포함해서 앞으로 5년 동안 실제로 얼마가 드는지 계산해줘.",
        "[가격]원짜리 제품을 [금리]%로 [개월]개월 할부하려고 해. 일시불과 비교해서 실제로 얼마를 더 내는지 계산해줘.",
        "대출잔액 [잔액]원, 현재 금리 [금리]%, 남은 기간 [기간]이야. 금리를 [새 금리]%로 낮췄을 때 총이자가 얼마나 줄어드는지 계산해줘.",
        "받은 견적 내용을 아래에 붙여넣을게. 가격이 유독 높아 보이는 항목, 꼭 필요한 항목, 빼거나 조정해볼 만한 항목을 구분해줘.",
        "[상품/서비스] 계약을 앞두고 있어. 가격이나 조건에서 협상해볼 만한 부분을 찾아주고, 실제로 어떻게 말하면 좋을지도 써줘.",
        "최근 3개월 지출내역을 아래에 붙여넣을게. 만족도는 거의 떨어뜨리지 않으면서 줄일 수 있는 지출을 찾아서 1년 기준 절감액을 계산해줘.",
        "[제품명]을 [가격]원에 사려고 해. 지금 사는 것과 기다리는 것, 중고로 사는 것, 다른 제품을 고르는 것까지 비교해서 비용 면에서 어떤 차이가 있는지 보여줘.",
    ):
        assert prompt in script
    for group in ("사기 전에", "매달 새는 돈", "큰돈 계산", "생활비 줄이기", "계약하기 전에"):
        assert group in script
    assert 'id="scenario-groups"' in page
    assert "scenarioDefinitions" in script
    assert "activeScenarioGroup" in script
    assert "dataScenarioGroup" not in script
    assert "dataset.scenarioGroup" in script
    assert "inputHints" in script
    assert "setSelectionRange" in script
    assert 'event.key !== "Tab"' in script
    assert "createScenarioIcon" in script
    assert "pasteNote" in script
    assert "카드사·은행 앱에서 복사한 내역이나 표 형식의 지출내역을 붙여넣을 수 있습니다." in script
    for previous_label in ("Ready to help", "New decision", "Decision types", "Purchase", "Recurring cost", "금융 비용"):
        assert previous_label not in page
    for status in ("요청 확인 중", "정보 조사 중", "추가 정보 필요", "준비됨", "검토 필요"):
        assert status in script


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
    assert "정보 조사 중" in script
    assert "Calculating" not in script
    assert 'querySelectorAll("#decision-form button, #required-data-form button")' in script
    assert "button.disabled = true" in script
    assert "button.disabled = false" in script
    assert "requestInFlight" in script
    assert "if (state.requestInFlight) return;" in script
    assert "setRequestLock(true);" in script
    assert "setRequestLock(false);" in script
    assert "workspace.inert = locked;" in script
    assert "siteHeader.inert = locked;" in script
    assert "has-active-decision" in script
    assert 'if (decision.status === "needs_input") {' in script
    assert "renderRequiredData(decision.missing_fields);\n    } else if (decision.status === \"ready\") {\n      renderDecisionResult(decision);" in script
    assert "decisionCards.replaceChildren();\n  resultSection.hidden = true;\n  inspector.hidden = true;" in script


def test_workspace_prioritizes_result_and_keeps_traceability_in_inspector() -> None:
    page = (STATIC_DIR / "index.html").read_text(encoding="utf-8")
    script = (STATIC_DIR / "app.js").read_text(encoding="utf-8")

    assert 'id="decision-result"' in page
    assert "결론" in script
    assert "핵심 숫자" in script
    assert "선택지" in script
    assert "주의할 점" in script
    assert "다음 할 일" in script
    assert "사실" in script
    assert "계산" in script
    assert "출처" in script
    assert "가정" in script
    assert "기술 세부 정보" in script
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
    assert "textarea { min-height: 88px" in stylesheet
    assert ".question-composer button:disabled" in stylesheet
    assert ".processing-blocker" in stylesheet
    assert ".processing-track" in stylesheet
    assert ".scenario-group-tabs" in stylesheet
    assert ".decision-form { max-width: none" in stylesheet
