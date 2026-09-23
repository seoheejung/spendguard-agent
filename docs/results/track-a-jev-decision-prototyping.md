# Track A. Jev Decision Prototyping & Optimization

## Scope and isolation

- Added an experimental-only entry point in `scripts/evaluate_track_a.py` and `scripts/evaluate_track_a_workflow.py`.
- The production API, production Agent workflow, Decision Pack rules, calculations, MCP, Web Search integration, and user-facing UI were not changed by this Track A implementation.
- The workflow comparison reuses `OpenAIAnalyzer` and `build_decision_pack`; it records Jev advice separately. The existing code rule still decides whether Web Search is enabled.
- Phase 0–7 result documents and evaluation fixtures remain unchanged. Track A fixtures are `evals/track_a_cases.json` and `evals/track_a_workflow_cases.json`.
- Frozen SHA-256: judgment fixture `d711144f2972c2eb202eb0bc71d0d77bdd426dc9c74cf93fdc817cdeea8794f9`; workflow fixture `e66ed149212b366aa80ecb4fa64ba8cbe856001b3146621b2f64f7020a003613`.
- All provider inputs were synthetic examples. JSONL logs store case IDs and decision metadata only; they do not store prompts, source text, credentials, or financial details.

## Typed judgments and safety

Three yes/no judgments use TypeSafe `Noul`: additional information, current information search, and decision result review. Search result relevance uses `Choice` with `relevant`, `not_relevant`, and `unknown`. Each call asks exactly one independent question. The official Python SDK and primitive references are [TypeSafe Python SDK](https://docs.typesafe.ai/sdk/python.md), [Noul](https://docs.typesafe.ai/primitives/noul.md), [Choice](https://docs.typesafe.ai/primitives/choice.md), and [confidence guidance](https://docs.typesafe.ai/confidence.md); the installed SDK signatures and answer models were also inspected before implementation.

`Noul` returns a probability of yes, not a separate confidence value. An exact 0.5 result maps to `needs_review`; SDK or response failures also map to an abstention. The `Choice` has an explicit `unknown` option. Three judgments are L2 and relevance is L1: relevance can filter a result in the experimental path, while unknown routes to Agent review. Confidence never authorizes an action. No confidence threshold was added. Monetary actions, purchases, contracts, cancellations, and other high-impact actions remain outside Jev authority.

Decision records include judgment ID/type, result, score or confidence, abstain flag, latency, token usage, calculated input cost, automation level, selected path, and—on E2E records—final workflow success. The sanitized records are in `track-a-jev-decisions.jsonl`; the E2E aggregate is in `track-a-workflow-evaluation.json`.

## Isolated judgment evaluation

First live evaluation of `track-a-v1` ran on 2026-09-23: 12 cases, 3 per judgment, fixture hash above. TypeSafe reported 4,881 input and 341 output tokens over 12 calls. Published input pricing is $0.042 per million tokens and output is free, for $0.000205002 total ([TypeSafe Jev announcement](https://typesafe.ai/blog/introducing-system-one-models-and-jev), checked 2026-09-23).

| Judgment | Correct | Accuracy | FP / FN | Abstain | Mean latency |
| --- | ---: | ---: | ---: | ---: | ---: |
| Additional information | 3/3 | 100% | 0 / 0 | 0% | 458.71 ms |
| Current information search | 3/3 | 100% | 0 / 0 | 0% | 293.41 ms |
| Search result relevance | 2/3 | 66.67% | 0 / 0 | 0% | 264.90 ms |
| Decision result review | 3/3 | 100% | 0 / 0 | 0% | 259.47 ms |

The relevance error was the deliberately ambiguous forum result: expected `unknown`, returned `not_relevant` with confidence 0.73. The Choice abstain rate was zero. Across the nine Noul examples, the observed Brier score was 0.0146; that small sample is descriptive and does not establish calibration. The isolated sample is too small to establish production quality.

For current-information search, the existing Code rule matched 2/3 isolated labels: it requested a search for “prices I pasted” even though the user had supplied those prices (one false positive). Jev matched 3/3 isolated labels. On the three E2E inputs, Code matched all 3 expected search decisions while Jev said search was needed for the missing-laptop-details request (one false positive). This split supports keeping the existing Code-owned production decision for now and treating phrasing around user-supplied current values as a future rule-evaluation case; it does not justify routing production through Jev.

## Baseline and experimental E2E comparison

The frozen `track-a-workflow-v1` fixture ran on 2026-09-23 with OpenAI model `gpt-5.6-luna`. Baseline calls the existing workflow once per case. The experimental path obtains the two intake judgments, calls the same Agent and Decision Pack workflow, filters only explicitly `not_relevant` sources, and sends the judgment/result bundle to the Agent for L2 review. No production route consumes these results.

| Metric | Production baseline | Jev experimental |
| --- | ---: | ---: |
| End-to-end success | 2/3 | 2/3 |
| Agent calls | 3 | 6 |
| Agent input / output tokens | 22,466 / 1,734 | 38,997 / 4,134 |
| Jev calls | 0 | 9 |
| Jev input / output tokens | 0 / 0 | 3,809 / 198 |
| Agent latency | 27.81 s | 58.48 s |
| End-to-end latency | 27.82 s | 62.27 s |
| Source Coverage | 0/1 | 0/1 |
| Unsupported Fact | 0 | 0 |
| OpenAI model + Web Search cost | $0.006594 | $0.0127902 |
| Jev cost | $0 | $0.000159978 |
| Total measured provider cost | $0.006594 | $0.012950178 |

The optimized Code candidate is the existing production path: skip Jev for Code-owned required-field/search checks and retain the current Agent handling for unresolved semantic or evidence review. It is behaviorally identical to baseline, so its measured E2E metrics are the baseline row above (3 Agent calls, 22,466/1,734 tokens, 27.82 s, 0/1 Source Coverage, $0.006594); it was not run as a separate provider pass. This candidate removes Jev calls without claiming Agent-call or latency savings.

Both paths missed the source-required case because Web Search returned no source that passed the existing citation/source normalization. The two other cases succeeded. Model token pricing used the [official GPT-5.6 Luna page](https://developers.openai.com/api/docs/models/gpt-5.6-luna); Web Search calls used the [official pricing page](https://developers.openai.com/api/docs/pricing). Costs include model tokens and Web Search calls; no other provider charge was observed. This is one small, variable live run, not a quality or cost guarantee.

## Execution-layer decisions

| Judgment | Track A placement | Evidence and next step |
| --- | --- | --- |
| Additional information | Code for known required fields; Jev remains an L2 research candidate for genuinely semantic gaps | Jev scored 3/3 on three synthetic cases, but the existing Decision Pack already checks required fields deterministically. Do not spend a Jev call on those code-owned checks. Collect more cases for ambiguous context. |
| Current information search | Code, provisionally | E2E Code matched 3/3 expected decisions; Jev matched 2/3. Code did get one isolated false positive for user-supplied pasted prices. Keep the existing production route and collect more such cases before changing the rule or moving this judgment. |
| Search result relevance | OpenAI Agent review for now; Jev L1 filter remains a candidate | 2/3, with the unknown case forced into `not_relevant` and no abstention. The workflow E2E returned no citable sources, so live relevance coverage could not be evaluated. |
| Decision result review | OpenAI Agent | The isolated set scored 3/3, but the E2E experiment made all three cases request Agent review, including a ready deterministic calculation. That added calls and cost without improving the 2/3 end-to-end success. |

No classifier training or distillation was performed. These results support reducing Jev usage on deterministic gates and gathering a broader, fixed relevance/review dataset before considering any automatic routing.

## Verification performed

- `uv --cache-dir .uv-cache run --no-sync pytest tests/test_track_a_prototype.py tests/test_jev.py tests/test_evals.py`: 11 passed.
- `uv --cache-dir .uv-cache run --no-sync python scripts/evaluate_track_a.py`: 12 live Jev calls; 0 provider errors.
- `uv --cache-dir .uv-cache run --no-sync python scripts/evaluate_track_a_workflow.py`: 3 paired baseline/experimental cases; both paths completed with 2/3 expected outcomes.
- `uv --cache-dir .uv-cache run --no-sync pytest --basetemp=.tmp-pytest-track-a-20260923`: 100 passed. This includes the existing workspace UI contract and Phase 7 UI regression tests.
- `uv --cache-dir .uv-cache lock --check`: passed; no dependency or lockfile change.
- The browser-flow script was not run because its local app (`127.0.0.1:8000`) and Chrome DevTools endpoint (`127.0.0.1:9444`) were not running. UI verification is limited to the 5 automated workspace UI tests in the full suite.
- `git diff --check`: final result recorded after documentation and staged-file review.
