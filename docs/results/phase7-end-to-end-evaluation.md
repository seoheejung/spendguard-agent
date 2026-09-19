# Phase 7 End-to-End Evaluation 결과

## 고정 평가 데이터

- Dataset: `evals/phase7_end_to_end_v1.json`
- Version: `phase7-v1`
- Freeze date: 2026-09-19, 첫 평가 실행 전에 expected Pack, status, required-data fields, 계산 결과, API 오류 응답을 고정했다.
- 총 21 cases: 재현 가능한 Decision Pack workflow 20건과 Web Search 오류 API 1건이다.
- 기존 `evals/phase1_cases.json` 17건은 변경하지 않았다. 특히 `ambiguous-001`의 `expected_intent`는 계속 `unknown`이다.

고정 workflow case에는 Purchase, Recurring Cost, Finance Cost(할부/대환), Ownership Cost, Quote Audit, Budget Optimization, unknown, 모호한 질문, 각 Pack의 필수 입력 부족, 검색 필요/불필요, 계산 필요/불필요, 검색 결과 없음, MCP 오류를 포함한다. Web Search 오류 case는 고정 fixture를 사용하는 API 테스트에서 `502`를 기대값으로 검증한다.

## 재현 가능한 로컬 평가 결과

실행 명령: `uv run --no-cache --no-sync python scripts/evaluate_phase7.py`

이 평가는 Agent의 structured output을 고정 fixture로 제공하고 기존 Decision Pack 및 실제 stdio MCP Client를 실행한다. 따라서 아래 Routing Accuracy는 OpenAI 자연어 모델의 추론 정확도가 아니라 **검증된 structured intent 이후의 code-owned Pack routing 정확도**다. 로컬 평가에는 OpenAI, Jev, 실제 Web Search 호출이 없다.

| 지표 | 실제 결과 | 분모 / 범위 |
| --- | --- | --- |
| Routing Accuracy | 100% | 20 / 20 workflow cases |
| Calculation Accuracy | 100% | 9 / 9 계산 case, 고정 expected 및 Direct/MCP 일치 |
| Required Data Accuracy | 100% | 20 / 20, 6개 Pack의 누락 입력 포함 |
| Source Coverage | 100% | source trace가 필요한 fixture 1 / 1 |
| Unsupported Fact | 0건 | 결과 source의 value/name/URL/retrieved_at 누락 및 facts 혼입 검사 |
| Tool Error Handling | 100% | MCP 오류 1 / 1이 `tool_error`로 처리 |
| End-to-End Success | 100% | 20 / 20 expected Pack, status, schema, 근거 규칙 충족 |

9개 계산 case는 기존 6개 Tool을 모두 사용했다. 각 MCP 결과의 `inputs`, `formula`, `intermediate`, `result`가 Phase 3 direct calculation과 일치하는지 확인했다. 계산 정확도는 9 / 9이며, Phase 4 MCP 독립 테스트의 6개 Tool direct/MCP 비교도 기존 회귀 테스트로 유지된다.

로컬 측정의 전체 latency는 15,549.17ms였다. stdio MCP를 실제 호출한 9개 정상 계산 case는 약 1,684.73~1,926.56ms/case였고, 계산을 실행하지 않는 Pack/fallback은 0.01~0.03ms 수준이었다. 이 값은 로컬 프로세스 시작 비용을 포함하므로 외부 모델 latency와 직접 비교하지 않는다.

로컬 호출 수는 Jev 0, OpenAI 0, Web Search 0, MCP 10회다. MCP 10회에는 정상 calculation 9회와 의도적으로 실패시킨 오류 case 1회가 포함된다. 로컬 평가에는 model-provider usage나 비용이 없으므로 둘 다 기록 가능한 값이 없다.

## 실제 OpenAI Web Search + MCP 검증

실행 명령: `uv run --no-cache --no-sync python scripts/evaluate_phase7_external.py`

2026-09-19에 `Apple iPhone current Korea sale price from official source`를 1회 실행했다. 결과는 `research.status=completed`, `official_source_confirmed=true`, Purchase Pack `ready`였다. 현재 가격 값은 결과 문서에 기록하지 않았다.

- source trace: `apple.com`, `https://www.apple.com/kr/shop/buy-iphone`, `retrieved_at=2026-09-19T14:20:32.797987+00:00`
- 4개 external fact 모두 위 공식 URL과 같은 retrieved_at를 포함했다. 외부 사실은 Decision result의 `sources`에만 존재하며 facts와 분리됐다.
- OpenAI Agent + Web Search latency: 7,562.14ms
- Decision Pack + stdio MCP latency: 2,092.43ms
- Total latency: 9,654.57ms
- 호출 수: Jev 0, OpenAI Agent 1, Web Search query 1, MCP 1 (`compare_costs`)

현재 `AnalysisResult` 경계는 Web Search tool-call 정확한 횟수와 OpenAI usage를 노출하지 않는다. 따라서 Web Search tool-call count는 확인 불가, usage는 확인 불가, 비용은 계산하지 않음으로 기록한다. 추정값을 사용하지 않았다.

## 오류·fallback·출처 검증

- `web-search-error-001`: `ResearchExecutionError`를 주입한 실제 Decision API 경로가 고정 expected대로 HTTP 502와 안전한 메시지를 반환했다.
- `research-no-results-001`: source 없는 `no_results`는 확정 external fact 없이 결과의 risk로 남는다.
- `mcp-error-001`: 계산 evidence 없이 `tool_error`를 반환하며 확정 결론이나 계산값을 생성하지 않는다.
- source trace fixture는 value, source_name, source_url, retrieved_at를 모두 확인하고 external fact가 `facts`에 섞이지 않음을 검증한다. 실제 외부 호출도 위 URL과 retrieved_at를 별도로 확인했다.

## Jev / OpenAI routing 구분

Phase 2 Jev 고정 17-case 평가는 16 / 17 (94.12%)이었다. 실패한 `ambiguous-001`은 expected `unknown`에 대해 `budget_optimization`, confidence 0.99로 오분류됐다. 이는 vendor benchmark가 아닌 2026-09-19 프로젝트 실측이며, Phase 7 local workflow에서는 Jev를 호출하거나 confidence로 routing하지 않는다.

Phase 7의 `ambiguous-001`은 고정 `unknown` structured output으로 Pack을 실행하지 않고 `needs_input` fallback을 반환했다. 따라서 high-confidence 오분류를 production에서 보정하거나 숨기지 않았고, Phase 2 결과와 Phase 7 code-routing 결과를 같은 정확도 지표로 합산하지 않았다. OpenAI의 기존 17-case baseline도 16 / 17 (94.12%)의 과거 실측이며, 이번 고정 workflow metric과 직접 비교하지 않는다.

## UI 및 기존 회귀

Phase 7에서 UI나 production 기능은 변경하지 않았다. UI contract는 Decision Workspace form/result, Researching 상태, Sources의 URL/retrieved_at, keyboard skip link를 재검증했다. 기존 Phase 1~6 테스트도 그대로 실행한다.

## 제한 및 후속 확인 항목

- 고정 local routing 결과는 OpenAI 모델 품질 수치가 아니다. OpenAI inference의 새 benchmark가 필요하면 별도 versioned dataset과 동일 환경의 반복 실행을 먼저 승인·기록해야 한다.
- 현재 Agent SDK 결과 경계에서 usage와 정확한 Web Search tool-call count가 확인되지 않아 비용을 추정하지 않았다.
- 위 제한은 최소 품질 기준(Calculation Accuracy 100%, Unsupported Fact 0건, 미처리 Tool 오류 0건, source trace, 재현 가능 결과, 기존 테스트 회귀 없음)을 충족하지 못한 항목이 아니라 측정 불가 항목이다.
