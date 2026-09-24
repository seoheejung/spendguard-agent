# Chapter B. Decision Answer Reconstruction

> 중단된 설계 기록입니다. 현재 작업 지시가 아닙니다. 후속 제품 작업은
> [Chapter B. 15 Scenario Validation](chapter-b-15-scenario-validation.md)과
> `.project/plan.md`의 현재 우선순위를 따릅니다. 이 문서에 따라 미커밋 구현을
> 계속하거나 완료 처리하지 않습니다.

> Preserve Phase 0–7 and Track A; reassemble their existing capabilities around complete, scenario-specific answers to consumer decision questions.

## 1. Purpose and boundary

The product accepts one natural-language question, performs necessary search and/or calculation inside the workflow, and returns one user-facing answer. This is a product-layer reconstruction, not a new business capability.

Preserve without editing their implementation, results, or evaluation data:

- Phase 0–7 code, completion results, and fixtures
- Track A code, result documents, logs, and evaluation fixtures
- existing Web Search, MCP, calculation, and side-effect policies
- the 15 established consumer scenarios and their intent

Decision Packs remain internal context and policy. They must not impose a generic staged user workflow or force every answer into one scenario-insensitive structure. Do not add Jev routing, learned classifiers, new calculations, new external services, or automatic purchase, cancellation, contract, or payment actions.

## 2. Approved architecture

```text
Natural-language question (+ prior answer only when a blocking field was requested)
  → one Decision Agent orchestration run
      ↔ existing Web Search when current external information is required
      ↔ existing MCP calculation tools when deterministic calculation is required
  → Code validates tool policy, side-effect boundary, and typed answer schema
  → scenario-specific DecisionAnswer
  → user-facing result
```

“One Decision Agent” means one orchestration run per user request. It does not require exactly one LLM API turn: model turns required for tool calling are allowed. Do not retain a separate sequential intake Agent run followed by a Research Agent run. Do not create 15 independent workflow implementations: keep search, calculation, validation, and error handling in shared orchestration; express scenario differences through typed `scenario_result` payloads and their renderers.

The orchestration owns tool selection within code-owned allowlists and existing safety rules. Reuse existing Search and MCP implementations. Search evidence must inform the scenario result and conclusion, not merely populate Sources. MCP outputs must inform Key Numbers and the scenario result, not remain only in technical traces.

## 3. Answer contract and rendering

The response has a shared answer envelope and a scenario-discriminated, typed `scenario_result`. Do not require a generic `comparison` field: comparison structures belong inside the relevant scenario payload and may differ in shape.

First-screen information order:

1. `Conclusion`: an actual comparison outcome or the strongest judgment supported by current evidence; never a restatement of the request.
2. `Key Numbers`: real retrieved or deterministically calculated numbers, with units and traceable source/calculation references.
3. Scenario-specific comparison.
4. `Why`: the decisive evidence and conditions.
5. `Risks / Uncertainty`: only unresolved or unverified facts.
6. `Sources`: sources actually used by the answer.

Facts, assumptions, calculation breakdowns, and technical details remain available under a collapsed details section. Do not expose English internal diagnostics, raw verification messages, generic next actions, internal field IDs, Pack names, tool names, or raw JSON in the user result. Map recoverable errors to concise Korean user messages; preserve diagnostic detail only in safe internal logs.

Forbidden conclusion patterns include equivalents of:

- “을 비교하려는 요청입니다.”
- “을 확인하려는 요청입니다.”
- generic fact-review instructions or source-conflict diagnostics

When credible current prices disagree, describe the supported range and the disagreement in user language rather than inventing a single authoritative value.

## 4. Blocking input policy

Return `needs_input` only when a missing value makes the requested analysis itself or a necessary tool call impossible. Optional information gaps must not block an otherwise useful answer. Prefer a clearly labeled assumption or uncertainty when analysis can proceed safely. Never ask again for a value already supplied in the question or prior user response, and never promote an inferred value to a user-provided fact.

No research or calculation should be fabricated to work around a true blocker. A blocking response asks only for the minimum necessary values and contains no unsupported result claims.

## 5. Scenario result shapes and populated golden questions

Use the existing 15 scenario intents, not 15 separate workflows. The shapes below define user-visible scenario payloads and deterministic QA inputs. Values are synthetic test inputs; they are not claims about current market facts. Search-derived fields in fixtures must carry source references.

| # | Scenario | Populated golden question | `scenario_result` shape |
|---|---|---|---|
| 1 | 최저가 비교 | “갤럭시 버즈3 프로를 사려고 해. 삼성 공식몰은 289,000원이고 배송비는 무료야. 오늘 살 수 있는 같은 제품 판매처 가격과 보증 조건을 찾아 가장 싼 선택지를 비교해줘.” | product; seller offers (item price, shipping, total, warranty, source refs); cheapest verified offer; delta from supplied offer; unavailable conditions |
| 2 | 구독료 다이어트 | “넷플릭스 17,000원, 디즈니+ 13,900원, 웨이브 10,900원을 매달 내고 있어. 넷플릭스는 매일, 디즈니+는 주 1회, 웨이브는 한 달에 한 번 써. 월·연 지출과 하나를 해지할 때 절약액을 비교해줘.” | subscriptions (monthly cost, use frequency, overlap evidence); monthly/annual total; per-service cancellation savings; retained-service scenarios |
| 3 | 통신비 점검 | “현재 5G 요금제에 월 69,000원을 내고 데이터는 평균 18GB 써. 통화는 월 300분 정도야. 한국에서 현재 가입 가능한 요금제와 월 비용을 비교해줘.” | current plan/use; researched candidate plans (price, data, call terms, eligibility, sources); monthly/annual deltas; fit caveats |
| 4 | 보험 중복 찾기 | “실손보험 월 24,000원, 암 진단비 보험 월 38,000원, 종합보험 월 71,000원을 내고 있어. 종합보험에도 암 진단비 2,000만원과 입원비가 포함돼 있어. 보험료 합계와 겹치는 보장을 찾아줘.” | policies (premium, user-provided coverage); duplicate/related coverage pairs; monthly/annual premium total; verification needs. Advisory only; no cancellation action |
| 5 | 카드 혜택 최적화 | “지난달 식비 520,000원, 교통 85,000원, 온라인 쇼핑 240,000원, 통신비 69,000원을 썼어. 연회비 20,000원 이하 카드의 현재 공개 혜택을 찾아 내 소비 기준 연간 순혜택을 비교해줘.” | spending categories; cards (eligible benefit, caps, conditions, annual fee, source refs); gross and net estimated annual benefit; unmet eligibility assumptions |
| 6 | 충동구매 방지 | “무선 헤드폰을 329,000원에 살까 고민 중이야. 주 4회, 한 번에 2시간씩 최소 3년 쓸 생각이고 지금은 유선 이어폰이 있어. 구매가와 사용시간당 비용을 계산하고 지금 사는 것과 한 달 기다리는 선택을 비교해줘.” | buy-now vs wait/keep-current options; supplied price; use hours and cost per hour; wait-price uncertainty explicitly marked (no invented forecast) |
| 7 | 장보기 예산 절감 | “성인 2명이 일주일 동안 먹을 장보기 예산은 120,000원이야. 집에 쌀 2kg, 식용유, 간장, 달걀이 6개 있어. 이번 주 장보기 목록과 식단을 구성하고 합계가 예산에서 얼마나 남는지 현재 가격으로 계산해줘.” | meals; shopping items (quantity, current unit/line price, source refs); excluded pantry items; basket total; remaining budget |
| 8 | 여행비 최적화 | “성인 2명이 2026년 11월 12일부터 15일까지 서울에서 부산으로 3박 여행을 가. 교통·숙박 예산은 700,000원이고 KTX와 시외버스, 1박 150,000원 이하 숙소를 포함해 현재 예약 가능한 조합을 비교해줘.” | dated transport/lodging options (availability, terms, source refs); component and trip totals; budget delta; freshness/availability caveats |
| 9 | 자동차 유지비 계산 | “2021년식 아반떼 1.6 가솔린을 앞으로 5년 보유할 거야. 연간 주행거리 12,000km, 연비 14km/L, 휘발유 1,700원/L, 보험료 연 900,000원, 자동차세 연 290,000원, 정비비 연 600,000원, 예상 감가 5년 8,000,000원으로 총 소유비를 계산해줘.” | 5-year cost breakdown (fuel, insurance, tax, maintenance, depreciation); total TCO; monthly average; input assumptions |
| 10 | 할부 vs 일시불 | “1,200,000원 제품을 연 8%로 12개월 원리금균등 할부하려고 해. 수수료는 0원이고 일시불 할인은 5%야. 할부 총액과 일시불 총액, 차이를 계산해줘.” | cash price after discount; installment payment/total; fee; total delta; calculation trace reference |
| 11 | 대출 갈아타기 계산 | “대출 잔액은 20,000,000원, 현재 금리는 연 6.2%, 남은 기간은 36개월이야. 새 대출은 연 4.8%로 36개월이고 중도상환·취급 수수료 합계가 300,000원이야. 갈아탈 때 총이자와 수수료를 반영한 절감액을 계산해줘.” | current/new interest totals; fees; net savings; payment comparison; calculation assumptions/trace reference |
| 12 | 견적서 바가지 체크 | “에어컨 2대 설치 견적이 실내기·실외기 2,400,000원, 배관 18m 720,000원, 타공 2회 160,000원, 설치비 350,000원, 총 3,630,000원이야. 각 항목의 현재 공개 가격 범위와 비교해 차이를 알려줘.” | supplied quote line items and checked sum; researched comparable ranges with conditions/source refs; item deltas; incomparable/missing scope |
| 13 | 가격 협상 준비 | “사무실 복합기 3년 임대 견적을 월 89,000원, 설치비 180,000원, 기본 인쇄 월 2,000매로 받았어. 같은 출력량과 기간의 공개 요금 조건을 찾아 총액 차이와 협상할 항목을 정리해줘.” | 36-month quote total; researched comparable offers with print allowance/fees/source refs; comparable delta; negotiable terms and evidence-linked wording |
| 14 | 연간 새는 돈 찾기 | “최근 3개월 지출은 음악 구독 월 10,900원, 클라우드 월 3,300원, 헬스장 월 55,000원, 사용하지 않은 앱 월 6,500원이야. 앱은 세 달 동안 한 번도 안 썼고 나머지는 계속 썼어. 항목별 연간 비용과 앱 해지 절감액을 계산해줘.” | per-item monthly/annual cost; use status; annual total; user-identified reduction candidates; annual savings by candidate |
| 15 | 구매 전 최종 심사 | “맥북 에어 M5 16GB RAM, 512GB SSD 모델을 1,690,000원에 사려고 해. 개발·문서 작업에 하루 6시간 쓰고 최소 4년 사용할 거야. 현재 노트북은 작동하지만 배터리가 2시간 가고, 중고도 괜찮아. 현재 신품·중고 시세와 기다리기·비슷한 대안을 찾아 4개 선택지를 비용 면에서 비교해줘.” | buy now / wait / used / alternative options; researched current prices and condition/terms/source refs; four-year comparable cost where supported; unsupported forecast or condition uncertainty |

Scenario payloads may share small presentation components, but their content contracts remain distinct. Keep raw facts, assumptions, calculation breakdowns, and internal identifiers out of the first-screen shape.

## 6. Pre-implementation failure analysis

Before coding, document and address these failure modes in the implementation and E2E verification:

- The workflow still runs two sequential orchestration runs, or silently runs search before the Decision Agent has established its need.
- A model requests a field already present in the question, or an optional field incorrectly blocks analysis.
- A guessed value is represented as user-provided or passed to Search as a fact.
- A selected scenario payload does not match its discriminant, omits required user-facing data, or falls back to generic text/cards.
- Tool output exists in trace/source storage but does not affect the conclusion, key numbers, or scenario comparison.
- A calculation result is dropped, altered, rounded inconsistently, or attributed to the wrong option.
- Search source references are absent, invalid, stale without a caveat, or disconnected from the displayed comparison value.
- Conflicting seller prices are collapsed into an unsupported single price or described with internal diagnostics.
- MCP/Search errors leak exception text, English diagnostics, tool names, or raw verification messages to the user.
- Empty, malformed, or unknown scenario output is presented as a successful answer instead of a safe localized recoverable error.
- High-impact action is triggered by an answer; no purchase, payment, cancellation, or contract side effect is allowed.
- Synthetic deterministic fixture data is confused with live market data or written as a factual README/result claim.
- Phase 0–7 or Track A fixtures, expected labels, results, or implementation are changed as a side effect.
- The result renderer exposes internal field IDs or leaves Facts / Assumptions / Calculations / Technical Details expanded by default.
- The blocking-input continuation loses the original question/answers or asks the same question again.

## 7. Evaluation design

Keep two independently reported E2E suites:

### Deterministic Regression

- Exercise the application workflow end to end for all 15 populated golden questions.
- Use fixed mock Search and MCP responses; freeze expected answer fields before running the evaluation.
- Verify the applicable expected calculations, source-to-result linkage, scenario discriminant and payload, conclusion quality, Key Numbers, comparison structure, and absence of repeated inputs/internal diagnostics.
- Assert that Search results affect the relevant scenario payload and conclusion/comparison, and MCP outputs affect Key Numbers and the payload.
- Do not update expected answers to improve a score. Keep this evaluation and its output separate from Phase 1–7 and Track A fixtures/results.
- Produce a repeatable evaluation artifact with per-scenario outcome and failure reasons.

### Live Smoke

- Exercise real Web Search only for cases that need current information; use representative scenarios spanning different result shapes.
- Do not pin live prices or availability as expected values.
- Verify successful workflow completion, schema validity, non-empty valid sources when Search is used, source linkage in the user answer, and a usable localized result.
- Record retrieval time and executed case IDs. Clearly separate live observations from deterministic fixture expectations.
- Never include credentials or sensitive user data in logs or artifacts.

Use E2E coverage as the testing mechanism; do not add unit tests. Run the existing full pytest suite without changing protected fixtures. No dependency or lockfile changes without authorization.

## 8. UI and compatibility checks

- One natural-language question flows to a completed answer unless a genuinely blocking field is missing.
- Loading reflects real orchestration/tool phases; do not invent percentage progress.
- The answer appears in the required first-screen order; scenario-specific comparison is prominent.
- Details are collapsed by default.
- Needs-input UI contains only the remaining blocking questions in natural Korean; previously supplied values are absent.
- No English internal diagnostic, raw verification message, field ID, Pack/tool/API name, or generic next-action copy is visible.
- Search and calculation failures use safe Korean messaging and do not masquerade as completed results.
- Preserve the scenario chooser/template behavior and responsive/accessibility behavior except where result-first rendering requires replacing the Inspector-centric result layout.

## 9. Protected regression boundary

- Do not edit Phase 0–7 source behavior, result documents, or existing evaluation fixtures/expected labels.
- Do not edit Track A code, result documents, logs, or evaluation fixtures/expected labels.
- If shared files must change, isolate Chapter B behavior behind the existing/new answer path without rewriting protected phase-specific evaluation behavior.
- Verify protected paths with `git diff` before completion.

## 10. Result document and completion criteria

Write verified outcomes only to `docs/results/chapter-b-decision-answer-reconstruction.md`. Include the architecture actually implemented, all 15 deterministic scenario results, live smoke case IDs/timestamps, source/result linkage, schema/UI checks, actual test commands and outcomes, known failures, and limitations. Update README only with behavior actually verified; do not change Phase 1–7 or Track A result wording.

Completion requires:

- all 15 deterministic E2E golden scenarios pass
- representative real Search live smoke passes without pinning dynamic prices
- all result-shape, blocking-field, source-linkage, MCP-number, UI privacy, and internal-diagnostic checks pass
- full pytest passes without modifying protected fixtures/results
- `uv lock --check`, `git diff --check`, and `git status` are reviewed
- result documentation reflects only observed results

Do not mark complete, commit, or push unless every completion criterion passes. If a required check fails or cannot run, report the specific blocker and leave changes uncommitted/unpushed.
