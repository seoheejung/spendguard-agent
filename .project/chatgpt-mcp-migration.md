# ChatGPT-hosted SpendGuard: 최소 이전 계획

> 과거 대안 검토 기록입니다. 현재 제품은 독립 Web UI → FastAPI → ChatGPT 계정으로 인증된 Codex CLI → Search/MCP 구조이며, 현행 계획과 결과는 [plan.md](plan.md) 및 [Codex 런타임 실측](../docs/results/chapter-b-codex-runtime-mvp.md)에 있습니다. 아래 경로와 파일 분류는 현행 구현 지시가 아닙니다.

확인일: 2026-09-24

## 목표와 경계

사용자 질문, 최신 정보 검색, 추론, 최종 답변은 ChatGPT에서 처리한다. SpendGuard는 계산 MCP 도구를 제공한다. 이 실행 경로는 SpendGuard 서버가 OpenAI Platform의 Responses API를 호출하지 않는다. 독립 웹 UI를 ChatGPT 구독의 추론 백엔드에 연결하는 방식으로 해석하지 않는다.

현재 `/api/decisions`의 추가 개선과 15개 시나리오별 보정은 중단한다. 기존 코드는 ChatGPT에서 MCP를 실제로 연결하고 한 건의 질문을 완료하기 전까지 보존한다.

## 현재 코드의 역할

| 역할 | 현재 위치 | 최소 이전 판단 |
| --- | --- | --- |
| 자연어 이해, Search 필요 판단, 검색, 최종 설명 | `src/spendguard/agent.py`, `src/spendguard/main.py`의 `/api/decisions` | ChatGPT가 맡는다. 기존 경로는 검증용 legacy로 남긴다. |
| 계산식과 입력 검증 | `src/spendguard/calculations.py` | 그대로 재사용한다. |
| 여섯 계산 도구의 MCP 노출 | `src/spendguard/mcp_server.py` | 그대로 재사용한다. ChatGPT에서 보이는 이름·설명·입력 schema를 PoC에서 확인한다. |
| 로컬 MCP 클라이언트 | `src/spendguard/mcp_client.py` | 개발 검증용으로 유지한다. ChatGPT 런타임의 클라이언트는 ChatGPT다. |
| Jev의 네 가지 narrow judgment 실험 | `src/spendguard/decision_prototype.py`, `src/spendguard/jev.py` | PoC에서 제외한다. ChatGPT + Search + 계산 기준선 이후 이득이 입증된 판단만 별도 도구 후보로 검토한다. |
| Required Data / Pack routing / Structured Output | `src/spendguard/decision_packs.py`, `src/spendguard/models.py` | ChatGPT MCP 경로에 옮기지 않는다. 기존 API 경로가 보존되는 동안 legacy로 둔다. |
| 독립 웹 UI | `src/spendguard/static/` | 첫 PoC에서는 사용하지 않는다. |

## 최소 PoC 순서

1. 계정에서 **Settings → Security and login → Developer mode**, **ChatGPT Plugins → +**가 실제로 보이는지 확인한다. OpenAI Developers의 [Build for ChatGPT](https://developers.openai.com/chatgpt)는 Plus/Pro의 full MCP를 명시하지만, [연결 안내](https://developers.openai.com/plugins/deploy/connect-chatgpt)는 실제 가용성이 계정·workspace 정책에 따라 달라질 수 있다고 설명한다.
2. 기존 계산 MCP를 ChatGPT가 접속할 수 있는 연결로 제공한다. 공식 연결 조건은 공개 HTTPS의 streamable HTTP `/mcp` 또는 Secure MCP Tunnel이다. 로컬 `127.0.0.1` URL은 ChatGPT 연결 주소가 아니다. Tunnel은 별도 Platform 조직 권한과 런타임 API 키가 필요하므로, 연결 방식은 계정 UI와 운영 조건을 확인한 뒤 정한다. [공식 연결 안내](https://developers.openai.com/plugins/deploy/connect-chatgpt), [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels).
3. 개인 MCP 연결에서 기존 여섯 계산 도구를 확인한다. 질문 한 건은 `120만 원을 연 0%로 24개월 할부하면 월 납입액과 총액은?`로 고정한다. ChatGPT가 `calculate_installment`를 호출하고, 도구 결과의 월 50,000원·총 1,200,000원을 최종 답변에 반영하는지 확인한다.
4. 도구 호출·인수·결과와 ChatGPT 답변을 기록한다. 이 E2E가 성공한 뒤에만 Search가 필요한 질문과 15개 질문으로 넓힌다. 반복 지침이 필요해지면 Skill을 추가한다. [공식 Plugin Quickstart](https://developers.openai.com/plugins/quickstart)는 MCP만 연결하는 개인 Plugin을 먼저 만들고, Skill과 UI는 이후 추가하는 흐름을 안내한다.

## 현재 확인 결과

- 기존 stdio MCP에서 여섯 도구가 나열됐다. `calculate_installment(1,200,000원, 연 0%, 24개월)`의 결과는 월 50,000원, 총 1,200,000원이었다.
- 코드를 바꾸지 않고 같은 FastMCP 서버를 로컬 HTTP `http://127.0.0.1:8765/mcp`로 실행해 여섯 도구와 `annualize_expense(80,000원, 1개월) = 960,000원/년`을 확인했다. 로컬 서버는 검증 후 종료했다.
- ChatGPT 계정의 Developer mode, 개인 Plugin 등록, ChatGPT → MCP → ChatGPT 답변은 아직 확인되지 않았다. 이 E2E는 완료로 기록하지 않는다.

## 전환 조건

실제 ChatGPT PoC에서 도구 호출과 최종 답변을 확인한 뒤 `/api/decisions`와 Agents SDK/Responses API 경로를 제거할지 결정한다. 제거 전에 기존 로컬 수정·평가 자료와 독립 UI의 처리 방침을 별도로 검토한다. Jev는 기준선이 안정화된 뒤 같은 질문에서 품질과 호출 수·지연시간을 비교하고 채택 여부를 결정한다.
