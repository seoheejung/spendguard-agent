# Phase 2 Jev Decision Layer Evaluation 결과

## 범위

- TypeSafe Jev `Choice` 기반 7개 Intent 분류
- 고정 평가 데이터 `evals/phase1_cases.json` 17건
- production routing, confidence threshold, MCP, Calculation Tool, Web Search 미구현

## SDK와 모델

| 항목 | 값 |
| --- | --- |
| TypeSafe SDK | `typesafe-sdk` 0.7.0 |
| Jev 모델 | `jev-latest` |
| 인증 | `TYPESAFE_API_KEY` 환경 변수 |
| 공식 SDK 확인일 | 2026-09-19 |

공식 Python SDK의 `TypeSafeClient.system_one()`과 `Choice` 사용. 응답 `choice`, `confidence`, `probabilities`, usage 수집.

## 실제 평가 결과

| 항목 | 결과 |
| --- | --- |
| 평가 케이스 | 17 |
| Intent 정답 | 16 |
| Intent 정확도 | 94.12% (16/17) |
| 평균 지연 시간 | 259.25ms |
| p50 지연 시간 | 238.50ms |
| 전체 실행 시간 | 4,407.82ms |
| API 오류 | 0 |
| 전체 평가 성공 | 성공 |

### 실패 케이스

| ID | expected_intent | actual_intent | 지연 시간 | confidence |
| --- | --- | --- | --- | --- |
| `ambiguous-001` | `unknown` | `budget_optimization` | 208.54ms | 0.99 |

## Usage와 비용

| 항목 | 실제 값 |
| --- | --- |
| Input tokens | 8,981 |
| Output tokens | 1,319 |
| Total tokens | 10,300 |
| Requests | 17 |
| Usage 완전성 | 17건 전체 수집 |
| 계산 기준 비용 | $0.000377202 |
| Dashboard 표시 비용 | $0.0004 |
| Output token 비용 | 무료 |

Jev input 가격: $0.042 / 1M tokens. Output token 가격: 무료.

`8,981 / 1,000,000 × $0.042 = $0.000377202` 계산 기준 비용. TypeSafe Dashboard Spend `$0.0004` 표시값과 일치.

공식 출처: [TypeSafe AI](https://typesafe.ai/), [Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev).

## Phase 1 OpenAI baseline 비교

| 항목 | OpenAI baseline | Jev |
| --- | --- | --- |
| Cases | 17 | 17 |
| Correct | 16 | 16 |
| Accuracy | 94.12% | 94.12% |
| Failed | `ambiguous-001` | `ambiguous-001` |
| API Errors | 0 | 0 |
| Mean Latency | 미측정 | 259.25ms |
| p50 Latency | 미측정 | 238.50ms |
| Usage | 미측정 | Input 8,981 / Output 1,319 |
| Cost | 미확인 | 계산 기준 $0.000377202 / Dashboard $0.0004 |

동일 17개 고정 케이스 기준 정확도와 API 오류 비교 가능. Phase 1 지연 시간, usage, 비용 미수집 상태에 따른 해당 항목 직접 비교 불가.

## 후속 적용 판단

- Jev Intent `Choice` 평가 완료
- Phase 1 baseline과 동등한 Intent 정확도 확인
- Jev production routing 미적용
- confidence threshold 미설정
- Noul, Score 실험 미수행

## 검증

- `uv run --no-cache --no-sync pytest`: 16 passed
- `uv lock --check`: 성공
- `git diff --check`: 성공
