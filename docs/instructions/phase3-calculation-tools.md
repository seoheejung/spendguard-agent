# Phase 3. Calculation Tools

> SpendGuard의 비용 계산을 모델 추론에서 분리하고 결정론적 코드로 구현·검증하는 단계

## 1. 목적

할부, 대출 변경, 사용당 비용, 장기 보유 비용 등 숫자 계산을 LLM/Jev가 아닌 결정론적 코드로 처리한다.

Phase 2 Jev 평가 결과와 무관하게 진행한다.

## 2. 구현 범위

- 계산 Tool 공통 입력/출력 모델
- 할부 비용 계산
- 대출 변경 비용 계산
- 사용당 비용 계산
- 연간 비용 환산
- TCO 계산
- 선택지 비용 비교
- 계산식 및 중간값 반환
- 단위 테스트
- 결과 문서 작성

## 3. 계산 원칙

- 계산은 모델에 맡기지 않는다.
- 입력값, 계산식, 중간값, 최종값을 추적 가능하게 유지한다.
- 통화와 기간 단위를 명시한다.
- 반올림 규칙을 코드에서 고정한다.
- 누락값을 임의 추정하지 않는다.
- 숫자 오류를 자연어로 보정하지 않는다.

## 4. 최소 Tool

```text
calculate_installment
calculate_refinance
calculate_usage_cost
annualize_expense
calculate_tco
compare_costs
```

실제 함수명은 저장소 기존 구조와 일관되게 조정할 수 있다.

## 5. 출력

각 계산 결과는 최소한 아래 정보를 포함한다.

```json
{
  "inputs": {},
  "formula": "",
  "intermediate": {},
  "result": {}
}
```

Pydantic 모델로 타입을 고정한다.

## 6. 테스트

최소 검증:

- 정상 입력
- 0 값
- 음수 입력 거부
- 잘못된 기간 거부
- 경계값
- 반올림
- 동일 입력 재현성
- 예상값과 정확히 일치

외부 API 없이 로컬에서 모두 검증 가능해야 한다.

## 7. 제외

이번 Phase에서는 구현하지 않는다.

- MCP Server
- Jev routing
- Web Search
- Decision Pack workflow
- 사용자 인증
- 데이터베이스
- 자동 구매/계약
- UI 기능 확장

## 8. 결과 문서

```text
docs/results/phase3-calculation-tools.md
```

기록:

- 구현 Tool
- 계산 공식
- 테스트 케이스
- 테스트 결과
- 반올림 규칙
- 미완료 사항

## 9. 완료 기준

- 정의된 계산 Tool 구현
- 모든 계산 로컬 테스트 통과
- 모델 호출 없이 계산 가능
- 입력/출력 schema 검증
- 결과 문서 작성
- README 실제 상태 반영
- `uv run --no-cache --no-sync pytest` 성공
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
