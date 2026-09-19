# Phase 4.5 Decision Workspace UI 결과

## 구현 화면 구조

- Header: SpendGuard 식별, Agent 상태
- Sidebar: Ask, Agent result, Calculations, Calculation / MCP result
- Workspace: 자연어 질문 입력, Decision 상태, Agent 결과, Calculation / MCP 실행
- Inspector: 선택 결과의 입력, 중간값, 결과 상세

구현되지 않은 Reports, Sources, Settings, Web Search, Researching, Decision Pack workflow 미노출.

## 재사용 구조

- `AppShell`: Header, Sidebar, Workspace, Inspector
- `solid-panel`: 입력, 계산, 결과 Card 공통 Panel
- `card-grid`: Agent 결과와 Calculation 결과 공통 Grid
- `valueRows`: Calculation 입력, 중간값, 결과 공통 표시
- `toolDefinitions`: 여섯 Calculation Tool 입력 Form 데이터

## 실제 연결 데이터

| UI 영역 | 실제 연결 |
| --- | --- |
| Agent 결과 | `POST /api/analyze`의 `intent`, `summary`, `known_facts`, `missing_fields`, `assumptions` |
| Direct Calculation | `POST /api/calculations/direct`의 Phase 3 결과 |
| MCP Calculation | `POST /api/calculations/mcp`의 Phase 4 stdio MCP Client 결과 |
| 계산 추적 | `inputs`, `formula`, `intermediate`, `result` |
| API 오류 | Agent 502/503, Calculation 422, MCP 502 메시지 |

임의 사용자 데이터, 절감액, 통계, Web Search 결과 없음.

## Decision 상태

| 상태 | 실제 UI 조건 |
| --- | --- |
| Needs Input | 초기 상태, 입력 또는 API 오류 상태 |
| Calculating | Direct Calculation 또는 MCP Tool 실행 중 |
| Review | Agent structured output 수신 상태 |
| Ready | Direct Calculation 또는 MCP 결과 수신 상태 |

`Researching` 상태 미구현 및 미노출.

## Responsive 및 Accessibility 검증

| 항목 | 결과 |
| --- | --- |
| Desktop 1440 × 1100 | Sidebar, Workspace, Inspector 3열 구조 확인 |
| Mobile 500 × 844 | 단일 열 Workspace, 가로 스크롤 Navigation, 핵심 입력·수치 영역 확인 |
| 긴 제목·설명·수치 | `overflow-wrap` 적용 |
| 카드 증가 구조 | CSS Grid 기반 `card-grid`, 데이터 기반 결과 Card |
| Keyboard 구조 | Skip link, native form control, button, link, visible focus outline |
| Motion 비활성화 | `prefers-reduced-motion: no-preference` 내부 한정 Motion |
| Glass 사용 범위 | Navigation, Inspector 한정 투명 Layer |
| 핵심 숫자 | Solid Panel 및 monospace 표시 |

Video Hero, WebGL, Three.js, backdrop filter 미사용.

## 테스트

| 항목 | 결과 |
| --- | --- |
| Agent API 기존 동작 | 통과 |
| Direct Calculation API | 통과 |
| stdio MCP Calculation API | 통과 |
| Calculation 입력 오류 422 | 통과 |
| Workspace UI 계약 | 3 passed |
| 전체 `uv run --no-cache --no-sync pytest` | 41 passed |

## 범위 제외

- Web Search 및 Researching
- Jev production routing
- Decision Pack workflow
- Reports, Sources, Settings
- 사용자 인증 및 데이터베이스
- Remote MCP
