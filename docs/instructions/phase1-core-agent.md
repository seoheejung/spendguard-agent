# Phase 1. Core Agent

> SpendGuard의 기본 질문 처리와 구조화 출력만 구현·검증하는 단계

## 1. 범위

이번 Phase에서는 아래 기능만 구현한다.

- Python 프로젝트 초기화
- FastAPI 기본 애플리케이션
- SpendGuard 단일 Agent
- 자연어 질문 입력
- Intent 분류
- 필수 입력값 누락 식별
- Structured Output
- 기본 Web UI
- 관련 테스트

## 2. 구현 대상

### Intent

Phase 1에서 최소한 아래 분류를 지원한다.

- `purchase`
- `recurring_cost`
- `finance_cost`
- `ownership_cost`
- `quote_audit`
- `budget_optimization`
- `unknown`

### Structured Output

최소 구조:

```json
{
  "intent": "purchase",
  "summary": "",
  "known_facts": [],
  "missing_fields": [],
  "assumptions": []
}
```

### Web UI

최소 기능:

- 자연어 질문 입력
- 요청 실행
- Intent 표시
- 확인된 사실 표시
- 누락 정보 표시
- 오류 표시

## 3. 제외

이번 Phase에서는 구현하지 않는다.

- MCP Server
- Calculation Tool
- Web Search
- CSV 분석
- PDF 분석
- Multi-Agent
- 데이터베이스
- 사용자 인증
- 자동 구매 또는 자동 계약
- Decision Pack별 실제 비용 계산

## 4. 구현 원칙

- `.project/plan.md` 범위 준수
- 단일 Agent 유지
- 미래 Phase용 추상화 추가 금지
- 필요한 패키지만 추가
- 환경 변수 기반 OpenAI 설정
- Pydantic 기반 출력 검증
- UI 변경 시 `DESIGN.md` 준수

## 5. 테스트

최소 검증:

- purchase 질문 Intent 분류
- recurring_cost 질문 Intent 분류
- finance_cost 질문 Intent 분류
- 정보 부족 질문 missing_fields 반환
- 알 수 없는 질문 unknown 처리
- Structured Output schema 검증
- API 오류 처리

## 6. 완료 기준

- FastAPI 애플리케이션 실행 성공
- 자연어 질문 입력 가능
- Intent 반환 확인
- 필수 정보 누락 반환 확인
- Structured Output schema 검증 성공
- 정의된 테스트 통과
- 실제 검증 결과를 `docs/results/phase1-core-agent.md`에 기록
- README에 Phase 1 실제 상태 반영
- `git diff` 검토
- `git status` 확인
