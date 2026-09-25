# SpendGuard 프로젝트 기획서

> 15개의 소비 문제를 실제 질문으로 해결하고, Codex·Search·MCP·Jev를 역할별로 분리해 실제 제품 흐름에서 검증하는 프로젝트

## 1. 목표

SpendGuard는 범용 의사결정 플랫폼이 아니라 **돈을 아끼는 15개 소비 시나리오를 실제로 동작하게 만드는 독립 웹 애플리케이션**입니다.

사용자 질문 한 건에 대해 가능한 범위까지 한 번에 판단하고 답변합니다.

현재 제품 구조:

```text
SpendGuard Web
→ FastAPI
→ Codex / Code
   ├─ 사용자 사실 추출
   ├─ 필요한 현재 정보 Search
   ├─ MCP deterministic calculation
   ├─ SpendGuard state 구성
   ├─ Jev가 필요한 경우 판단별 최소 입력으로 Decision Bundle 실행
   └─ FastAPI가 Jev 결과를 세션 state에 저장하고 Code로 판단 조합
→ Codex가 결과를 반영해 최종 설명 작성
→ FastAPI가 확정 계산값과 답변의 금액 일치 확인
→ 자연스러운 최종 답변
```

Jev는 단순한 yes/no gate가 아니라, **SpendGuard 서버가 보관한 state에서 각 판단에 필요한 최소 사실만 받아 작은 semantic judgment를 수행하는 decision layer**로 사용합니다. 현재 첫 요청의 Search·MCP 사용과 최종 작성은 Codex 실행 안에서 진행합니다.

현재 제품 런타임에서는 OpenAI Platform API를 사용하지 않습니다.

- `OPENAI_API_KEY` 미사용
- `OPENAI_MODEL` 미사용
- OpenAI Responses API 직접 호출 미사용
- OpenAI Agents SDK 사용자 요청 처리 미사용
- SpendGuard의 Platform API Web Search 직접 호출 미사용
- OpenAI Platform API fallback 미사용

Codex는 현재 Windows 사용자 환경에 저장된 ChatGPT 계정 인증을 재사용합니다.

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
- Jev에는 계산값이나 검색되지 않은 사실을 만들게 하지 않음
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

시나리오 이름은 사용자 탐색용입니다.

15개의 독립 pipeline이나 별도 answer schema를 만들지 않습니다.

---

## 4. 런타임 역할

### Codex / Code

Codex와 Code는 Jev가 판단할 수 있는 상태를 먼저 만듭니다.

담당:

- 사용자 질문 해석
- 사용자 사실 추출
- 수정 가능한 가정 구성
- Search 필요 여부 판단
- MCP 필요 여부 판단
- Search / MCP 실행
- SpendGuard state 구성
- Jev 판단 결과와 계산·검색 근거 통합
- 최종 사용자 답변 작성

Codex runtime은 개발 작업용 Codex 세션과 역할을 구분합니다.

사용자 요청 처리 중 저장소 수정, Git 변경, 임의 개발 작업을 제품 기능으로 사용하지 않습니다.

제품 요청용 Codex는 별도 최소 runtime 작업 디렉터리에서 실행하며, 기본 모델은 `gpt-6-luna`, reasoning effort는 `low`입니다. 후속 질문은 서버에 살아 있는 thread가 있으면 `codex exec resume`을 사용합니다. 최종 응답은 `answer`, 최대 3개의 `suggested_followups`, `sources`로 전달하고 실행 지표는 별도 metadata에 둡니다. 추천 질문 생성에 별도 실행이나 도구 호출을 추가하지 않습니다.

### Search

현재 가격, 요금, 혜택, 항공권, 숙박, 견적, 정책처럼 최신 정보가 필요한 경우에만 사용합니다.

- 검색하지 않은 최신 정보 생성 금지
- 값·단위·조건·출처·확인 시점 유지
- 검색 결과를 SpendGuard state와 최종 비교에 실제 사용
- 검색 실패를 일반론 답변으로 숨기지 않음
- 사용자 요청의 live Search는 최대 4회 또는 Search 단계 60초 중 먼저 도달한 상한에서 멈춤
- 기존 근거로 답할 수 있는 후속 질문은 Search를 다시 실행하지 않음

### MCP

결정적인 계산은 FastMCP 도구를 사용합니다.

- `calculate_installment`
- `calculate_refinance`
- `calculate_usage_cost`
- `annualize_expense`
- `calculate_tco`
- `compare_costs`
- `calculate_repeated_cost`
- `sum_costs`

계산 결과는 확정값으로 사용하며, FastAPI는 MCP 계산 trace를 다시 검증합니다. 최종 답변의 결정론적 금액 불일치는 공통 숫자 검증 경로에서 보정하거나 답변을 반환하지 않습니다. Codex와 Jev는 확정값을 임의로 변경하지 않습니다.

### SpendGuard state

Jev 호출 전에 사용자 사실·검색 결과·계산 결과를 하나의 판단 상태로 구성합니다.

현재 세션 state의 주요 필드:

```text
SpendGuard state
├─ user_facts
├─ assumptions
├─ current_facts
├─ alternatives
├─ calculations
├─ judgment_facts
├─ jev_results
└─ sources
```

state는 사용자에게 노출하는 공통 answer schema가 아닙니다.

후속 질문에서 기존 judgment 입력과 새 사실을 비교하는 내부 상태입니다. FastAPI는 명시적으로 표시된 금액 사실을 결정론적으로 추출해 변경 판단만 갱신하고, 그 밖의 새 관련 사실은 Codex의 판단 도구 입력으로 받을 수 있습니다. TypeSafe Jev에는 전체 state나 원문 질문·대화·출처 URL을 보내지 않고, 판단별로 허용된 숫자·불리언·범주 값만 보냅니다.

### 최근 소비 판단 기록

성공적으로 표시된 결과만 브라우저 `localStorage`에 최대 30건 저장합니다. 기록에는 첫 질문·답변, 최근 후속 질문·답변, 출처와 추천 질문 등 화면 복원에 필요한 값만 남깁니다. `#history`에서 목록, `#history/<record-id>`에서 상세를 열고 개별·전체 삭제를 지원합니다.

기록 조회는 서버의 Codex thread 복원이 아닙니다. 저장된 기록에서 후속 질문을 시작하면 브라우저가 저장된 질문·답변을 문맥으로 보내 새 서버 대화를 시작하고, 같은 소비 판단 기록을 갱신합니다. 서버에 살아 있는 활성 대화의 후속 질문만 기존 thread를 resume합니다. 별도 서버 영구 저장소나 로그인은 없습니다.

---

## 5. Jev Decision Layer

Jev는 workflow gate나 전체 scenario router가 아닙니다.

Jev의 역할은 **SpendGuard state에서 계산이나 사실 조회로 확정할 수 없는 작은 semantic judgment를 빠르게 수행하는 것**입니다.

### Jev primitive

Jev 판단은 문제 성격에 따라 아래 형태를 사용합니다.

- `Noul` — yes/no 성격의 semantic judgment
- `Score` — 필요도·부담·가치·중복도 같은 정도 평가
- `Choice` — 코드에서 미리 정의한 선택지 중 하나 선택

Jev가 새로운 제품 선택지나 금액을 임의로 생성하게 하지 않습니다.

### 구매 판단 Decision Bundle

구매 관련 질문에서 판단 가능한 입력이 있으면 필요한 판단들을 한 번의 Jev 요청으로 묶어 수행합니다. 각 judgment의 입력은 서로 분리된 최소 사실만 포함하며, 근거가 부족한 판단은 `unknown`으로 둡니다.

```text
Codex / Code
→ 사용자 사실 추출
→ 필요한 현재 가격 Search
→ MCP 계산
→ SpendGuard state 구성

필요한 judgment만 한 Jev 요청으로 호출
├─ Noul: 지금 교체 필요성이 충분한가?
├─ Noul: 현재 구매가 생활비 여유를 훼손하는가?
├─ Noul: 구매를 미뤄도 사용상 손실이 작은가?
├─ Score: 현재 기기의 교체 필요도
├─ Score: 구매 부담 수준
├─ Score: 기존 제품 대비 업그레이드 가치
├─ Choice: buy_now / wait / buy_cheaper_variant
└─ Choice: 가장 중요한 판단 요인
       price / replacement_need / feature_gain / cashflow

→ Code가 결정 조합
→ Codex는 설명 작성
```

Jev 도구는 read-only 평가 결과만 반환합니다. FastAPI가 그 결과를 세션 state에 저장하고, Code가 최종 판단 흐름을 조합합니다. 후속 질문에서 판단 입력이 같으면 결과를 재사용하고, 달라진 입력에 영향을 받는 judgment만 다시 요청합니다. 새 평가가 없으면 Jev 요청은 0회입니다.

Codex는 Jev가 이미 수행한 동일 semantic judgment를 다시 처음부터 수행하지 않도록 합니다.

### 재사용 가능한 Jev 판단과 확장 후보

Jev는 시나리오 이름보다 **판단 종류**를 기준으로 재사용합니다.

| 판단 | 기본 primitive | 활용 |
| --- | --- | --- |
| 지출 필요성이 높은가 | Score / Noul | 충동구매, 구매 전 최종 심사 |
| 현재 현금흐름 부담이 큰가 | Score / Noul | 구매, 여행, 구독, 카드 |
| 미뤄도 손실이 작은가 | Noul | 구매, 교체, 계약 |
| 대체 가능성이 높은가 | Score | 구매, 구독, 장보기 |
| 가격 대비 효용이 높은가 | Score | 구매, 카드, 통신 |
| 기존 대비 업그레이드 가치가 높은가 | Score | 제품 교체 |
| 기능 중복도가 높은가 | Score | 구독, 보험 |
| 저활용 상태인가 | Noul / Score | 구독, 반복 지출 |
| 만족도 손실이 낮은 절감인가 | Score / Noul | 연간 새는 돈, 장보기 |
| 추가 검토가 필요한 항목인가 | Noul | 견적 |
| 어느 대안이 현재 조건에 더 적합한가 | Choice | 구매, 여행, 카드 |
| 가장 중요한 결정 요인은 무엇인가 | Choice | 구매, 계약, 비교 |

시나리오마다 새로운 Jev 모델 구조를 만들지 않습니다.

현재 구매·교체 Decision Bundle을 구현했습니다. 나머지 판단 종류는 동일한 방식으로 확장할 후보이며, 구현 완료로 간주하지 않습니다.

### Jev가 맡지 않는 역할

- 현재 가격 검색
- 사실 검증
- 금액 계산
- 이자 계산
- 단위 변환
- 전체 scenario routing
- 자동 결제·계약·해지
- 최종 자연어 답변 작성

---

## 6. Baseline / Jev 비교

제품에서 Jev를 실제로 활용하되, 효과를 검증하기 위해 baseline을 유지합니다.

```text
baseline
= Codex + Search + MCP
  → Codex가 semantic judgment와 설명을 모두 수행

jev
= Codex / Code + Search + MCP
  → SpendGuard state
  → Jev Decision Bundle
  → Code decision composition
  → Codex explanation
```

비교의 핵심은 Jev 호출 자체가 아닙니다.

Jev가 Codex가 하던 semantic judgment를 실제로 대체하는지 확인합니다.

측정:

- scenario success
- 최종 답변 품질
- Jev judgment 정확도
- Jev abstain / unknown
- Codex 실행 횟수
- Jev 요청 횟수
- Search 사용 횟수
- MCP 사용 횟수
- E2E latency
- failure / timeout / retry

측정할 수 없는 ChatGPT 내부 token, 내부 model cost, Web Chat quota는 추정하지 않습니다.

Jev 적용 판단:

- judgment 품질이 사전 정의 기준 충족
- 최종 답변 품질 저하 없음
- Codex가 동일 judgment를 반복하지 않음
- Codex 실행량 또는 E2E latency에서 의미 있는 개선
- failure / retry 증가 없음

Jev가 이득을 만들지 못한 judgment는 그대로 기록하고 다른 역할로 억지 확장하지 않습니다.

---

## 7. Jev 검증 시나리오

정보가 너무 부족한 sparse 질문만으로 Jev 성능을 판단하지 않습니다.

Jev 판단에 필요한 candidate 정보가 실제로 들어 있는 대표 질문을 함께 사용합니다.

### 구매 / 교체

```text
기존 제품 사용 기간
현재 불편
새 제품 가격
보유 현금
고정 지출
가까운 예정 지출
대체 모델
기능 차이
```

검증:

- 교체 필요성
- 현금흐름 부담
- 대기 가능성
- 업그레이드 가치
- buy / wait / cheaper variant
- 주요 판단 요인

### 구독료 다이어트

```text
구독명
월 비용
사용 빈도
주요 사용 목적
겹치는 서비스
```

검증:

- 저활용 여부
- 기능 중복도
- 해지 시 만족도 영향
- 상세 검토 우선순위

### 견적서 바가지 체크

```text
항목명
수량
단가
공개 가격
필수 여부
견적 조건
```

검증:

- 추가 검토 필요 여부
- 가격 이상도
- 협상 우선순위

### 연간 새는 돈 찾기

```text
지출 항목
월 비용
사용 빈도
만족도
대체 가능성
```

검증:

- 절감 가능성
- 만족도 손실
- 대체 가능성
- 절감 우선순위

기존 `chapter_b_sparse_v1`은 사용자 UX와 전체 답변 검증에 유지합니다.

Jev 자체 평가는 판단 가능한 정보가 포함된 fixture를 별도로 사용합니다.

---

## 8. 검증 전략

### 제품 검증

실제 `/api/decisions` 경로로 확인합니다.

- 일반 추론
- Search
- MCP
- Search + MCP
- Jev Decision Bundle
- 후속 질문
- 사용 한도 오류 처리
- 사용자 결과 렌더링
- 결정론적 금액 계산 trace와 최종 답변의 숫자 일치
- 최근 소비 판단 기록의 저장·조회·삭제·새 대화 후속 질문

원칙:

- 이미 제공한 값 재질문 금지
- 선택 정보 부족만으로 흐름 중단 금지
- 근거 없는 숫자·가격·조건 생성 금지
- Search와 MCP 결과의 최종 답변 반영 확인
- 실패를 기록만 하고 종료하지 않고 공통 원인을 수정 후 재검증
- 실행하지 않은 테스트나 측정값 기록 금지

### Jev 검증

동일한 실제 질문을 baseline과 Jev 경로에서 비교합니다.

```text
동일 user facts
동일 Search facts
동일 MCP results
동일 alternatives
→ baseline
vs
→ Jev Decision Bundle
```

Jev에 유리하도록 검색 결과나 계산 결과를 다르게 주지 않습니다.

---

## 9. 기존 이력

Phase 0~7, Chapter A, Track A 결과는 historical result로 보존합니다.

과거 OpenAI Agents SDK / Responses API 기반 측정도 당시 구현 결과로 유지합니다.

Track A에서 확인된 실패를 그대로 반복하지 않습니다.

- broad Intent router로 Jev 사용하지 않음
- 추가 정보 필요 여부를 Jev에 맡기지 않음
- Search 필요 여부를 Jev에 맡기지 않음
- Jev 호출 때문에 Codex 실행 횟수를 늘리지 않음
- 질문 전체를 근거 없이 한 번 분류해 `unknown`만 만드는 구조를 기본 Jev 활용으로 사용하지 않음

과도한 범용화 방향은 계속 제외합니다.

- 범용 AI 의사결정 플랫폼
- scenario별 독립 workflow
- scenario별 복잡한 typed result schema
- generic DecisionAnswer 중심 재구성
- blocking-field engine 중심 설계
- 모든 요청에 동일 Jev gate 적용

---

## 10. 기술 스택

| 구분 | 기술 |
| --- | --- |
| Language | Python 3.13 |
| API | FastAPI |
| Runtime reasoning | Codex CLI authenticated with ChatGPT account |
| Current information | Codex Search |
| Calculation | FastMCP 4.0.0 |
| Decision layer | TypeSafe Jev |
| Validation | Pydantic |
| Test | pytest / E2E |
| Frontend | HTML / CSS / JavaScript |
| Client history | Browser localStorage |

현재 제품 설정과 예제 환경 변수에서 `OPENAI_API_KEY`, `OPENAI_MODEL`을 사용하지 않습니다.

SpendGuard runtime은 별도 Codex 실행 설정을 사용할 수 있지만 사용자의 기존 인증 상태를 재사용합니다.

---

## 11. 현재 구현 상태와 남은 검증

현재 `/api/decisions`는 baseline과 Jev 모드를 유지합니다. 웹 UI는 Jev 모드를 요청하며, 제품 요청용 Codex CLI가 필요한 Search와 MCP 계산을 수행하고 최종 답변을 작성합니다. 별도 `render` 실험 코드가 있어도 현재 웹 요청 경로는 render-only 구조가 아닙니다.

구현된 공통 경로:

1. 최소 runtime 작업 디렉터리에서 `gpt-6-luna` / low reasoning으로 Codex 실행, Search 4회·60초 상한 적용
2. 구매·교체 판단에서 허용된 최소 사실로 Jev `Noul` / `Score` / `Choice` bundle 평가, FastAPI가 결과를 세션 state에 저장
3. 후속 질문의 명시적 금액 사실을 FastAPI에서 비교해 변경된 judgment만 재평가하고, 동일한 판단은 재사용
4. 살아 있는 Codex thread는 `exec resume`으로 이어받고 기존 근거와 출처를 재사용
5. MCP 계산 trace 검증과 최종 답변의 공통 금액 일치 보정, `answer`·`suggested_followups`·`sources` 반환
6. Codex 사용 한도는 HTTP 429와 `codex_usage_limit`로 전달
7. 성공한 소비 판단을 브라우저 `localStorage`에 최근 30건까지 저장하고 URL로 조회·삭제·새 대화 후속 질문 시작

남은 검증은 동일 질문의 baseline/Jev 비교에서 판단 품질, Codex 실행량, 응답 시간과 실패율을 실제로 확인하는 것입니다. 구독·견적·연간 지출 등으로 Jev 판단을 확대하는 일은 현재 구현 범위와 구분합니다. 측정하지 않은 개선 수치나 완료 여부는 결과로 기록하지 않습니다.

기능 단위로 구현·검증 후 커밋하며, 서로 다른 기능을 한 커밋에 섞거나 사용자 지시 없이 push하지 않습니다.
