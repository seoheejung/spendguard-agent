# Phase 4.5. Decision Workspace UI

> Phase 1~4에서 구현한 Agent, Jev, Calculation Tool, MCP 결과를 실제 SpendGuard 화면 구조로 연결하는 단계

## 1. 목적

기존 기본 Web UI를 `DESIGN.md`의 Decision Workspace 구조로 확장한다.

새로운 의사결정 기능을 추가하는 단계가 아니라, 지금까지 실제 구현된 기능과 상태를 재사용 가능한 UI 구조로 표현하는 단계다.

## 2. 사전 조건

- Phase 4 MCP Server 완료
- Phase 4 관련 테스트 통과
- Agent, Jev 평가 결과, Calculation Tool, MCP 출력 구조 확인 완료

Phase 4가 완료되지 않았다면 진행하지 않는다.

## 3. 구현 범위

- Decision Workspace 기본 Layout
- Sidebar Navigation
- Search / Ask 입력 영역
- Agent Status 표시
- Decision 상태 표현
- 기존 Agent 분석 결과 표시
- 기존 Calculation 결과 표시
- MCP 실행 결과 표시
- Detail / Inspector 기본 구조
- Responsive / Accessibility 적용
- 관련 UI 테스트 및 실행 검증

## 4. 화면 구조

```text
Header
├── Search / Ask
└── Agent Status

Sidebar
├── Today
├── Decisions
├── Reports
├── Sources
└── Settings

Workspace
├── Question / Input
├── Decision Status
├── Decision Cards
└── Detail / Inspector
```

구현되지 않은 기능은 Navigation이나 Placeholder로 미리 노출하지 않는다.

## 5. 상태

현재 실제 구현 가능한 상태만 사용한다.

```text
Needs Input
Calculating
Review
Ready
```

`Researching`은 Web Search가 구현되는 후속 Phase에서 추가한다.

## 6. 디자인 기준

`DESIGN.md`를 기준으로 구현한다.

핵심 원칙:

- 콘텐츠 구조 우선
- 재사용 가능한 Layout
- 정적 / 동적 요소 분리
- Liquid Glass는 Navigation, Floating Control, Inspector 등 일부 Layer에만 사용
- 계산표와 핵심 숫자는 Solid UI 유지
- Motion은 상태 전환과 사용자 Action에만 사용
- Video Hero, 상시 WebGL, 불필요한 Three.js 사용 금지
- Motion, Glass, Gradient 제거 후에도 정보 구조 유지

## 7. 재사용성

페이지별 전용 Layout을 만들지 않는다.

공통 구조:

```text
AppShell
Sidebar
Header
Workspace
Grid
Stack
Panel
Card
Inspector
```

Decision Card는 특정 Decision Type에 종속되지 않도록 데이터 기반으로 구성한다.

새로운 Decision Type 추가 시 공통 Component와 CSS 수정이 최소여야 한다.

## 8. 데이터 연결

UI는 실제 구현된 결과만 표시한다.

- OpenAI Agent Structured Output
- Jev 평가 또는 판단 결과 중 현재 노출이 필요한 값
- Calculation Tool 결과
- MCP Tool 결과
- 오류 상태

가짜 통계, 임의 절감액, 구현되지 않은 기능용 Placeholder를 만들지 않는다.

## 9. 제외

이번 Phase에서는 구현하지 않는다.

- Web Search
- `Researching` 실제 동작
- Decision Pack workflow
- 데이터베이스
- 사용자 인증
- Multi-Agent
- 자동 구매 또는 계약
- Remote MCP
- 새로운 계산 기능

## 10. 검증

최소 확인:

- Desktop / Mobile Layout
- Keyboard Navigation
- 핵심 숫자 잘림 여부
- 제목과 설명 길이 증가
- 카드 수 증가 시 Layout 유지
- Motion 비활성화 상태
- Glass / Gradient 제거 상태
- 실제 API 오류 표시
- 구현되지 않은 기능 노출 여부

## 11. 결과 문서

```text
docs/results/phase4.5-decision-workspace-ui.md
```

기록:

- 구현 화면
- 재사용 Component
- 상태 표현
- 실제 연결 데이터
- Responsive 검증
- Accessibility 검증
- 성능 관련 확인
- 미완료 사항

## 12. 완료 기준

- Decision Workspace 기본 화면 구현
- 실제 Agent / Calculation / MCP 결과 연결
- 재사용 가능한 Layout 구성
- 구현되지 않은 기능 미노출
- Responsive / Accessibility 확인
- 관련 테스트 통과
- 결과 문서 작성
- README 실제 상태 반영
- `uv run --no-cache --no-sync pytest` 성공
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
- 완료 후 commit / push
