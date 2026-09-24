# Chapter B — Decision Answer Reconstruction

> 중단된 미커밋 실험 기록입니다. 새 작업 기준은
> [Chapter B. 15 Scenario Validation](../instructions/chapter-b-15-scenario-validation.md)입니다.
> 아래의 미완료 gate는 새 Chapter B의 완료 기준이 아닙니다.

## Verification status

Chapter B is not complete and is not ready to commit. The deterministic golden cases and local browser flow pass, but the live Search smoke remains unresolved under stricter source-linkage checks, and the full suite retains five legacy UI contract failures. No commit or push was made. README was not changed.

## Implemented scope

- `/api/answers` is a separate experimental answer workflow; `/api/decisions` remains the production path.
- Common orchestration owns Search/MCP calls, validation, source checks, and errors; scenario-specific typed results drive the answer view.
- The answer view prioritizes conclusion, key numbers, scenario result, rationale, uncertainty, and sources; technical detail stays collapsed.
- Fifteen populated deterministic golden cases use fixed Search/MCP responses and check the rendered answer and evidence links.
- Developer-side failure diagnostics record safe stage, exception class, provider status and allowlisted error metadata, request ID when available, Search state, and retry/fallback state. Credentials, raw provider payloads, and user questions are not logged.

## Live Search diagnosis

The first provider failure was HTTP 400 `invalid_json_schema` for `tools`. Isolated requests identified the legacy negative-lookahead decimal pattern in MCP calculation tool schemas as the trigger. The model-facing schema now substitutes an equivalent lookahead-free decimal pattern while the existing runtime validation remains in place. The provider accepted the corrected schema and execution advanced to Search/MCP.

Later Live Smoke runs exposed separate validation failures: generated source references were not always among the exact URLs returned by Web Search, and one run omitted the required comparison calculation. Those answers are rejected instead of being presented as verified. An earlier weak smoke assertion passed, but it did not establish strict linkage for every scenario value and is not treated as completion. The final stricter smoke was interrupted at the user's request to stop paid API calls; no additional paid request will be made in this verification pass. Therefore live Search-to-answer completion remains unverified.

## Browser and test verification

- Deterministic Chapter B golden E2E: 15 cases pass.
- Headless Chrome browser E2E: pass for initial scenario chooser, chooser hiding after request, genuinely blocking input, answer section order, collapsed details, source linkage, no internal diagnostic leakage, mobile overflow, and user cancellation of a stalled local request. Harness diagnostics confirm Chrome launch, remote debugging, `/json/version`, and `/json/list` page target acquisition.
- Phase 7 fixed workflow/evaluation regression: 3 pass. The static `test_phase_seven_workspace_contract_remains_available` fails because it requires the removed `inspector` markup. This is a legacy presentation assertion, not a `/api/decisions` behavior or Phase 7 evaluation fixture; no Phase 0–7 fixture, expected label, or completed result was changed. The Chapter B-added skip was removed; no skip is present in the current test.
- Full pytest (last run): 99 passed, 5 failed. The failures are the Phase 7 static Inspector assertion above and four old `tests/test_workspace_ui.py` assertions for Inspector-era markup/copy. They are not skipped. This remains an unresolved compatibility boundary and prevents completion.
- `git diff --check`: passed in the current verification run.
- `uv lock --check`: passed with a workspace-local cache after the global uv cache path was access-denied.
- No README change, commit, or push.

## Remaining completion gates

1. Resolve or explicitly reconcile the legacy static UI assertions without changing protected Phase 0–7 fixtures/results or hiding failures with skips.
2. With the user's explicit approval to resume paid API calls, rerun the strict Live Smoke and establish Search-backed scenario values, exact source linkage, and required calculation usage.
3. Re-run full pytest, Phase 7 regression, `uv lock --check`, browser E2E, and `git diff --check` after any changes.

## Stuck processing investigation: failure modes before code changes

The reported screen can persist when the browser receives no terminal answer/error event. The current browser code awaits `fetch` and each stream read without a deadline, keeps the workspace inert, and has no cancellation control. The agent stream likewise has no execution deadline. Before changing this isolated flow, check these possible failures with local E2E responses only:

- The server never sends response headers or the first progress event; the initial overlay text remains visible.
- A tool/model turn stops producing stream data after a progress event; the last stage remains visible indefinitely.
- A result event arrives but the stream never closes; rendering waits for EOF.
- The user cancels or a local deadline expires, but the browser remains inert or the server keeps processing.
- A malformed/error stream does not release the request lock and allow a retry.
- The overlay appears while `hidden` due to CSS or stale asset behavior, independent of a request.

The fix must not generate progress percentages, run paid API calls during verification, or mark a timed-out analysis as a completed answer.

### Local finding and change

The browser request had no deadline in `fetch` or `reader.read()`, and the agent stream had no execution deadline. A stalled response could therefore leave the fixed overlay and inert workspace in place indefinitely. The screenshot's unchanged initial overlay text with scenario cards behind it does not match the current JavaScript's state after submit; a mixed or cached browser asset is plausible but could not be confirmed from that screenshot alone.

The answer stream now has a 90-second server deadline and emits a localized error on timeout. The browser exposes `분석 중단`, aborts the request on click, and releases the lock; a 95-second browser deadline also releases the lock if the server never responds. A completed result is rendered without waiting for the stream to close. The HTML is served with `Cache-Control: no-store`, and the script/stylesheet URLs carry a new version parameter to refresh browser assets. None of these paths returns an invented answer.

Local E2E evidence: the 15 golden answers still pass, a deliberately stalled `/api/answers` request ends with a localized error and no result, and headless Chrome sees the overlay hidden initially, visible during a delayed request, then hidden with an enabled form after cancellation. The browser abort signal was observed by the local response stub. This does not prove that the user's currently running provider request completed or that a live Search answer can be produced; no paid API request was made for this investigation.
