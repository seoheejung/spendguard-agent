# SpendGuard

> MCP 기반 비용 의사결정 AI Agent

## 개요

SpendGuard는 구매·구독·계약·생활비와 관련된 질문을 분석하고, 필요한 정보를 확인한 뒤 계산·최신 정보 검색·선택지 비교를 통해 검증 가능한 판단 근거를 제공하는 AI Agent 프로젝트입니다.

LLM이 모든 계산과 판단을 직접 수행하는 구조가 아니라, 판단과 설명은 Agent가 담당하고 계산은 결정론적 Tool/MCP로 분리합니다.

## 해결하려는 문제

- 소비 관련 질문에서 필요한 조건 누락
- 할부·대출·TCO·연간 절감액 계산 오류 가능성
- 가격·요금제·정책 등 변동 정보의 최신성 문제
- 근거 없는 추천
- 사실·가정·계산·Agent 판단의 혼합

## 핵심 구조

```mermaid
flowchart TD
    User["User"] --> Agent["SpendGuard Agent"]
    Agent --> Intent["Intent / Required Data"]
    Intent --> MCP["SpendGuard MCP"]
    Intent --> Search["Web Search"]
    MCP --> Calc["Deterministic Calculation"]
    Search --> Evidence["Current Evidence"]
    Calc --> Verify["Verification"]
    Evidence --> Verify
    Verify --> Result["Decision Result"]
```

## 기술 스택

| 구분 | 기술 |
| --- | --- |
| Language | Python 3.13 |
| API | FastAPI |
| Agent | OpenAI Agents SDK |
| LLM API | OpenAI Responses API |
| MCP | FastMCP |
| HTTP | HTTPX |
| Validation | Pydantic |
| Test | pytest |
| Frontend | HTML / CSS / JavaScript |

## 프로젝트 구조

```text
spendguard-agent/
├── .agents/
│   └── skills/
│       └── spendguard-phase-workflow/
│           └── SKILL.md
├── .project/
│   └── plan.md
├── docs/
│   └── instructions/
│       └── phase1-core-agent.md
├── .env.example
├── .gitignore
├── AGENTS.md
├── DESIGN.md
└── README.md
```

## 개발 단계

| Phase | 범위 | 상태 |
| --- | --- | --- |
| Phase 0 | Repository Bootstrap | 완료 |
| Phase 1 | Core Agent | 예정 |
| Phase 2 | Calculation Tools | 예정 |
| Phase 3 | MCP Server | 예정 |
| Phase 4 | Current Information Research | 예정 |
| Phase 5 | Decision Packs | 예정 |
| Phase 6 | Evaluation | 예정 |

## 실행

아직 실행 가능한 애플리케이션이 없습니다.

Phase 1 구현 및 실제 실행 검증 후 실행 방법을 추가합니다.

## 문서

| 문서 | 역할 |
| --- | --- |
| `.project/plan.md` | 프로젝트 전체 기획 기준 |
| `AGENTS.md` | 저장소 공통 작업 규칙 |
| `DESIGN.md` | Web UI 디자인 기준 |
| `docs/instructions/phase1-core-agent.md` | Phase 1 작업 범위와 완료 기준 |
| `.agents/skills/spendguard-phase-workflow/SKILL.md` | Phase 작업 반복 절차 |
