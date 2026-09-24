# Consumer Decision UI Reimagining 결과

> 과거 UI 실험 결과입니다. 현재 제품 화면은 단일 답변 카드이며 아래 Inspector와 Required Data 설명은 현행 동작이 아닙니다. 현재 구현·검증은 [Codex 런타임 결과](chapter-b-codex-runtime-mvp.md)를 참고합니다.

## 구현 방향

기존 관리형 화면 구조를 유지하지 않고, SpendGuard를 “돈 쓰기 전에 비교하고 계산하는 소비 판단 도구”로 다시 구성했다.

- 상단에는 제품명, 현재 상태, 새 질문만 남겼다.
- 첫 화면은 단일 질문 입력과 실제 소비 상황으로 시작한다.
- 시나리오는 `사기 전에`, `매달 새는 돈`, `큰돈 계산`, `생활비 줄이기`, `계약하기 전에`의 다섯 묶음으로 정리했다.
- 카드에는 홍보 문구 대신 필요한 입력값을 표시하고, 통일된 stroke SVG 아이콘을 사용했다.
- 결과는 결론, 핵심 숫자, 선택지, 주의할 점, 다음 할 일을 우선 표시한다.
- 사실, 계산, 출처, 가정, 기술 상세는 Inspector로 분리했다.

## 편집 가능한 원문 템플릿

15개 소비 시나리오를 `scenarioDefinitions`에 보관한다. 카드가 선택되면 해당 템플릿을 질문 칸에 넣고 첫 번째 대괄호 입력값을 선택한다. 업로드 기능이 없는 현재 입력 방식에 맞춰 구독·보험·카드 소비내역·견적·연간 지출 템플릿은 “아래에 붙여넣을게”로 명시한다.

- `Tab`으로 다음 대괄호 입력값으로 이동한다.
- 구독 목록·견적서·지출 내역처럼 붙여넣기가 필요한 템플릿에는 바로 사용할 수 있는 안내를 함께 표시한다.
- 이미 작성 중인 질문은 카드 선택으로 덮어쓰지 않는다. 필요한 경우에만 “템플릿으로 바꾸기”를 사용한다.
- 첫 화면의 예시 문구도 15개 원문 중 하나를 날짜 기준으로 보여 주며, 임의로 재작성하지 않는다.
- `needs_input`은 결과가 아닌 보완 단계로 처리한다. 필요한 입력 폼만 표시하며, 응답의 내부 결론·위험·다음 할 일 문구는 결과 카드에 노출하지 않는다.
- 요청·조사·보완 처리 중에는 두 CTA를 모두 비활성화해 중복 요청을 막는다.

## 선택한 시안

이미지 생성기로 만든 [Consumer Decision Rail 시안](../designs/decision-workspace-concepts/concept-d-consumer-decision-rail.png)을 선택했다. 단일 질문 입력, 실제 소비 시나리오, 결과 근거를 한 흐름으로 연결하면서도 가짜 지표나 구현되지 않은 기능을 화면에 추가하지 않는 방향이기 때문이다.

## 유지한 동작 범위

- 기존 `/api/research-needed`, `/api/decisions` 요청과 payload
- 기존 Agent, Decision Pack, Web Search, MCP, Calculation workflow
- `missing_fields` 기반의 동적 추가 입력
- 실제 계산 결과가 있을 때만 핵심 숫자를 표시하는 규칙

## Purchase Required Data 회귀 수정

### 원인

기존 `/api/decisions` 경로는 질문의 키워드만 보고 `OpenAIAnalyzer.analyze()` 안에서 intake와 Web Search를 한 번에 수행했다. 그 뒤 Decision Pack이 별도 문자열 `missing_fields`와 폼 payload만 검사했기 때문에 Agent의 `known_facts`에 있던 “나고야 항공권”과 “37만원”을 Code-owned 필수 필드 검사에서 재사용하지 못했다. Purchase 공통 규칙은 실제 시나리오와 무관하게 `purpose`도 요구했고, OR 조건 전체를 단일 필드명으로 반환했다. Required Data가 부족해도 검색은 이미 끝난 뒤였다.

분리 경로를 처음 추가했을 때는 `known_data`를 `dict[str, Any]`로 선언해 OpenAI Agents SDK의 strict output schema가 이를 거부했다. 예외가 “The agent could not analyze this question.”로 일반화되어 화면에 표시됐다.

### 수정

- Decision workflow intake는 Web Search를 비활성화한 별도 Agent 실행으로 분리하고, 고정된 typed `KnownDecisionData` schema로 canonical `known_data` 값을 반환하도록 했다. SDK strict JSON Schema 생성 검증을 추가했다.
- Code는 Agent `known_data`와 사용자가 보완한 값들을 canonical field ID로 합친 뒤 Required Data를 검사한다. display 문구나 `known_facts` 문자열 매칭은 사용하지 않는다.
- Purchase 공통 필수값에서 generic `purpose`를 제거했다. `price` / `price_confirmation_needed` OR 조건은 `price`라는 canonical 입력만 반환하므로 UI에 OR 문구나 내부 field ID를 노출하지 않는다.
- 항공권의 최신 가격 비교는 목적지·가격 외에 출발지, 여행 날짜, 편도/왕복이 명시되기 전까지 `needs_input`으로 반환한다. 이 단계의 Web Search/MCP 호출은 0회이며 `sources`와 `calculations`는 빈 배열이다.
- 모든 필수값이 준비된 다음에만 Web Search를 실행하며, 검색 입력에는 정규화된 사용자 제공 조건만 전달한다. 사용자 미제공 출발지·날짜·경로는 보충하거나 추정하지 않는다.
- UI는 사전 keyword check만으로 “정보 조사 중”을 표시하지 않으며, 서버가 반환한 canonical missing field에 해당하는 한국어 질문만 표시한다. 기존 시나리오 숨김 및 Required Data 위치 동작은 유지한다.

Phase 7 고정 fixture와 expected label은 변경하지 않았다. Phase 7 평가 경로의 기존 규칙도 그대로 유지해 완료 결과의 재현성을 보존했다. 새 canonical Required Data 동작은 production Decision API 경로에 한정했다.

## 검증

- Purchase Required Data 통합 회귀: 입력된 `target`·`price`는 재요청하지 않고, 부족한 출발지·날짜·편도/왕복만 반환했다. 이 상태에서 Web Search callback 0회, MCP 호출 0회, `sources=[]`, `calculations=[]`를 확인했다.
- 같은 질문에 명시적 출발지·날짜·편도/왕복을 보완하면 연구 callback 1회로 진입했고, 검색 입력에 정규화된 명시 조건만 전달되는 것을 확인했다.
- `uv run pytest --basetemp=.tmp-pytest-flight-final -p no:cacheprovider`: 101 passed.
- Phase 7 fixed workflow 평가 경로는 수정하지 않았고 고정 평가 결과 테스트가 계속 통과했다.
- `tests/test_workspace_ui.py`: 5 passed. UI JavaScript 구문 검사와 `uv lock --check`, `git diff --check` 통과.
- Chrome DevTools remote-debugging 포트가 실행 환경에서 열리지 않아 브라우저 자동화 스크립트는 실행하지 못했다.
- `node --check src/spendguard/static/app.js` 성공
- `uv run pytest tests/test_workspace_ui.py -q`: 5 passed
- 1440×1100, 1280×1100, 1024×1000, 390×844, 320×720에서 초기 화면을 확인했다.
- 모든 폭에서 `document.documentElement.scrollWidth`가 viewport 폭을 넘지 않았다.
- 15개 카드와 5개 그룹이 렌더링되는 것을 확인했다.
- 할부 vs 일시불 카드에서 첫 `[가격]`이 자동 선택되고, `Tab` 후 `[금리]`이 선택되는 것을 확인했다.
- `needs_input` 응답에서 필요한 입력 폼만 보이고 결과 영역은 숨겨지는 것을 브라우저에서 확인했다.
- 진행 중 CTA 비활성화와 96px 질문 입력 영역 높이를 브라우저에서 확인했다.
- 빠른 두 번 submit에도 사전 확인 1회와 결정 요청 1회만 발생하며, 진행 중에는 전체 화면 차단 레이어와 `inert`가 활성화되는 것을 브라우저에서 확인했다.
- 캡처: [시안 및 viewport 기록](../designs/decision-workspace-concepts/README.md)

## 제한 사항

- 결과 상태의 실데이터 검증은 기존 API 응답 계약에 의존한다. 검증용 가짜 소비 데이터는 제품 화면이나 저장소에 추가하지 않았다.
