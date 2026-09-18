# Phase 1. Core Agent Baseline

> Jev 도입 전 SpendGuard의 기본 질문 처리와 OpenAI Structured Output baseline을 구현·검증하는 단계

## 1. 학습·검증 목적

Phase 2 Jev 비교를 위한 기준선을 만든다.

이번 Phase에서는 OpenAI 기반 기본 Agent가 소비 질문을 어떻게 분류하고 필요한 정보를 식별하는지 고정 평가 데이터와 함께 확인한다.

## 2. 구현 범위

- Python 프로젝트 초기화
- FastAPI 기본 애플리케이션
- OpenAI Agents SDK 기반 단일 Agent
- 자연어 질문 입력
- Intent 분류
- 사용자 입력에서 확인 가능한 사실 추출
- 필수 정보 누락 식별
- Structured Output
- 기본 Web UI
- 고정 평가 데이터
- 관련 테스트

## 3. Intent

Phase 1에서 아래 분류를 사용한다.

- `purchase`
- `recurring_cost`
- `finance_cost`
- `ownership_cost`
- `quote_audit`
- `budget_optimization`
- `unknown`

Intent 정의는 테스트와 평가 데이터에서 동일하게 사용한다.

## 4. Structured Output

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

필요한 필드와 타입은 구현 시 Pydantic schema로 고정한다.

## 5. 기본 Web UI

최소 기능:

- 자연어 질문 입력
- 요청 실행
- Intent 표시
- 확인된 사실 표시
- 누락 정보 표시
- 오류 표시

`DESIGN.md` 범위만 적용한다.

## 6. 평가 데이터

Phase 2에서도 그대로 사용할 수 있도록 고정 케이스를 만든다.

최소 범주:

- 각 Intent의 명확한 질문
- Intent가 모호한 질문
- 필수 정보가 충분한 질문
- 필수 정보가 부족한 질문
- 프로젝트 범위 밖 질문

평가 데이터에는 최소한 아래 값을 포함한다.

```json
{
  "id": "purchase-001",
  "input": "189만원짜리 노트북을 살지 고민 중이다.",
  "expected_intent": "purchase"
}
```

Phase 1 완료 후 평가 데이터를 Phase 2 비교 기준으로 변경하지 않는다.
필요한 수정이 발생하면 변경 사유와 version을 기록한다.

## 7. 제외

이번 Phase에서는 구현하지 않는다.

- TypeSafe Jev
- `typesafe-sdk`
- `TYPESAFE_API_KEY`
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

## 8. 구현 원칙

- `.project/plan.md` 범위 준수
- 단일 Agent 유지
- 미래 Phase용 추상화 추가 금지
- 필요한 패키지만 추가
- OpenAI 설정 환경 변수 관리
- Pydantic 기반 출력 검증
- UI 변경 시 `DESIGN.md` 준수
- 계산 결과가 필요한 질문에도 Phase 1에서 계산 기능 선반영 금지

## 9. 테스트

최소 검증:

- `purchase` Intent 분류
- `recurring_cost` Intent 분류
- `finance_cost` Intent 분류
- `ownership_cost` Intent 분류
- `quote_audit` Intent 분류
- `budget_optimization` Intent 분류
- 범위 밖 질문 `unknown` 처리
- 정보 부족 질문 `missing_fields` 반환
- Structured Output schema 검증
- API 오류 처리

## 10. 기록할 결과

Phase 완료 후 `docs/results/phase1-core-agent.md`에 실제 결과만 기록한다.

- 사용 모델
- 평가 케이스 수
- Intent 정답 수
- Intent 정확도
- 실패 케이스
- 테스트 결과
- 실제 실행 확인 결과

## 11. 완료 기준

- FastAPI 애플리케이션 실행 성공
- 자연어 질문 입력 가능
- Intent 반환 확인
- 필수 정보 누락 반환 확인
- Structured Output schema 검증 성공
- 고정 평가 데이터 생성
- 정의된 테스트 통과
- 실제 검증 결과 문서 작성
- README Phase 1 상태 반영
- `git diff` 검토
- `git status` 확인
