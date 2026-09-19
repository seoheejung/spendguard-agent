# Phase 3 Calculation Tools 결과

## 구현 Tool

| Tool | 처리 |
| --- | --- |
| `calculate_installment` | 원리금 균등 월 납입금, 총 납입금, 총 이자 |
| `calculate_refinance` | 기존 잔여 비용, 신규 잔여 비용, 수수료 포함 절감액 |
| `calculate_usage_cost` | 사용 단위당 비용 |
| `annualize_expense` | 기간 지출의 연간 환산 |
| `calculate_tco` | 구매비, 월 보유비, 추가 비용 기반 TCO |
| `compare_costs` | 최저 비용 선택지와 비용 차이 |

## 출력 구조

모든 Tool의 `CalculationResult` 출력:

```json
{
  "inputs": {},
  "formula": "",
  "intermediate": {},
  "result": {}
}
```

## 계산식

| Tool | 공식 |
| --- | --- |
| 할부 | `P*r*(1+r)^n / ((1+r)^n-1)`, `r = annual_rate / 1200` |
| 대환 | `기존 잔여 총액 - (신규 잔여 총액 + 대환 수수료)` |
| 사용당 비용 | `총비용 / 사용 단위` |
| 연간 환산 | `금액 * (12 / 기간 월수)` |
| TCO | `구매비 + (월 보유비 * 보유 월수) + 추가 비용` |
| 비용 비교 | `선택지 총비용 - 최저 총비용` |

## 반올림 규칙

- 통화 결과: 소수점 둘째 자리
- 방식: `Decimal`과 `ROUND_HALF_UP`
- 통화 변환 미수행

## 테스트

| 항목 | 결과 |
| --- | --- |
| 전체 pytest | 26 passed |
| 계산 Tool 테스트 | 10 passed |
| 정상 입력 | 통과 |
| 0 값 | 통과 |
| 음수 입력 거부 | 통과 |
| 잘못된 기간 거부 | 통과 |
| 경계값 | 통과 |
| 반올림 | 통과 |
| 동일 입력 재현성 | 통과 |

## 범위 제외

- MCP Server
- Jev routing
- Web Search
- Decision Pack workflow
- UI 기능 확장
- 외부 API 호출
