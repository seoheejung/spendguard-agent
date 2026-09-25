# SpendGuard runtime, Jev delta, and follow-up verification

Date: 2026-09-25. These are actual browser and local test results. The prior latency numbers are user-provided observations; the exact earlier AirPods prompt was not available in the repository, so latency comparisons are indicative.

## Changes verified

- Fresh and resumed Codex subprocesses use the minimal runtime directory as `cwd`. SpendGuard keeps `gpt-6-luna` and low reasoning.
- One Codex response returns `answer`, up to three `suggested_followups`, and `sources`. The answer body excludes duplicate suggestions; chips fill the input without submitting.
- The read-only Jev MCP tool sends independent allowlisted facts for each Noul, Score, or Choice judgment. It does not write state. FastAPI stores the result in the conversation session.
- For a follow-up with explicitly labeled monetary facts, FastAPI extracts and compares normalized judgment inputs before Codex resumes. The server sends only affected judgments to Jev and passes the result to the same Codex answer turn. Identical normalized inputs need no Jev request or state-check MCP call. Unstructured new facts can still use the read-only tool during Codex execution.
- The API recomputes calculation MCP outputs and checks the derived cash balance against the final answer. Current source links are retained when earlier prices are reused.

## Observed results

| Flow | Total | First visible Codex event | Time outside Search/MCP | Search actions | Calculation MCP | Decision MCP | Jev requests | New judgments | Reused judgments |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Prior first question, user report | 45.2 s | unavailable | unavailable | 1 | 1 | unavailable | unavailable | unavailable | unavailable |
| Prior follow-up, user report | 37.7 s | unavailable | unavailable | 0 | 0 | unavailable | unavailable | unavailable | unavailable |
| Final AirPods first question | 57.925 s | 2.948 s | 49.129 s | 2 | 1 | 1 | 1 | 6 | 0 |
| Final same-session cashflow follow-up | 14.646 s | 4.340 s | 14.036 s | 0 | 0 | 0 | 1 | 4 | 4 |

The first final run had three web tool items, two of which were Search actions. The Jev request completed six judgments on the first turn; two cashflow judgments remained unevaluated because cash facts were missing. The follow-up added `available_cash`, `upcoming_fixed_expense`, and `upcoming_income`. It recomputed `cashflow_harmed`, `purchase_burden_score`, `purchase_choice`, and `key_factor`, and reused `replacement_needed`, `waiting_low_loss`, `replacement_need_score`, and `upgrade_value_score`. Codex resumed the prior thread in one CLI run. Server logs recorded the request, judgment, reuse, recompute, and state-change counts without logging Jev payload values.

The first final answer showed 199,000 KRW and 269,000 KRW, with a 70,000 KRW difference in both prose and table, and matched the Jev `wait` direction. It used Apple's published launch prices, clearly stated that these were not confirmed current checkout prices, and linked the source. This is a quality limit for a question asking for current prices. The follow-up used the prior source, gave the exact `−40,000 KRW` cash balance after 430,000 KRW cash plus 130,000 KRW income minus 600,000 KRW rent, and recommended waiting. Its Search and calculation MCP results were reused. The first answer returned two contextual suggestions, shown only as chips. Clicking a chip filled the input without sending a request.

The final first request was **12.725 s slower** than the user-reported first-request figure; latency improvement is not established for first requests. The final follow-up was **23.054 s faster** than the user-reported follow-up figure, with the caveat that the exact earlier prompt was unavailable. No additional latency architecture was added after this measurement.

## Defects found during verification

- An initial 67.7 s browser attempt used Search 3, calculation MCP 1, and Jev 0. The Jev tool was rejected as a write action under `approval_policy=never`; this attempt is excluded from Jev latency comparison. The tool became read-only evaluation, with FastAPI owning state persistence.
- An intermediate follow-up answered without refreshing Jev after new cash facts. The forced tool-call approach was replaced by server-side comparison of normalized monetary facts.
- Another intermediate answer stated that 430,000 + 130,000 − 600,000 was zero. Code now returns the signed cash balance in the decision composition and checks final balance wording without an additional Codex call.

## Verification scope

- `.\.venv\Scripts\python.exe -m pytest tests/test_decision_state.py tests/test_codex_runtime.py tests/test_mcp.py tests/test_calculations.py -q -p no:cacheprovider`: 33 passed.
- `node --check src/spendguard/static/app.js`: passed.
- Browser: final AirPods first question and one same-session follow-up; answer, source link, suggestions, chip behavior, resume, Jev counters, and computed font sizes checked. Answer body font changed from 15.2 px to 13.6 px; first paragraph from 18.08 px to 16 px.
- The full 15-scenario benchmark was not run.
