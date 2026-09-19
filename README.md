# SpendGuard

SpendGuard는 소비 관련 자연어 질문에서 의도와 확인된 사실, 추가로 필요한 정보를 구조화하는 AI 의사결정 지원 프로젝트입니다.

## 현재 구현 상태

Phase 1 Core Agent Baseline이 구현되어 있습니다.

- FastAPI 애플리케이션과 기본 웹 UI
- OpenAI Agents SDK 기반 단일 Agent
- Pydantic Structured Output: `intent`, `summary`, `known_facts`, `missing_fields`, `assumptions`
- 7개 Intent: `purchase`, `recurring_cost`, `finance_cost`, `ownership_cost`, `quote_audit`, `budget_optimization`, `unknown`
- Phase 2 비교용 고정 평가 데이터 17건

Jev, MCP, 계산 도구, Web Search, 사용자 인증, 데이터베이스는 구현하지 않았습니다.

## Phase 상태

| Phase | 상태 | 범위 |
| --- | --- | --- |
| Phase 1 | 완료 | Core Agent Baseline |
| Phase 2 | 예정 | Jev Decision Layer Evaluation |

## Phase 1 실제 평가

고정 평가 데이터 17건을 `OPENAI_MODEL`에 설정된 모델로 실행한 결과는 다음과 같습니다.

- Intent 정답: 16건
- Intent 정확도: 94.12% (16/17)
- 실패 케이스: `ambiguous-001` — expected `unknown`, actual `budget_optimization`
- API 오류: 0건
- pytest: 10 passed

## 실행

Python 3.13과 uv가 필요합니다.

```powershell
uv sync --all-groups
$env:OPENAI_API_KEY = "..."
$env:OPENAI_MODEL = "..."
uv run uvicorn spendguard.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 열면 됩니다. API 키 또는 모델 설정이 없으면 `/api/analyze`는 설정 오류를 `503`으로 반환합니다.

## 검증과 평가

```powershell
uv run pytest
uv run python scripts/evaluate_phase1.py
```

평가 스크립트는 `evals/phase1_cases.json`의 고정 17건을 현재 설정된 OpenAI 모델로 실행하고 Intent 정확도와 실패 케이스를 JSON으로 출력합니다.

## 문서

- `.project/plan.md`: 프로젝트 계획
- `docs/instructions/phase1-core-agent.md`: Phase 1 범위
- `docs/results/phase1-core-agent.md`: 구현 및 검증 결과
