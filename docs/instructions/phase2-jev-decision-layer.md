# Phase 2. Jev Decision Layer Evaluation

> Phase 1 OpenAI baseline과 동일한 평가 데이터로 TypeSafe Jev의 Intent 분류 성능을 비교·검증하는 단계

## 1. 학습·검증 목적

Phase 1에서 확보한 OpenAI Intent 분류 baseline과 TypeSafe Jev를 동일한 조건에서 비교한다.

이번 Phase에서는 Jev를 실제 SpendGuard workflow에 바로 적용하지 않는다.

먼저 좁고 닫힌 선택지의 Intent 분류에서 정확도, 지연 시간, 오류를 측정하고 후속 적용 여부를 판단한다.

## 2. 사전 조건

작업 시작 전 아래 조건을 확인한다.

- Phase 1 실제 모델 평가 17건 완료
- Phase 1 Intent 정답 수와 정확도 기록 완료
- `evals/phase1_cases.json` 고정
- TypeSafe Skill 설치 및 확인 완료
- `TYPESAFE_API_KEY` 환경 변수 설정 가능

Phase 1 실제 평가가 완료되지 않았다면 Phase 2 구현을 진행하지 않고 미완료 조건을 보고한다.

API Key 실제 값은 출력하지 않는다.

## 3. 구현 범위

- 설치된 TypeSafe Skill 확인 및 사용
- TypeSafe 공식 Python SDK 추가
- Jev Client 구성
- `Choice` 기반 Intent 분류
- Phase 1의 동일한 17개 평가 데이터 사용
- Jev 전용 평가 스크립트
- 정확도 및 지연 시간 측정
- 실패 케이스 기록
- Phase 1 OpenAI baseline과 결과 비교
- 관련 단위 테스트
- 결과 문서 작성

## 4. Intent

Phase 1과 동일한 분류를 사용한다.

- `purchase`
- `recurring_cost`
- `finance_cost`
- `ownership_cost`
- `quote_audit`
- `budget_optimization`
- `unknown`

Intent 이름, 의미, 평가 정답을 변경하지 않는다.

Jev의 `Choice` 후보는 코드에서 위 7개로 고정한다.

모델이 새로운 Intent를 생성하도록 하지 않는다.

## 5. Jev 적용 방식

이번 Phase의 Jev 사용 범위는 Intent 분류로 제한한다.

```text
User Input
    ↓
Jev Choice
    ↓
7개 Intent 중 하나
    ↓
Evaluation
```

`Choice`의 criteria에는 각 Intent의 의미를 명확하게 정의한다.

Phase 1 평가 결과를 보고 특정 케이스에 맞도록 criteria를 임의 조정하지 않는다.

초기 criteria를 변경해야 할 경우 변경 이유와 변경 전후 결과를 기록한다.

## 6. TypeSafe 설정

공식 Python SDK를 사용한다.

```text
typesafe-sdk
```

인증:

```text
TYPESAFE_API_KEY
```

환경 변수의 실제 값은 로그, 테스트 출력, 결과 문서에 기록하지 않는다.

SDK 사용법과 현재 API 형식은 설치된 TypeSafe Skill과 TypeSafe 공식 문서를 기준으로 확인한다.

SDK 내부 API나 응답 필드를 추측해서 구현하지 않는다.

## 7. 평가 데이터

Phase 1에서 생성한 아래 파일을 그대로 사용한다.

```text
evals/phase1_cases.json
```

금지:

- 케이스 삭제
- 정답 변경
- Jev에 유리하도록 문장 수정
- 별도 Jev 전용 정답 생성

필요한 메타데이터가 있다면 기존 평가 정답을 변경하지 않는 범위에서 별도 결과 파일에 기록한다.

## 8. 평가 항목

최소 측정:

- 전체 케이스 수
- Intent 정답 수
- Intent 정확도
- 실패 케이스 ID
- `expected_intent`
- `actual_intent`
- 요청별 지연 시간
- 전체 실행 시간
- API 오류 수

계산:

```text
Intent Accuracy
= Intent 정답 수 / 전체 평가 케이스 수 × 100
```

지연 시간은 최소 평균값을 기록한다.

가능하면 동일 실행 결과에서 p50도 기록한다.

비용 또는 Token 사용량은 SDK/API가 실제 usage 값을 제공하거나 공식 가격과 실제 token 수를 확인할 수 있는 경우에만 계산한다.

확인할 수 없는 비용을 추정해서 기록하지 않는다.

## 9. 비교

결과 문서에서 Phase 1 OpenAI baseline과 Jev를 비교한다.

| 항목 | OpenAI Baseline | Jev |
| --- | --- | --- |
| Cases | | |
| Correct | | |
| Accuracy | | |
| API Errors | | |
| Mean Latency | | |

측정 조건이나 수집 방식이 다른 항목은 직접 비교 가능한 값처럼 표시하지 않는다.

이번 Phase에서는 Jev가 더 우수하다는 결론을 미리 정하지 않는다.

실제 측정값만 기록한다.

## 10. Noul / Score

이번 Phase에서는 기본 구현 대상이 아니다.

아래 조건을 모두 만족할 때만 추가 실험을 허용한다.

- Phase 1 평가 데이터에 동일하게 비교할 수 있는 명확한 정답이 존재
- 현재 Phase 목적과 직접 관련
- Intent `Choice` 비교가 먼저 완료

조건을 만족하지 않으면 이후 Phase 후보로 남기고 구현하지 않는다.

## 11. 제외

이번 Phase에서는 구현하지 않는다.

- Jev 기반 실제 production routing
- confidence threshold 기반 자동 실행
- MCP Server
- Calculation Tool
- Web Search
- Decision Pack 실제 실행
- Multi-Agent
- 데이터베이스
- 사용자 인증
- 자동 구매 또는 자동 계약
- 평가 데이터 변경
- UI 기능 확장

기존 Phase 1 Web UI를 Jev용 화면으로 확장하지 않는다.

## 12. 테스트

최소 검증:

- 7개 Intent가 `Choice` 후보에 모두 포함되는지 확인
- 임의 Intent 생성 불가 확인
- Jev 응답을 기존 Intent 타입으로 변환 가능
- API Key 미설정 오류 처리
- TypeSafe API 오류 처리
- 평가 데이터 로딩
- 결과 schema 검증

외부 API가 필요한 테스트와 로컬 단위 테스트를 구분한다.

## 13. 기록할 결과

Phase 완료 후 아래 파일을 작성한다.

```text
docs/results/phase2-jev-decision-layer.md
```

최소 기록:

- 사용한 TypeSafe SDK 버전
- 사용한 Jev 모델 또는 공식 alias
- 평가 케이스 수
- Intent 정답 수
- Intent 정확도
- 실패 케이스
- 평균 지연 시간
- API 오류
- 확인 가능한 경우 usage / 비용
- Phase 1 baseline 비교
- Jev 후속 적용 여부 판단에 필요한 사실

평가 결과가 기대보다 낮아도 그대로 기록한다.

## 14. 구현 원칙

- `.project/plan.md` 범위 준수
- TypeSafe Skill 사용
- 공식 SDK와 공식 문서 우선
- Phase 1 평가 데이터 고정
- 모델 옵션은 코드에서 정의
- 계산 가능한 값은 코드에서 계산
- confidence를 정확도 보장으로 해석하지 않음
- 평가 없이 threshold 설정 금지
- 미래 Phase 기능 선반영 금지

## 15. 완료 기준

- Phase 1 실제 baseline 존재 확인
- `typesafe-sdk` 정상 설치 및 lock 반영
- `TYPESAFE_API_KEY` 기반 실제 Jev 호출 성공
- 동일 17개 케이스 평가 완료
- Intent 정답 수와 정확도 계산
- 실패 케이스 기록
- 지연 시간 측정
- Phase 1 baseline 비교 작성
- 관련 테스트 통과
- `docs/results/phase2-jev-decision-layer.md` 작성
- 실제 상태만 README 반영
- `uv lock --check` 성공
- `git diff --check` 성공
- `git status` 확인
- commit과 push 미실행
