# Phase 6. Decision Packs

> Jev, OpenAI Agent, Web Search, MCP Calculation Tools를 실제 소비 의사결정 workflow로 연결하는 단계

## 1. 목적

Phase 1~5에서 개별적으로 검증한 판단, 계산, 검색, UI 요소를 Decision Pack 단위의 실제 workflow로 연결한다.

이번 Phase에서 처음으로 사용자의 소비 질문이 하나의 의사결정 흐름으로 처리되도록 구성한다.

## 2. 사전 조건

- Phase 2 Jev 평가 완료
- Phase 3 Calculation Tools 완료
- Phase 4 MCP Server 완료
- Phase 4.5 Decision Workspace UI 완료
- Phase 5 Current Information Research 완료

하나라도 완료되지 않았다면 진행하지 않는다.

## 3. 구현 대상

아래 6개 Decision Pack을 지원한다.

| Pack | 처리 대상 |
| --- | --- |
| Purchase | 제품 구매, 중고, 대체재, 구매 시점 |
| Recurring Cost | 구독, 통신비, 반복 지출 |
| Finance Cost | 할부, 대출 변경 |
| Ownership Cost | 자동차 등 장기 보유 비용 |
| Quote Audit | 견적서, 계약 비용 |
| Budget Optimization | 장보기, 여행, 최근 지출 |

## 4. 공통 Workflow

```text
User Question
    ↓
Decision Pack 판단
    ↓
Required Data 확인
    ↓
필요 시 사용자 입력 요청
    ↓
필요 시 Web Search
    ↓
필요 시 MCP Calculation Tool
    ↓
근거와 계산 검증
    ↓
Option 비교
    ↓
Decision Result
```

각 단계의 담당 계층을 명확히 구분한다.

## 5. 역할 분리

### Jev

- 코드에서 정의한 후보 중 좁은 typed judgment
- Decision Pack 후보 판단에 사용할 수 있음

Phase 2에서 `ambiguous-001`을 높은 confidence로 오분류했으므로 confidence 값만으로 production routing을 확정하지 않는다.

Jev 결과를 실제 routing에 사용할 경우 별도 코드 정책과 fallback을 명시하고 테스트한다.

### OpenAI Agent

- 사용자 요청 해석
- 필요한 Tool orchestration
- 검색 결과와 계산 결과 통합
- 사용자용 최종 설명

### Code

- Pack별 필수 필드
- 입력 타입과 단위
- routing 정책
- fallback
- Tool 호출 조건
- 결과 schema

### MCP

Phase 3에서 구현하고 Phase 4에서 노출한 기존 계산 Tool만 재사용한다.

새로운 계산 로직이 필요하면 현재 Phase에서 임의로 추가하지 않고 기획 범위와 필요성을 먼저 확인한다.

### Web Search

Phase 5 기준으로 변동 가능한 외부 사실에만 사용한다.

## 6. Pack별 최소 요구사항

### Purchase

최소 입력:

- 대상
- 사용 목적
- 가격 또는 가격 확인 필요 여부

활용 가능 기능:

- 현재 가격 조사
- 사용당 비용
- 대체 선택지 비용 비교

### Recurring Cost

최소 입력:

- 서비스 또는 지출 항목
- 현재 비용

활용 가능 기능:

- 연간 비용 환산
- 반복 비용 비교
- 현재 공식 가격 확인

### Finance Cost

최소 입력:

- 금액
- 기간
- 금리 또는 비교 조건

활용 가능 기능:

- 할부 비용
- 대환 비용 비교

### Ownership Cost

최소 입력:

- 대상
- 보유 기간

활용 가능 기능:

- TCO
- 반복 보유 비용

### Quote Audit

최소 입력:

- 견적 항목 또는 견적 내용

활용 가능 기능:

- 항목별 비용 구조 확인
- 비교 가능한 외부 가격 조사
- 과도 여부는 근거가 있을 때만 표시

### Budget Optimization

최소 입력:

- 예산 또는 지출 데이터

활용 가능 기능:

- 연간 환산
- 비용 선택지 비교
- 반복 지출 분석

## 7. 최종 결과 구조

최종 결과는 최소한 아래 항목을 구분한다.

```text
Conclusion
Facts
Assumptions
Calculations
Options
Risks
Next Actions
Sources
```

- 사실과 가정을 분리한다.
- 계산 결과에는 계산식과 입력값을 연결한다.
- 외부 사실에는 출처를 연결한다.
- 근거가 부족하면 결론을 강제로 생성하지 않는다.

## 8. UI 연결

Decision Workspace에서 실제 Decision Pack 결과를 표시한다.

- Pack
- 상태
- 확인된 사실
- 필요한 입력
- 계산 결과
- 선택지
- 출처
- 최종 결과

Decision Card와 공통 Layout은 데이터 기반으로 유지한다.

Pack마다 화면 구조를 복제하지 않는다.

## 9. Routing 검증

최소 검증:

- 6개 Pack의 명확한 질문
- `unknown`
- 모호한 질문
- 필수 입력 부족
- 검색 필요 / 불필요
- 계산 필요 / 불필요

Phase 1·2의 `ambiguous-001`을 그대로 회귀 테스트에 포함한다.

Jev confidence threshold만으로 모호한 요청을 해결했다고 간주하지 않는다.

## 10. 테스트

각 Pack에 대해 최소한 아래 경로를 검증한다.

- 정상 처리
- 필수 입력 부족
- 외부 검색 필요
- 계산 필요
- Tool 오류
- 근거 부족
- 최종 결과 schema

실제 API 호출 테스트와 결정론적 로컬 테스트를 구분한다.

## 11. 제외

이번 Phase에서는 구현하지 않는다.

- 자동 구매
- 자동 계약
- 자동 구독 해지
- 은행 또는 카드 계정 직접 연동
- 투자 자문
- 신용평가
- Multi-Agent
- 가격 예측 모델

## 12. 결과 문서

```text
docs/results/phase6-decision-packs.md
```

기록:

- Pack별 구현 범위
- 계층별 역할
- routing 정책
- Jev 적용 범위
- Tool 사용 구조
- UI 연결 결과
- 테스트 결과
- 실패 또는 제한 사항

## 13. 완료 기준

- 6개 Decision Pack 실제 workflow 구현
- 필수 입력 확인 동작
- 필요한 경우 Web Search 사용
- 필요한 경우 MCP Calculation Tool 사용
- 사실 / 가정 / 계산 / 출처 분리
- Decision Workspace 연결
- 모호한 질문과 `unknown` 처리 검증
- 관련 테스트 통과
- 결과 문서 작성
- README 실제 상태 반영
- `uv run --no-cache --no-sync pytest` 성공
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
- 완료 후 commit / push
