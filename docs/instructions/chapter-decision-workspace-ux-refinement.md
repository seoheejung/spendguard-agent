# Chapter A. Decision Workspace UX Refinement

> Phase 0~7에서 검증한 기능은 유지하고, SpendGuard를 개발자용 통합 화면이 아닌 실제 사용자 중심 Decision Workspace로 재구성하는 UI/UX 개선 작업

## 1. 목적

현재 화면은 Agent, Decision Pack, Calculation, MCP 등 내부 구현 단위가 사용자 인터페이스에 직접 노출되어 있다.

이번 작업의 목적은 기능을 추가하는 것이 아니라 기존 기능을 하나의 자연스러운 의사결정 흐름으로 재구성하는 것이다.

핵심 사용자 흐름:

```text
질문 입력
→ 필요한 정보 확인
→ 필요한 추가 입력
→ 검색 / 계산
→ 결과 검토
→ 근거 / 출처 확인
```

`DESIGN.md`는 변경하지 않고 현재 디자인 기준 그대로 적용한다.

## 2. 사전 조건

- Phase 0~7 완료
- Phase 7 End-to-End Evaluation 완료
- 기존 테스트 전체 통과
- 현재 backend API, Agent, Web Search, MCP, Calculation Tool, Decision Pack 동작 확인

기존 검증 결과를 깨뜨리는 방식으로 UI를 수정하지 않는다.

## 3. 현재 UX 문제

아래 문제를 우선 해결한다.

- Agent, MCP, Direct Function, Phase 번호 등 내부 구현 용어가 사용자 화면에 직접 노출
- Ask와 Decision Pack에서 질문을 중복 입력
- 사용자가 JSON을 직접 입력해야 하는 구조
- Direct Function / MCP 실행 경계를 사용자가 선택
- 계산 Tool 조작 화면이 사용자 workflow보다 앞에 노출
- 입력 Form이 화면 대부분을 차지하고 결과가 상대적으로 약함
- 오른쪽 Inspector 영역 활용 부족
- Navigation이 사용자 작업이 아니라 내부 구현 단위 중심
- 긴 세로 Form으로 인해 실제 의사결정 흐름이 한눈에 보이지 않음

## 4. 변경 원칙

- backend business logic 재구현 금지
- Agent, Jev, Web Search, MCP, Calculation Tool 재구현 금지
- Phase 7 평가 기준과 고정 eval 데이터 변경 금지
- 기존 API contract는 가능한 범위에서 유지
- UI에서 내부 구현 세부사항을 숨기되 traceability는 유지
- 사용자 입력은 자연어를 기본으로 유지
- 필요한 추가 입력만 상황에 따라 노출
- 결과와 핵심 숫자를 입력 Form보다 우선
- 구현되지 않은 기능 추가 금지
- 새로운 Decision Pack 추가 금지
- 새로운 계산 기능 추가 금지

## 5. 목표 Information Architecture

### Header

```text
SpendGuard
현재 Decision 상태
새 의사결정
```

Agent 이름이나 내부 실행 엔진 상태를 사용자에게 기본 노출하지 않는다.

### Sidebar

실제 구현된 사용자 기능만 표시한다.

권장 구조:

```text
New Decision

Decision Types
- Purchase
- Recurring Cost
- Finance Cost
- Ownership Cost
- Quote Audit
- Budget Optimization
```

Decision Type은 별도 페이지가 아니라 질문 시작을 돕는 template / filter 역할로 사용한다.

Reports, Settings, History 등 구현되지 않은 기능은 표시하지 않는다.

### Workspace

```text
Question
Decision Progress
Missing Information
Decision Result
```

### Inspector

결과가 존재할 때만 실제 근거를 표시한다.

```text
Calculations
Sources
Assumptions
Technical Details
```

Technical Details는 기본 접힘 상태로 두고 MCP Tool 이름, formula trace 등 개발자 성격의 정보가 필요한 경우에만 확인할 수 있게 한다.

## 6. 단일 입력 흐름

사용자 질문 입력창은 하나를 기본으로 한다.

현재처럼:

```text
Ask
→ Agent 분석

Decision Pack
→ 질문 재입력
→ JSON 입력
```

형태로 사용하지 않는다.

목표:

```text
자연어 질문
→ Decision Pack 자동 판단
→ Required Data 확인
→ 누락 정보 Form 자동 표시
→ 기존 Search / MCP 자동 실행
→ Decision Result
```

기존 `/api/analyze`, `/api/decisions`, Calculation API는 필요한 범위에서 재사용한다.

사용자가 JSON을 직접 작성하지 않도록 한다.

필요한 structured payload는 UI가 내부적으로 생성한다.

## 7. Missing Information UX

필수 입력이 부족하면 `Needs Input` 상태에서 해당 필드만 표시한다.

예:

```text
현재 월 요금
[ 80,000 ] 원

월 데이터 사용량
[ 40 ] GB

현재 통신사
[              ]
```

원칙:

- JSON textarea 금지
- 이미 질문에서 확인된 값 재입력 요구 금지
- 단위와 통화 표시
- 한 번에 필요한 필드만 노출
- 사용자가 입력한 값은 Decision Result의 Facts와 연결

## 8. Decision Progress

내부 Tool 이름 대신 사용자 관점의 상태를 사용한다.

```text
요청 확인
정보 확인
비용 계산
결과 검토
완료
```

실제 내부 상태와 연결:

```text
Needs Input
Researching
Calculating
Review
Ready
```

상태를 과장된 animation으로 표현하지 않는다.

## 9. Decision Result

결과가 화면의 중심이 되어야 한다.

우선순위:

```text
Conclusion
Key Numbers
Options
Risks
Next Actions
```

그 아래 또는 Inspector에서:

```text
Facts
Calculations
Assumptions
Sources
```

핵심 금액과 절감액이 존재하면 큰 숫자로 표시한다.

근거 없는 절감액이나 임의 숫자를 생성하지 않는다.

## 10. 내부 구현 정보 노출 기준

기본 사용자 화면에서 숨긴다.

- OpenAI Agent structured output
- Direct Function
- MCP execution boundary
- MCP Tool 이름
- Phase 번호
- internal schema 이름
- raw JSON
- backend endpoint 이름

필요한 traceability는 `Technical Details`에서 확인할 수 있다.

사용자에게는 의미 있는 표현으로 변환한다.

```text
calculate_installment → 할부 비용 계산
compare_costs → 선택지 비용 비교
```

## 11. Calculation UX

기존 Calculation Tool 조작 Panel을 main workflow의 기본 화면으로 사용하지 않는다.

계산은 Decision Pack workflow에서 필요한 경우 자동 실행한다.

수동 Calculation UI를 유지해야 한다면 사용자 main flow와 분리하고 기본 Navigation에서 강조하지 않는다.

계산 결과는 입력값, 계산식, 중간값, 결과를 Inspector에서 추적 가능하게 유지한다.

## 12. Sources UX

Source는 결과와 연결해 표시한다.

최소 표시:

- 확인한 사실
- 출처명
- 링크
- 조회 시각

URL 목록만 나열하지 않는다.

사용자가 어떤 결론의 근거인지 이해할 수 있어야 한다.

## 13. Visual 적용

`DESIGN.md`를 그대로 따른다.

유지:

- Deep Ink base
- Electric Blue / Ice Cyan / Acid Lime 역할 색
- 제한적 Thin Grid
- 계산 숫자의 monospace
- Navigation / Inspector의 제한적 Glass

수정:

- 과도한 technical label 축소
- 큰 제목 반복 축소
- 빈 grid 공간 축소
- Panel 간 시각적 우선순위 강화
- 핵심 Result Card를 Workspace 중심으로 이동
- 긴 세로 Form 최소화

Retrofuturism은 장식 레이어로만 사용하고 개발자 콘솔 형태로 만들지 않는다.

## 14. Responsive

Desktop:

```text
Sidebar | Main Decision Workspace | Inspector
```

Inspector는 실제 상세 정보가 있을 때 의미 있게 사용한다.

Mobile:

```text
Header
Question / Result
Missing Information
Detail Accordion
```

Desktop 3열을 단순 축소하지 않는다.

## 15. Accessibility

- Keyboard Navigation
- Skip Link
- visible focus
- native form control 우선
- 상태 변화 `aria-live`
- 오류 `role="alert"`
- 색상 외 텍스트 상태 표시
- `prefers-reduced-motion` 유지

## 16. 검증

최소 검증:

- 자연어 질문 입력이 한 곳에서 시작되는가
- 동일 질문을 두 번 입력하지 않는가
- 사용자가 JSON을 작성하지 않는가
- Direct / MCP를 사용자가 선택하지 않아도 되는가
- 필수 입력 부족 시 필요한 Field만 표시되는가
- Search / Calculation이 기존 정책대로 실행되는가
- 결과가 입력 Form보다 시각적으로 우선되는가
- Conclusion / Options / Risks / Next Actions 구분이 명확한가
- Calculation / Sources / Assumptions trace가 유지되는가
- 내부 구현 용어가 기본 화면에 노출되지 않는가
- 6개 Decision Pack 모두 동일 Layout을 재사용하는가
- 15개 절약 시나리오가 기존 workflow에서 계속 동작하는가
- Desktop / Mobile 모두 정보 우선순위가 유지되는가
- 기존 Phase 7 평가와 backend 테스트에 회귀가 없는가

## 17. 범위 제외

- 새로운 Decision Pack
- 새로운 Calculation Tool
- 새로운 Web Search 정책
- Jev production routing 추가
- Multi-Agent
- DB / 사용자 계정 / History
- Reports
- 자동 구매 / 계약 / 해지
- Phase 7 평가 데이터 수정
- `DESIGN.md` 변경

## 18. 결과 문서

작성:

```text
docs/results/chapter-decision-workspace-ux-refinement.md
```

기록:

- 변경 전 UX 문제
- 변경한 Information Architecture
- 단일 입력 흐름
- Missing Information 처리
- Decision Result 구조
- Inspector 구조
- 내부 구현 정보 노출 정책
- Desktop / Mobile 검증
- Accessibility 검증
- 기존 기능 회귀 결과
- 미완료 사항

## 19. 완료 기준

- 단일 자연어 질문 흐름 구현
- 중복 질문 입력 제거
- 사용자 JSON 입력 제거
- Direct / MCP 선택 기본 UI 제거
- 내부 구현 용어 기본 화면 노출 제거
- Required Data 기반 추가 입력 UI 구현
- Decision Result 중심 Layout 구현
- Calculation / Sources / Assumptions Inspector 연결
- 기존 6개 Decision Pack 유지
- 초기 절약 시나리오 15종 회귀 확인
- 기존 Phase 7 평가 데이터 변경 없음
- 관련 UI / API / workflow 테스트 통과
- `uv run --no-cache --no-sync pytest` 성공
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
- 결과 문서 작성
- README에는 실제 UX 변경만 필요한 범위에서 반영
- 완료 후 commit / push
