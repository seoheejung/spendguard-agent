# Decision Workspace UX Refinement Chapter 결과

## 변경 전 UX 문제

- Ask와 Decision Pack에 질문 입력이 각각 있어 같은 질문을 두 번 입력해야 했다.
- JSON 입력, Direct Function/MCP 선택, Tool 이름, Agent structured output 같은 구현 용어가 기본 화면에 노출됐다.
- 계산 조작 화면이 결정 workflow보다 먼저 보이고, 결과보다 입력 Form이 화면을 차지했다.
- Sources, assumptions, calculation trace가 사용자 결과와 분리된 개발자용 화면 구조였다.

## 변경한 화면 구조

`DESIGN.md`는 변경하지 않았다. Workspace는 아래 사용자 흐름으로 재구성했다.

```text
Question → Required Data → Research / Calculation → Decision Result → Inspector
```

- Header: 현재 decision 상태만 표시한다.
- Sidebar: New decision과 6개 Decision Type 질문 템플릿만 제공한다. 템플릿은 질문 입력을 돕고 routing을 강제하지 않는다.
- Workspace: 하나의 자연어 질문 Form, 진행 상태, 조건부 Required Data Form, Decision Result 순서다.
- Inspector: 결과가 있을 때 Facts, Calculations, Sources, Assumptions와 접힌 Technical details를 표시한다.

기본 화면에서 OpenAI Agent output, Direct Function/MCP 선택, Tool 이름, Phase 번호, raw JSON, backend endpoint는 제거했다. Tool 이름과 formula는 Inspector의 접힌 Technical details에서만 확인할 수 있다.

## 단일 입력과 Required Data UX

질문은 하나의 `#question` textarea에서만 입력한다. UI는 기존 `/api/decisions`의 첫 결과를 그대로 사용하고, `needs_input`의 code-owned `missing_fields`만 읽어 추가 Form을 동적으로 만든다. 사용자는 JSON을 작성하지 않으며, UI가 입력값을 기존 payload 형식으로 구성해 같은 질문으로 다시 요청한다.

기존 `/api/research-needed`는 Researching 상태 표시에 계속 사용하고, `/api/decisions`는 기존 Agent, Web Search, Decision Pack, stdio MCP workflow를 그대로 실행한다. 새 API나 business logic은 추가하지 않았다.

## Decision Result와 Inspector

기본 결과 카드의 우선순위는 Conclusion, Key Numbers, Options, Risks, Next Actions다. 계산값이 있을 때만 Key Numbers를 표시하며, 근거 없는 절약 수치나 가격을 생성하지 않는다.

Inspector는 다음 trace를 유지한다.

- Facts: 기존 facts와 사용자가 추가한 Required Data
- Calculations: 사용자 친화적인 계산 이름과 결과
- Sources: 확인 사실, 출처명, 링크, 조회 시각
- Assumptions
- Technical details: Pack 식별자, Tool 이름, formula trace

## 검증

- `node --check src/spendguard/static/app.js` 성공
- Workspace/Decision Pack/Phase 7 관련 테스트: 44 passed
- Desktop 1440×1100 로컬 화면 확인: 단일 질문 Form, 6개 템플릿, 결과 우선 구조를 확인했다.
- Mobile 500×844 로컬 화면 확인: 단일 열 Workspace, 가로 스크롤 템플릿, 질문 Form 우선 구조를 확인했다.
- UI contract 테스트는 단일 textarea, JSON/Direct/MCP 기본 UI 제거, dynamic required fields, Inspector trace, responsive/reduced-motion 기준을 검증한다.
- 기존 `tests/test_decision_packs.py`의 6개 Pack 및 초기 절약 시나리오 15종 coverage가 통과했다.
- 기존 `tests/test_phase7_end_to_end_evaluation.py`의 고정 평가 데이터와 expected 결과를 수정하지 않고 UI contract만 새 구조로 갱신했다.

## 범위와 미완료 사항

- Agent, Jev, Web Search, MCP, Calculation Tool, Decision Pack business logic과 backend API 계약은 변경하지 않았다.
- 새 Decision Pack, Calculation Tool, 외부 서비스, History, Reports, 계정 기능은 추가하지 않았다.
- Technical details는 Inspector에서만 제공하며, 기본 화면에 개발자용 통합 콘솔을 다시 노출하지 않았다.
