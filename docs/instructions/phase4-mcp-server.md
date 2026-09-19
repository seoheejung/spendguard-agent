# Phase 4. MCP Server

> Phase 3 Calculation Tools를 MCP Tool로 노출하고 직접 호출과 MCP 호출 결과를 비교·검증하는 단계

## 1. 목적

Phase 3에서 검증한 결정론적 계산 기능을 FastMCP 기반 MCP Server로 분리한다.

MCP는 계산 로직을 새로 구현하지 않고 기존 Calculation Tool을 호출하는 연결 계층으로 사용한다.

## 2. 사전 조건

- Phase 3 Calculation Tools 완료
- Phase 3 테스트 통과
- 계산 공식과 출력 schema 고정

Phase 3가 완료되지 않았다면 Phase 4를 진행하지 않는다.

## 3. 구현 범위

- FastMCP 추가
- stdio MCP Server
- Phase 3 계산 기능 MCP Tool 등록
- 독립 MCP Client
- MCP Tool input/output schema 검증
- 직접 함수 호출과 MCP 호출 결과 비교
- 오류 전달 검증
- 관련 테스트
- 결과 문서 작성

## 4. MCP Tool

Phase 3에서 구현된 계산 기능만 MCP로 노출한다.

예상 대상:

```text
calculate_installment
calculate_refinance
calculate_usage_cost
annualize_expense
calculate_tco
compare_costs
```

Phase 4에서 새로운 계산 로직을 추가하지 않는다.

## 5. 구조

```text
Client
  ↓
MCP Client
  ↓
FastMCP Server
  ↓
Calculation Tools
```

계산 로직의 source of truth는 Phase 3 코드다.

## 6. 비교 검증

동일 입력에 대해 아래 결과가 일치해야 한다.

```text
Direct Function Call
=
MCP Tool Call
```

비교 항목:

- 최종 결과
- 중간값
- 계산식
- 오류 타입
- 입력 검증 결과

## 7. Transport

초기 검증은 stdio를 사용한다.

Streamable HTTP, 인증, 원격 배포는 이번 Phase 범위에 포함하지 않는다.

## 8. 테스트

최소 검증:

- MCP Server 시작
- Tool 목록 확인
- 각 Tool 호출 성공
- input schema 검증
- output schema 검증
- 잘못된 입력 오류
- 직접 호출과 MCP 결과 일치
- 서버 종료 처리

## 9. 제외

이번 Phase에서는 구현하지 않는다.

- Remote MCP 배포
- Streamable HTTP
- MCP 인증
- Jev production routing
- Web Search
- Decision Pack workflow
- Multi-Agent
- 데이터베이스
- UI 기능 확장

## 10. 결과 문서

```text
docs/results/phase4-mcp-server.md
```

기록:

- FastMCP 버전
- 노출 Tool
- 직접 호출/MCP 비교 결과
- 테스트 결과
- 실행 방법
- 오류 처리
- 미완료 사항

## 11. 완료 기준

- stdio MCP Server 실행 성공
- Calculation Tool MCP 노출
- 독립 MCP Client 호출 성공
- 직접 호출과 MCP 결과 일치
- 관련 테스트 통과
- 결과 문서 작성
- README 실제 상태 반영
- `uv run --no-cache --no-sync pytest` 성공
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
