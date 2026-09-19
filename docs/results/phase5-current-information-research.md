# Phase 5 Current Information Research 결과

## 구현

- 변동 가능한 가격, 요금제, 구독, 정책, 프로모션, 사양, 판매 조건 질문만 backend `needs_current_information()`으로 구분한다.
- 검색이 필요한 요청에만 OpenAI Agents SDK `WebSearchTool`을 붙이고, `tool_choice="required"`로 실제 Web Search 호출을 요구한다. 계산·사용자 제공 금액 질문에는 Tool을 추가하지 않는다.
- Responses 출력의 `web_search_call.action.sources`와 URL citation을 수집한다. Agent가 제안한 fact의 URL이 실제 응답 URL과 일치할 때만 external fact로 보존한다.
- external fact는 `value`, `source_name`, `source_url`, `retrieved_at`를 기록한다. `source_name`은 Responses citation title(없으면 URL host)에서 얻고, `retrieved_at`은 응답 정규화 시 UTC로 기록한다. `published_at`은 생성하지 않는다.
- Agent 설명(`summary`)과 사용자 제공 사실(`known_facts`)은 external fact와 별도 필드로 유지한다. 검색 결과 없음, 공식 출처 미확인, 상충 결과, 최신성 확인 불가를 상태와 note로 표시하며 상충·최신성 미확인 결과에서는 확정 fact를 비운다. Tool 오류는 API 502로 전달한다.
- Decision Workspace는 backend research preflight가 필요하다고 확인한 경우에만 실행 중 `Researching` 상태를 보이고, 응답의 Sources 영역에 확인 사실, 출처명, 링크, 조회 시각을 렌더링한다.

## 공식 문서 확인

- OpenAI 공식 [Web search guide](https://developers.openai.com/api/docs/guides/tools-web-search)를 확인했다. 이 문서의 Responses `web_search` 도구, `web_search_call`, URL citation 형식을 기준으로 구현했다.

## 로컬 단위/API/UI 검증

- 검색 필요 분류와 비검색(사용자 제공 금액·결정론적 계산) 분류를 검증했다.
- `WebSearchTool`은 research 요청에만 설정되고, `response_include=["web_search_call.action.sources"]` 및 required tool choice가 적용됨을 검증했다.
- 실제 citation URL만 보존, source name/URL/retrieved_at 정규화, 검색 결과 없음, 공식 출처 미확인, 상충 정보, 최신성 확인 불가, Tool 오류를 모의 Responses 출력으로 검증했다.
- API의 research preflight 및 research 오류 502, Sources/Researching UI 계약을 검증했다.

## 실제 외부 호출 검증

- 2026-09-19에 설정된 로컬 OpenAI 자격 증명으로 `Apple iPhone current Korea sale price from official source`를 실행했다. API key는 출력하거나 기록하지 않았다.
- Web Search가 실제 호출되어 Apple Korea 공식 판매 페이지를 대상으로 한 query를 반환했다.
- 결과: `status=completed`, `official_source_confirmed=true`, external fact 5건, 모든 fact의 source URL 및 retrieved_at 존재를 확인했다.
- 실제 호출은 검색 성공 여부와 trace field 존재만 기록했으며, 검색된 가격·사양·published_at을 문서에 재기록하지 않았다.

## 범위 제외

- Phase 6 Decision Pack workflow, 자동 구매·계약, 검색 기반 가격 이력, DB, remote MCP는 구현하지 않았다.
