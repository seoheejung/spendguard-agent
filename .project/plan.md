# SpendGuard 프로젝트 기획서

> 15개의 소비 문제를 실제 질문으로 해결하고, Codex·Search·MCP·Jev의 역할을 필요한 범위로 제한해 검증하는 프로젝트

## 1. 목표

SpendGuard는 범용 의사결정 플랫폼이 아니라 **돈을 아끼는 15개 소비 시나리오를 실제로 동작하게 만드는 독립 웹 애플리케이션**입니다.

사용자 질문 한 건에 대해 가능한 범위까지 한 번에 판단하고 답변합니다.

```text
SpendGuard Web
→ FastAPI
→ Codex runtime
   ├─ 자연어 이해 및 복합 추론
   ├─ 현재 정보 조사
   ├─ SpendGuard MCP deterministic tools
   └─ optional Jev narrow judgment
→ 자연스러운 최종 답변
```

현재 제품 런타임에서는 OpenAI Platform API를 사용하지 않습니다.

- `OPENAI_API_KEY` 미사용
- `OPENAI_MODEL` 미사용
- OpenAI Responses API 직접 호출 미사용
- OpenAI Agents SDK 사용자 요청 처리 미사용
- SpendGuard의 Platform API Web Search 직접 호출 미사용 (Codex CLI의 인증된 검색 기능 사용)
- OpenAI Platform API fallback 미사용

Codex는 현재 Windows 사용자 환경에 이미 저장된 ChatGPT 계정 인증을 재사용합니다.

SpendGuard 실행 중 `codex login`, OAuth 시작, 브라우저 로그인창 실행을 하지 않습니다.

---

## 2. 제품 원칙

- 사용자가 준 값을 다시 묻지 않음
- 정보가 일부 부족해도 합리적인 가정으로 유용한 답을 만들 수 있으면 중단하지 않음
- 사용자 사실과 시스템 가정을 구분
- 추가 질문은 가정으로도 유용한 답을 만들 수 없을 때만 사용
- 현재 가격·정책·혜택은 실제 조사 결과만 사용
- 결정적인 계산은 MCP 또는 코드로 처리
- 검색·계산 결과를 최종 답변의 실제 비교와 숫자에 반영
- 내부 routing, tool 이름, field id, raw JSON, diagnostic 비노출
- 자동 구매·결제·계약·해지·대출·보험 가입 실행 금지
- 테스트 하나를 통과시키기 위한 scenario별 regex·if·하드코딩 금지

사용자 결과는 복잡한 공통 schema보다 자연스러운 답변을 우선합니다.

```text
판단
→ 중요한 숫자
→ 실제 비교
→ 절감 가능액
→ 가정과 불확실성
→ 필요한 경우 출처
```

---

## 3. 15개 핵심 시나리오

| No. | 시나리오 | 핵심 결과 |
| --- | --- | --- |
| 1 | 최저가 비교 | 현재 가격, 대안, 조건, 실제 차액 |
| 2 | 구독료 다이어트 | 월·연 비용, 중복·저활용 후보, 절감액 |
| 3 | 통신비 점검 | 현재 비용, 대안 요금제, 월·연 차액 |
| 4 | 보험 중복 찾기 | 보험료, 중복 가능 보장, 확인 필요 항목 |
| 5 | 카드 혜택 최적화 | 혜택, 한도·조건, 연회비 반영 순혜택 |
| 6 | 충동구매 방지 | 사용당 비용, 대체재, 기회비용 |
| 7 | 장보기 예산 절감 | 식단, 장보기 목록, 총액, 예산 잔액 |
| 8 | 여행비 최적화 | 주요 비용, 대안 조합, 총비용 차이 |
| 9 | 자동차 유지비 계산 | 항목별 비용, 5년 TCO, 월평균 |
| 10 | 할부 vs 일시불 | 월 납부액, 총이자, 총비용, 차액 |
| 11 | 대출 갈아타기 계산 | 기존·신규 총이자, 수수료, 순절감액 |
| 12 | 견적서 바가지 체크 | 합계, 공개 가격 비교, 검토·협상 후보 |
| 13 | 가격 협상 준비 | 비교 근거, 협상 항목, 실제 협상 문장 |
| 14 | 연간 새는 돈 찾기 | 반복 지출 연환산, 절감 후보, 연간 절약액 |
| 15 | 구매 전 최종 심사 | 지금 구매·대기·중고·대체품 비용 비교 |

시나리오 이름은 사용자 탐색용입니다. 15개의 독립 pipeline이나 별도 answer schema를 만들지 않습니다.

---

## 4. 런타임 역할

### Codex

- 사용자 질문 해석
- 복합 비교와 추론
- Search / MCP 사용 판단; Jev 후보는 평가 요청이 명시적으로 선택
- 결과 통합
- 최종 답변 생성

Codex runtime은 개발 작업용 Codex 세션과 역할을 구분합니다.

사용자 요청 처리 중 저장소 수정, Git 변경, 임의 명령 실행을 제품 기능으로 사용하지 않습니다.

### Search

현재 가격, 요금, 혜택, 항공권, 숙박, 견적, 정책처럼 최신 정보가 필요한 경우에만 사용합니다.

- 검색하지 않은 최신 정보 생성 금지
- 값·단위·조건·출처·확인 시점 유지
- 검색 결과를 최종 비교에 실제 사용
- 검색 실패를 일반론 답변으로 숨기지 않음

### MCP

결정적인 계산은 기존 FastMCP 도구를 사용합니다.

- `calculate_installment`
- `calculate_refinance`
- `calculate_usage_cost`
- `annualize_expense`
- `calculate_tco`
- `compare_costs`
- `calculate_repeated_cost`
- `sum_costs`

계산 결과를 LLM이 임의로 다시 계산하거나 변경하지 않습니다.

### Jev

Jev는 workflow gate나 router가 아니라 반복되는 좁은 semantic if/else 후보입니다.

현재 후보는 네 개만 유지합니다.

| 시나리오 | Jev 판단 |
| --- | --- |
| 구독료 다이어트 | 중복·저활용 절감 후보인가 |
| 견적서 바가지 체크 | 추가 검토가 필요한 항목인가 |
| 연간 새는 돈 찾기 | 만족도 영향이 낮은 절감 후보인가 |
| 구매 전 최종 심사 | 상세 비교할 가치가 있는 대안인가 |

Jev가 맡지 않는 역할:

- 전체 scenario routing
- Search 필요 여부
- 추가 질문 여부
- 금액 계산
- 최종 사용자 결론

---

## 5. Baseline / Jev 비교

동일한 15개 fixture에서 두 모드를 비교합니다.

```text
baseline
= Codex + Search + MCP

jev
= Codex + Search + MCP
+ 지정된 4개 narrow judgment의 Jev
```

Jev 모드에서도 최종 답변은 Codex가 생성합니다.

Jev를 추가 호출하는 것 자체가 목적이 아닙니다. Jev가 담당한 판단을 Codex가 다시 반복하지 않도록 구성합니다.

측정:

- scenario success
- 최종 답변 품질
- 실제 Search 사용 여부
- 실제 MCP 사용 여부
- Jev 사용 여부와 판단 결과
- Codex 실행 횟수
- Jev 요청 횟수
- E2E latency
- failure / timeout / retry

측정할 수 없는 ChatGPT 내부 token, 내부 model cost, Web Chat quota는 추정하지 않습니다.

Jev 적용 조건:

- 사전 정의한 judgment 기준 충족
- 최종 scenario success 저하 없음
- Codex 호출 수 또는 E2E latency 개선
- failure / retry 증가 없음

조건을 충족하지 못한 후보는 제품 경로에 적용하지 않습니다.

---

## 6. 검증 전략

주 검증 데이터는 `chapter_b_sparse_v1`의 정보가 적은 자연어 질문 15개입니다.

기존 criterion을 결과에 맞춰 수정하지 않습니다.

검증 원칙:

- 실제 `/api/decisions` 경로 사용
- Search 필요 질문은 실제 조사와 출처 반영 확인
- 계산 질문은 실제 MCP 호출과 결과 확인
- Jev 모드는 실제 Jev 호출 확인
- 이미 제공한 값 재질문 여부 확인
- 선택 정보 부족만으로 흐름 중단 금지
- 근거 없는 숫자·가격·조건 생성 금지
- 실패를 기록만 하고 종료하지 않고 공통 원인을 수정한 뒤 재검증
- 실행하지 않은 테스트나 측정값 기록 금지

대표 기능 검증 후 15개 전체를 실행합니다.

```text
일반 추론
Search
MCP
Search + MCP
Jev 후보
→ 15개 sparse 전체
```

---

## 7. 기존 이력

Phase 0~7, Chapter A, Track A 결과는 historical result로 보존합니다.

과거 OpenAI Agents SDK / Responses API 기반 측정도 당시 구현 결과로 유지합니다.

현재 제품 런타임의 근거로 재사용하지 않습니다.

Track A에서 확인된 방향:

- broad Intent router로 Jev 사용하지 않음
- 추가 정보 필요 여부를 Jev에 맡기지 않음
- Search 필요 여부를 Jev에 맡기지 않음
- Jev는 좁은 semantic judgment만 재평가

과도한 범용화 방향은 계속 제외합니다.

- 범용 AI 의사결정 플랫폼
- scenario별 독립 workflow
- scenario별 복잡한 typed result schema
- generic DecisionAnswer 중심 재구성
- blocking-field engine 중심 설계
- 모든 요청에 Jev gate 적용

---

## 8. 기술 스택

| 구분 | 기술 |
| --- | --- |
| Language | Python 3.13 |
| API | FastAPI |
| Runtime reasoning | Codex CLI authenticated with ChatGPT account |
| Calculation | FastMCP 4.0.0 |
| Decision model evaluation | TypeSafe Jev |
| Validation | Pydantic |
| Test | pytest / E2E |
| Frontend | HTML / CSS / JavaScript |

현재 제품 설정과 예제 환경 변수에서 `OPENAI_API_KEY`, `OPENAI_MODEL`을 사용하지 않습니다.

Codex 모델과 인증은 SpendGuard env가 아니라 기존 Codex 설정과 사용자 인증 상태를 사용합니다.

---

## 9. 현재 작업 및 실측

현재 구현은 아래 범위로 전환했습니다. 실측 결과와 남은 실패는 [Chapter B Codex 런타임 결과](../docs/results/chapter-b-codex-runtime-mvp.md)에 기록합니다.

1. OpenAI Platform API 기반 활성 경로 제거
2. 기존 Codex 인증 재사용 방식으로 FastAPI → Codex 연결
3. `OPENAI_API_KEY`, `OPENAI_MODEL` 제거
4. 실제 현재 정보 조사 경로 연결
5. 기존 MCP 계산 도구 연결
6. Jev 4개 narrow judgment 재구성
7. baseline / jev 실행 모드 구현
8. 중복된 사용자 결과 UI 정리
9. evaluator를 새 runtime에 맞게 수정
10. 대표 기능 실제 검증
11. 15개 sparse baseline / Jev 실행 및 문제 수정
12. README·instructions·results·env 문서 갱신

완료 기준:

```text
OPENAI_API_KEY 없음
OPENAI_MODEL 없음
OpenAI Platform 직접 호출 없음
기존 Codex 인증 재사용
자동 로그인 없음
Codex 실제 추론
필요 시 실제 Search
필요 시 실제 MCP 계산
Jev 후보 실제 호출
자연스러운 최종 답변
15개 sparse 전체 검증
baseline / Jev 비교
관련 테스트 통과
문서와 구현 일치
```

기능 단위로 구현·검증 후 커밋합니다.

서로 다른 기능을 하나의 커밋에 섞지 않으며, 사용자의 명시적 지시 없이 push하지 않습니다.
