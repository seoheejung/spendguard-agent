# Phase 5. Current Information Research

> 가격·정책·요금제처럼 변동 가능한 외부 사실을 Web Search로 확인하고 출처와 조회 시점을 추적하는 단계

## 1. 목적

모델 내부 지식만으로 최신 정보를 단정하지 않고, 변동 가능한 외부 사실을 실제 Web Search 결과와 연결한다.

이번 Phase에서는 검색 자체와 근거 추적을 구현하며 Decision Pack별 최종 workflow는 Phase 6에서 구성한다.

## 2. 사전 조건

- Phase 4.5 Decision Workspace UI 완료
- Phase 1 OpenAI Agent 동작 확인
- Phase 3 Calculation Tools와 Phase 4 MCP Server 완료

Phase 4.5가 완료되지 않았다면 진행하지 않는다.

## 3. 구현 범위

- OpenAI Agents SDK 공식 `WebSearchTool` 연동
- 변동 가능 정보의 검색 필요 여부 처리
- 검색 질의 생성
- 검색 결과와 외부 사실 분리
- 출처 URL과 출처명 수집
- 조회 시각 기록
- 공식 출처 우선 처리
- 검색 실패와 근거 부족 처리
- UI의 `Researching` 상태 활성화
- Sources 영역 연결
- 관련 테스트
- 결과 문서 작성

## 4. 검색 대상

검색이 필요한 정보:

- 현재 판매 가격
- 현재 요금제
- 구독 가격
- 공식 정책
- 프로모션
- 제품 사양과 현재 판매 조건

검색하지 않는 정보:

- 사용자가 이미 제공한 값
- Phase 3에서 계산 가능한 값
- 코드로 확정 가능한 규칙
- 변하지 않는 계산 공식

불필요한 검색 호출을 만들지 않는다.

## 5. 출처 원칙

가능한 경우 아래 우선순위를 사용한다.

```text
공식 제조사 / 서비스 / 기관
→ 공식 판매·정책 페이지
→ 신뢰 가능한 1차 또는 전문 출처
→ 기타 검색 결과
```

공식 출처가 존재하지 않거나 확인되지 않으면 그 사실을 기록한다.

검색 결과에 없는 사실을 모델이 보완해서 만들지 않는다.

## 6. 외부 사실 구조

외부 사실은 최소한 아래 정보를 추적 가능하게 유지한다.

```json
{
  "value": "",
  "source_name": "",
  "source_url": "",
  "retrieved_at": ""
}
```

필요한 경우 `published_at`을 추가할 수 있다.

확인할 수 없는 날짜를 임의 생성하지 않는다.

## 7. Agent 역할

OpenAI Agent는 아래 역할을 담당한다.

- 검색 필요 여부에 따른 Web Search 사용
- 검색 질의 구성
- 관련 결과 선택
- 복수 출처의 정보 통합
- 근거가 부족한 경우 사용자에게 명시

검색 결과 자체와 Agent 해석을 구분한다.

## 8. UI 연결

Phase 4.5 UI에 실제 `Researching` 상태를 추가한다.

Sources 영역에서는 최소한 아래 정보를 확인할 수 있어야 한다.

- 출처명
- 확인한 값 또는 사실
- 출처 링크
- 조회 시각

구현되지 않은 Decision Pack 전용 화면은 추가하지 않는다.

## 9. 오류 처리

최소 처리:

- 검색 결과 없음
- 공식 출처 확인 실패
- 검색 Tool 오류
- 상충하는 검색 결과
- 최신성 판단 불가

근거가 충분하지 않으면 임의로 값을 확정하지 않는다.

## 10. 테스트

최소 검증:

- 검색 필요 정보에서 Web Search 사용
- 검색 불필요 정보에서 불필요한 호출 없음
- 출처 URL 수집
- 조회 시각 기록
- 외부 사실과 Agent 설명 분리
- 검색 실패 처리
- Sources UI 표시
- `Researching` 상태 전환

실제 외부 호출 테스트와 로컬 단위 테스트를 구분한다.

## 11. 제외

이번 Phase에서는 구현하지 않는다.

- Decision Pack별 전체 workflow
- 자동 구매 또는 계약
- 데이터베이스
- 사용자 금융 계정 연동
- Multi-Agent
- Remote MCP 배포
- 검색 결과 기반 가격 예측

## 12. 결과 문서

```text
docs/results/phase5-current-information-research.md
```

기록:

- 사용한 Web Search 방식
- 검색 대상과 비검색 대상
- 출처 구조
- 실제 검색 검증 결과
- 오류 처리
- UI 연결 결과
- 테스트 결과
- 미완료 사항

## 13. 완료 기준

- 실제 Web Search 호출 성공
- 변동 정보와 비변동 정보 분리
- 외부 사실의 출처와 조회 시각 추적
- 공식 출처 우선 처리 확인
- 검색 실패 처리 확인
- `Researching` 상태와 Sources UI 연결
- 관련 테스트 통과
- 결과 문서 작성
- README 실제 상태 반영
- `uv run --no-cache --no-sync pytest` 성공
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
- 완료 후 commit / push
