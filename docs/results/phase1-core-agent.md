# Phase 1 Core Agent 결과

## 구현 상태

- FastAPI 앱, 단일 OpenAI Agents SDK Agent, Pydantic Structured Output, 기본 웹 UI를 구현했다.
- Agent 출력은 `intent`, `summary`, `known_facts`, `missing_fields`, `assumptions`로 고정했다.
- 지원 Intent는 `purchase`, `recurring_cost`, `finance_cost`, `ownership_cost`, `quote_audit`, `budget_optimization`, `unknown`이다.
- Jev, MCP, 계산 도구, Web Search, 인증, 데이터베이스, 다중 Agent는 추가하지 않았다.

## 고정 평가 데이터

`evals/phase1_cases.json`에 17건을 생성했다. 각 Intent의 명확한 질문, 모호한 질문 2건, 정보 충분/부족 질문, 범위 밖 질문을 포함한다. 이 파일은 Phase 2 비교 기준으로 변경하지 않는다.

## 검증 결과

- `uv lock` 성공: 51개 패키지 해석.
- 첫 `uv sync --all-groups`는 격리 캐시 파일 권한 오류(os error 5)로 중단됐다. `uv sync --all-groups --no-cache`로 재실행해 개발 의존성을 포함한 환경 설치에 성공했다.
- `uv run --no-cache --no-sync pytest` 최종 결과: 10 passed, 경고 2건. 경고는 Starlette TestClient가 사용하는 anyio 별칭의 deprecation 경고와 `.pytest_cache` 쓰기 권한 경고다.
- 실제 Uvicorn 실행: `GET /`가 200을 반환하고 질문 입력 UI를 제공하는 것을 확인했다.
- 실제 Uvicorn 실행: OpenAI 설정 없는 `POST /api/analyze`가 503을 반환하는 것을 확인했다.

첫 API 요청은 PowerShell의 JSON 인자 인코딩 문제로 잘못된 본문을 전송했고, 앱은 예상대로 422를 반환했다. 호환되는 요청 방식으로 본문을 다시 전송해 위 503 결과를 확인했다.

첫 pytest 실행은 의존성 설치가 완료되기 전 `openai.AsyncOpenAI` import 오류로 수집에 실패했다. 설치 완료 후 동일 검증을 다시 실행했으며 최종 결과는 위와 같다.

## 모델 평가 결과

`src/spendguard/agent.py`의 `load_project_env()`는 프로젝트 루트의 `.env`에서 설정되지 않은 환경 변수를 읽는다. `OpenAIAnalyzer`가 Agent 생성 시 이 함수를 호출하므로 애플리케이션과 `scripts/evaluate_phase1.py` 모두 동일한 `.env` 설정을 사용한다. `.env`의 실제 값은 열람하거나 기록하지 않았다.

`uv run --no-cache --no-sync python scripts/evaluate_phase1.py`로 고정 평가 데이터 17건을 실제 OpenAI baseline에 실행했다.

- 사용 모델: `OPENAI_MODEL`에 설정된 모델 (값 비공개)
- 평가 케이스: 17건
- Intent 정답: 16건
- Intent 정확도: 94.12% (16/17)
- 실패 케이스: `ambiguous-001` — expected_intent `unknown`, actual_intent `budget_optimization`
- API 오류: 없음
- 전체 평가 성공 여부: 성공 (`evaluation_success: true`)

## 핵심 baseline
| 항목        |            Phase 1 결과 |
| --------- | --------------------: |
| 평가 케이스    |                    17 |
| Intent 정답 |                    16 |
| 정확도       |                94.12% |
| 실패        |       `ambiguous-001` |
| Expected  |             `unknown` |
| Actual    | `budget_optimization` |
| API 오류    |                     0 |
| 테스트       |           `10 passed` |
