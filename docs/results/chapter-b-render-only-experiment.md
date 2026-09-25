# Render-only Codex experiment

Date: 2026-09-26. Scope: one AirPods purchase question and one cashflow follow-up. This is an experimental runner, not the production FastAPI decision endpoint. The earlier A numbers are from the completed browser verification on 2026-09-25; its exact prompt matches this experiment's question, but its Codex model-turn count was not recorded. A later A attempt completed, but the experiment harness discarded its metrics after a Decimal parsing error before B began; it is excluded from the comparison.

## Path and evidence boundary

A used FastAPI → Codex agent → Search / MCP / Jev → answer. B used server-side evidence preparation → existing calculation MCP → minimum-input Jev bundle → code composition → one isolated Codex rendering turn. The renderer ran from a temporary workspace with user configuration ignored, web search disabled, no MCP server, shell/apps/hooks disabled, and `approval_policy=never`. Its event stream had one model turn and no tool calls. The renderer only returned `answer` and `suggested_followups`; source metadata remained with the prepared bundle.

B did **not** implement a general server Search provider. Public Google HTML and Bing RSS probes did not surface the known official Apple page reliably. The controlled experiment fetched two previously known Apple URLs instead. Therefore B has 0 search-engine queries and 2 direct web-source fetches, while A used 2 Codex Search actions. The answers use the same Apple launch price evidence, but the whole-request latency values are not a strict like-for-like Search comparison. Neither path confirmed current checkout prices.

## Measured results

| Flow | Total | Codex subprocess / outside-tool time | First visible Codex event | Search | Direct source fetches | Calculation MCP | Jev requests / new judgments / reused | Codex model turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A first, prior browser result | 57.925 s | 49.129 s outside Search/MCP; subprocess duration unavailable | 2.948 s | 2 | 0 | 1 | 1 / 6 / 0 | unavailable |
| B first, final render-only run | 16.762 s | 11.687 s subprocess | 1.463 s | 0 | 2 | 1 | 1 / 6 / 0 | 1 |
| A follow-up, prior browser result | 14.646 s | 14.036 s outside Search/MCP; subprocess duration unavailable | 4.340 s | 0 | 0 | 0 | 1 / 4 / 4 | unavailable |
| B follow-up, final render-only run | 8.563 s | 8.063 s subprocess | 0.507 s | 0 | 0 | 0 | 1 / 4 / 4 | 1 |

B first-stage breakdown: direct web-source fetches 1.035 s, calculation MCP 3.306 s, Jev/code state step 0.724 s, Codex 11.687 s. The two first-request total times differ by 41.163 s, but this includes the Search-path difference. The follow-up total improved by 6.083 s on the same stored facts. Its 8.063 s Codex renderer still missed the proposed 3–7 s follow-up target; this experiment does not justify claiming the CLI is fast enough for all serving requests.

## Answer quality

- B first answer recommended waiting until the travel budget and current seller prices are known. It displayed Apple’s 2024 launch prices of 199,000 KRW and 269,000 KRW, the MCP-verified 70,000 KRW difference, the ANC feature difference, and the Apple source link. The answer explicitly said these were not current checkout prices. It generated two contextual follow-up questions outside the answer body.
- B follow-up reused the price/source facts and four Jev judgments. The four affected cashflow judgments were recomputed. The answer recommended waiting and correctly stated 430,000 + 130,000 − 600,000 = −40,000 KRW. It made no Search or MCP call.
- An earlier B run finished in 12.316 s but omitted a clear buy/wait conclusion because Jev returned an unknown purchase choice. Code composition now defers a purchase when the existing product works and affordability inputs are absent; the final B result above is after that fix. This was a quality correction, not a latency optimization.

## Verification and limits

- `.\.venv\Scripts\python.exe -m pytest tests/test_decision_state.py tests/test_codex_runtime.py tests/test_mcp.py tests/test_calculations.py -q -p no:cacheprovider`: 34 passed, one existing FastMCP regex warning.
- `.\.venv\Scripts\python.exe -m py_compile scripts/render_only_experiment.py src/spendguard/codex_runtime.py src/spendguard/decision_state.py`: passed.
- Final run data: `docs/results/chapter-b-render-only-observation.json`. No 15-scenario benchmark was run.
- The experiment requires a dependable server-side Search provider before it can replace the live product path. No further prompt tuning or serving architecture change was attempted after the final measurement.
