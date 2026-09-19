# Phase 7. End-to-End Evaluation

> SpendGuard 전체 workflow의 정확성, 근거 추적성, 오류 처리, latency, 비용을 고정 평가 데이터로 검증하는 단계

## 1. 목적

Phase 1~6에서 구현한 전체 시스템을 기능 개수나 화면 완성도가 아니라 실제 의사결정 workflow의 검증 가능성으로 평가한다.

이번 Phase에서는 새로운 제품 기능을 추가하지 않는다.

## 2. 사전 조건

- Phase 6 Decision Packs 완료
- 전체 테스트 통과
- README와 각 Phase 결과 문서가 실제 구현 상태와 일치

Phase 6가 완료되지 않았다면 진행하지 않는다.

## 3. 평가 범위

전체 경로:

```text
User Input
→ Routing
→ Required Data
→ Jev / Code
→ Web Search
→ MCP Calculation
→ Verification
→ Decision Result
→ UI
```

6개 Decision Pack과 `unknown` / 모호한 질문을 포함한다.

## 4. 평가 데이터

End-to-End 전용 고정 평가 데이터를 생성한다.

최소 포함:

- Pack별 명확한 질문
- 필수 정보 충분
- 필수 정보 부족
- 검색 필요
- 검색 불필요
- 계산 필요
- 계산 불필요
- 모호한 질문
- 범위 밖 질문
- Tool 오류 또는 검색 실패 경로

평가 데이터와 expected 결과를 첫 실행 전에 고정한다.

평가 결과를 개선하기 위해 실행 후 정답을 임의 수정하지 않는다.

필요한 수정이 발생하면 version과 사유를 기록한다.

## 5. 핵심 지표

### Routing Accuracy

```text
정답 routing 수 / 전체 routing 평가 수 × 100
```

### Calculation Accuracy

결정론적 계산의 expected 값과 실제 값 비교.

목표:

```text
100%
```

### Required Data Accuracy

필수 입력 누락을 올바르게 식별했는지 측정한다.

### Source Coverage

외부 확인이 필요한 사실 중 출처가 연결된 비율을 측정한다.

### Unsupported Fact

검색 결과나 사용자 입력으로 근거를 확인할 수 없는 외부 사실의 수를 측정한다.

목표:

```text
0건
```

### Tool Error Handling

Tool 또는 검색 실패가 정상 오류 상태로 처리되는지 확인한다.

### End-to-End Success

각 평가 케이스가 기대한 workflow와 결과 schema를 완료했는지 측정한다.

## 6. 성능과 비용

가능한 범위에서 아래를 기록한다.

- 전체 latency
- 단계별 latency
- Jev 요청 수
- OpenAI 요청 수
- Web Search 호출 수
- MCP Tool 호출 수
- 실제 usage
- 검증 가능한 비용

가격이나 usage를 확인할 수 없는 항목은 추정하지 않는다.

서로 측정 방식이 다른 값을 직접 비교 가능한 수치처럼 표시하지 않는다.

## 7. Jev 평가

Phase 2 결과와 실제 Phase 6 routing 결과를 구분한다.

확인:

- Phase 2 고정 17건 결과 유지
- 실제 workflow routing 정확도
- confidence와 실제 정답 관계
- 높은 confidence 오분류 존재 여부
- fallback 동작

`ambiguous-001`은 회귀 케이스로 유지한다.

## 8. Calculation / MCP 평가

Phase 3 Calculation Tool과 Phase 4 MCP 결과가 End-to-End에서도 동일한 계산 결과를 유지하는지 확인한다.

최소 확인:

- 계산식
- 입력
- 중간값
- 최종값
- 반올림
- 오류 전달

## 9. Web Search 평가

확인:

- 검색 필요 여부
- 실제 검색 실행
- 공식 출처 우선
- 출처 URL
- 조회 시각
- 검색 실패 처리
- 상충 정보 처리

근거 없는 외부 사실이 결과에 포함되지 않아야 한다.

## 10. UI 회귀 검증

Phase 4.5의 기본 UI 기준을 다시 확인한다.

- Desktop
- Mobile
- Keyboard Navigation
- Decision 상태
- Sources
- 긴 콘텐츠
- 오류 상태
- Motion 감소 설정
- 구현되지 않은 기능 노출 없음

UI 시각 개선을 위한 대규모 재설계는 이번 Phase 범위가 아니다.

## 11. 회귀 테스트

Phase 1~6의 기존 테스트를 모두 유지한다.

과거 실패 케이스를 삭제하거나 우회하지 않는다.

기존 결과와 달라진 동작이 있으면 원인을 문서화한다.

## 12. 제외

이번 Phase에서는 구현하지 않는다.

- 새로운 Decision Pack
- 새로운 계산 Tool
- 새로운 외부 서비스
- Multi-Agent
- 자동 구매 또는 계약
- 데이터베이스
- 기능 범위 확대

평가 중 발견한 개선 사항은 결과 문서의 후속 과제로 기록한다.

## 13. 결과 문서

```text
docs/results/phase7-end-to-end-evaluation.md
```

최소 기록:

- 평가 데이터 버전과 케이스 수
- Pack별 결과
- Routing Accuracy
- Calculation Accuracy
- Required Data Accuracy
- Source Coverage
- Unsupported Fact 수
- Tool Error 처리 결과
- End-to-End Success
- latency
- usage / 비용
- 주요 실패 케이스
- 후속 개선 항목

## 14. 성공 기준

최소 기준:

- Calculation Accuracy: 100%
- Unsupported Fact: 0건
- Tool 오류 미처리: 0건
- 외부 사실 출처 추적 가능
- 고정 평가 데이터 결과 재현 가능
- 기존 Phase 테스트 회귀 없음

Routing, Required Data, End-to-End 지표는 실제 측정값을 기록하며 결과를 숨기거나 기준에 맞춰 정답을 수정하지 않는다.

## 15. 완료 기준

- End-to-End 고정 평가 데이터 생성
- 전체 평가 실행 완료
- 핵심 지표 계산
- 실제 latency / usage / 확인 가능한 비용 기록
- UI 회귀 검증
- 전체 기존 테스트 통과
- 실패 케이스 문서화
- 결과 문서 작성
- README 최종 상태 반영
- `uv run --no-cache --no-sync pytest` 성공
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
- 완료 후 commit / push
