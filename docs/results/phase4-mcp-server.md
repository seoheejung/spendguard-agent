# Phase 4 MCP Server 결과

## 구현 범위

- FastMCP 4.0.0
- stdio MCP Server: `spendguard.mcp_server`
- 독립 stdio MCP Client: `spendguard.mcp_client`
- Phase 3 `spendguard.calculations` 재사용
- 신규 계산 로직 없음

## 노출 MCP Tool

| Tool | 재사용 Calculation Tool |
| --- | --- |
| `calculate_installment` | 할부 비용 |
| `calculate_refinance` | 대출 변경 비용 |
| `calculate_usage_cost` | 사용당 비용 |
| `annualize_expense` | 연간 비용 환산 |
| `calculate_tco` | TCO |
| `compare_costs` | 비용 비교 |

## 실행 방법

```powershell
uv run python src/spendguard/mcp_server.py
```

`spendguard.mcp_client`의 독립 stdio Client를 통한 Tool 목록 조회와 Tool 호출.

## Direct / MCP 비교

동일 입력 기준 여섯 Tool의 Direct Function Call과 독립 stdio MCP Tool Call 비교.

| 비교 항목 | 결과 |
| --- | --- |
| 입력 | 일치 |
| 계산식 | 일치 |
| 중간값 | 일치 |
| 최종 결과 | 일치 |

## Schema 및 오류 처리

- 입력 schema: Phase 3 Pydantic 입력 모델
- 출력 schema: `inputs`, `formula`, `intermediate`, `result`
- 잘못된 입력: FastMCP `ToolError` 전달
- Client context 종료: stdio subprocess 종료 처리

## 테스트

| 항목 | 결과 |
| --- | --- |
| MCP Server 시작 및 Tool 목록 | 통과 |
| 여섯 MCP Tool 호출 | 통과 |
| 입력 schema 검증 | 통과 |
| 출력 schema 검증 | 통과 |
| 잘못된 입력 오류 전달 | 통과 |
| Direct / MCP 결과 비교 | 통과 |
| `uv run --no-cache --no-sync pytest` | 35 passed |

## 범위 제외

- Remote MCP 배포
- Streamable HTTP
- MCP 인증
- Jev production routing
- Web Search
- Decision Pack workflow
