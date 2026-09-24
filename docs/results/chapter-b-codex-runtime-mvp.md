# Chapter B: Codex 런타임 전환 실측 (2026-09-24)

## 현재 제품 경로

SpendGuard Web → FastAPI `/api/decisions` → ChatGPT 계정으로 로그인된 Codex CLI → 필요한 경우 Codex Search 및 SpendGuard MCP → 단일 사용자 답변. Jev는 평가 요청에서 네 후보 중 하나를 명시할 때만 호출합니다. 기본 UI는 baseline입니다.

`codex.cmd login status`는 기존 ChatGPT 로그인을 확인했고, `codex.cmd doctor`는 인증 방식 `chatgpt`, 저장된 API key 없음, ChatGPT 백엔드 연결을 보고했습니다. 앱은 실행 중 로그인을 시작하지 않습니다. Codex 자식 프로세스에서 `OPENAI_API_KEY`, `OPENAI_MODEL`, `TYPESAFE_API_KEY`를 제거하고 Codex 자체 모델 설정을 따릅니다. 활성 코드에는 OpenAI Platform 직접 호출이나 fallback이 없습니다.

Codex는 임시 작업 디렉터리, 읽기 전용 sandbox, shell/apps/hooks 비활성화, 승인 요청 비활성화 상태에서 실행합니다. 15건 E2E의 시작과 끝에서 저장소 소스·설정·Git 상태 해시가 같았습니다. API는 최종 답변과 관측 가능한 호출 메타데이터만 반환하며 실행 trace는 평가 아티팩트에만 남습니다.

## 실제 기능 확인

- 일반 추론: 구독 질문에 도구 없이 답변.
- Search: 현재 요금제·판매가·항공권·공식 보험 안내 등에서 실제 검색 호출, URL과 조회 날짜가 있는 답변 확인.
- MCP: 할부 120만 원/24개월 무이자 → `calculate_installment` 결과 월 5만 원, 총 120만 원. 실제 브라우저 UI에서도 이 문장이 단일 결과 카드에 표시됨.
- Search + MCP: 서울 지하철 공개 요금 1,550원 × 40회 → 실제 Search와 `calculate_repeated_cost` 호출, 최종 62,000원. 검색 결과가 계산 입력에 사용됨.
- Jev: 네 후보는 지정된 평가 요청에서 각각 한 번 호출. Search 선택, 계산, 전체 분기, 최종 결론은 Jev에 위임하지 않음. 네 판단은 모두 정보 부족을 뜻하는 `unknown`이었고, 최종 답변은 Codex가 작성함. Jev 실패는 관측되지 않았으며 오류 시 API는 실패를 반환합니다(fallback 없음).
- 카드 혜택의 수정 후 재검증은 실제 카드사 출처의 할인율·월 한도·실적·연회비 조건을 비교에 반영했습니다. [신한카드 상품 안내](https://www.shinhancard.com/pconts/html/card/apply/credit/1234575_2207.html)의 배민 5%, 전월 20만 원, 월 한도 3만 원과 [LG전자 설치 안내](https://www.lge.co.kr/story/user-guide/air-conditioners-install-guide)의 공개 설치 조건을 별도로 대조했습니다.

대표 기능 요청의 응답·실측 메타데이터는 [실제 경로 smoke 기록](chapter-b-codex-smoke.json)에 보존했습니다.

## 고정 fixture 전체 평가

`evals/chapter_b_sparse_v1.json`의 질문·criterion·기대 도구 사용 여부는 수정하지 않았습니다. 두 모드 모두 같은 15건을 `/api/decisions`에서 실행했습니다. 최종 답변과 Search 목적, MCP 입력/결과, Jev 판단, latency가 [baseline 원시 기록](chapter-b-codex-baseline-final-raw.json)과 [Jev 원시 기록](chapter-b-codex-jev-final-raw.json)에 있습니다. Criterion별 판단은 [baseline 점수](chapter-b-codex-baseline-final-raw-score.json), [Jev 점수](chapter-b-codex-jev-final-raw-score.json), 각각의 `-reviews.json` 파일에 남겼습니다.

| 관측값 | baseline | Jev |
| --- | ---: | ---: |
| 최종 답변 도달 | 14/15 | 15/15 |
| 고정 criterion 통과 | 8/15 | 10/15 |
| Search 호출 | 15 | 21 |
| MCP 호출 | 15 | 26 |
| Jev 요청 | 0 | 4 |
| Codex 실행 | 15 | 15 |
| E2E 총 시간 | 675.4초 | 758.7초 |
| E2E 중앙값 | 41.8초 | 40.7초 |
| 오류 / timeout / retry | 1 / 0 / 0 | 0 / 0 / 0 |

baseline 자동차 1건은 앞선 실행에서 Codex가 약 120초에 비정상 종료했습니다. 당시 stderr와 사용량 상태가 저장되지 않았으므로 원인은 **unknown**입니다. 이를 재현하거나 timeout을 조정하지 않았습니다. 이후 일반 Jev 15건 평가에서는 자동차 질문이 147.5초에 답변까지 도달했습니다. 두 결과만으로 과거 종료 원인을 추정하지 않습니다. 이후 비정상 종료의 종료 코드와 stderr를 평가 기록에 남기도록 구현했습니다.

주요 실패는 구독의 두 서비스 직접 비교 누락, 카드 혜택의 조사 누락, 일부 계산·검색 호출의 fixture 기대치 불일치, baseline 자동차 오류, 연간 지출 답변의 만족도 불확실성 누락, Jev 최저가 답변의 정확한 차액 누락입니다. 할부·견적·가격 협상에서 도구 사용 기준과 결정론적 계산 원칙이 충돌할 가능성은 현 fixture 기준 실패로 그대로 유지했습니다. fixture는 수정하지 않았습니다.

## 공통 수정 재검증

현재 대안이나 제시받은 금액을 비교할 때 공개 근거를 찾고, 알려진 금액끼리는 실제 차액을 적도록 공통 Codex 지침을 수정했습니다. 특정 도시·제품·카드에 대한 regex나 분기는 추가하지 않았습니다. 수정 후 관련 4건을 각 모드에서 재실행한 [baseline 기록](chapter-b-codex-baseline-common-fix.json)과 [Jev 기록](chapter-b-codex-jev-common-fix.json)을 전체 실행 기록과 별도로 보존했습니다.

수정 후 카드 질문은 baseline Search 4회/MCP 4회, Jev Search 3회/MCP 9회로 답변에 도달했고 공개 혜택과 조건을 제시했습니다. 가격 협상 질문도 두 모드에서 공식 설치 기준을 검색했습니다. 4건 중 criterion 통과는 각각 3건입니다. baseline 가격 협상은 MCP 사용 불일치로, Jev 구독 질문은 서로 다른 서비스 가치의 직접 비교 부족으로 실패했습니다. 이 재검증은 전체 15건 재실행 결과로 합산하지 않았습니다.

Jev 4건의 `unknown` 판단은 sparse 입력에서 근거 부족이라는 좁은 판단으로 수동 검토했습니다(4/4). 별도의 사전 정답 라벨은 없고 모두 `unknown`이므로 판단 정확도 기준 충족이나 실제 분류 대체 이득은 입증되지 않았습니다. Jev 모드는 Codex 실행 횟수를 줄이지 못했고 전체 시간과 도구 호출이 늘었습니다. 네 후보를 기본 제품 경로에 적용하지 않고 평가 모드로 유지합니다. 내부 token, model cost, ChatGPT quota는 측정하거나 추정하지 않았습니다.

## 검증과 제약

- `uv run python scripts/run_chapter_b_runtime.py --mode baseline|jev --output ...`로 실제 15건 실행. 각 아티팩트의 `repository_unchanged`는 `true`.
- `uv run python scripts/evaluate_chapter_b_sparse.py --runtime-results ... --reviews ... --output ...`로 고정 criterion 채점.
- 실제 브라우저에서 질문 제출 → FastAPI → Codex/MCP → 단일 결과 카드 확인. 내부 trace는 표시되지 않음.
- 제품 의존성 목록의 사용하지 않는 `openai-agents` 제거와 `uv.lock` 갱신은 자동 승인 검토가 거부했습니다. 저장소의 lock 파일 갱신 별도 승인 규칙이 이유이며, 해당 패키지는 활성 코드에서 import하지 않습니다. 우회하거나 lock 파일을 변경하지 않았습니다.

과거 Phase/Track A 및 Responses API 결과는 역사적 결과로 남겨두고 현재 런타임 실측으로 해석하지 않습니다.
