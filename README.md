# SpendGuard

> 15개의 소비 문제를 실제 질문으로 해결하고, 필요한 경우에만 Search·MCP·Jev를 사용하는 소비 절감형 웹 애플리케이션

## 개요

SpendGuard는 범용 의사결정 플랫폼이 아닙니다.

사용자가 자주 겪는 구매·구독·계약·생활비 문제 15가지를 대상으로, 질문 한 건에 대해 가능한 범위까지 한 번에 비교·계산·조사하고 자연스러운 답변을 제공하는 프로젝트입니다.

목표 런타임:

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

현재 구현은 OpenAI Platform API를 제품 런타임에서 직접 호출하지 않습니다.

- `OPENAI_API_KEY` 미사용
- `OPENAI_MODEL` 미사용
- OpenAI Responses API 직접 호출 미사용
- OpenAI Agents SDK 사용자 요청 처리 미사용
- Platform API Web Search 미사용
- OpenAI Platform API fallback 미사용
- 기존 Codex CLI 인증 상태 재사용
- SpendGuard 실행 중 자동 로그인·OAuth·브라우저 인증 금지

## 제품 원칙

- 사용자가 이미 준 값을 다시 묻지 않음
- 정보가 일부 부족해도 합리적인 가정으로 유용한 답을 만들 수 있으면 중단하지 않음
- 사용자 사실과 시스템 가정을 구분
- 현재 가격·정책·혜택은 실제 조사 결과만 사용
- 결정적인 계산은 MCP 또는 코드로 처리
- Search·MCP 결과를 최종 답변의 실제 숫자와 비교에 반영
- 내부 routing, tool 이름, field id, raw JSON, diagnostic 비노출
- 자동 구매·결제·계약·해지·대출·보험 가입 실행 금지
- 테스트 하나를 맞추기 위한 scenario별 regex·if·하드코딩 금지

사용자에게 필요한 것은 내부 architecture가 아니라 결과입니다.

```text
판단
→ 중요한 숫자
→ 실제 비교
→ 절감 가능액
→ 가정과 불확실성
→ 필요한 경우 출처
```

## 돈 아껴주는 15개 시나리오

| No. | 시나리오 | 핵심 결과 |
| --- | --- | --- |
| 1 | 최저가 비교 | 현재 가격, 대안, 조건, 실제 차액 |
| 2 | 구독료 다이어트 | 월·연 비용, 중복·저활용 후보, 절감액 |
| 3 | 통신비 점검 | 현재 비용, 대안 요금제, 월·연 차액 |
| 4 | 보험 중복 찾기 | 보험료, 중복 가능 보장, 확인 필요 항목 |
| 5 | 카드 혜택 최적화 | 혜택, 조건, 연회비 반영 순혜택 |
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

15개는 제품 기능 목록입니다.

시나리오별 독립 pipeline, 복잡한 typed result schema, generic `DecisionAnswer` 중심 구조로 확장하지 않습니다.

## 런타임 역할

### Codex

- 사용자 질문 해석
- 복합 비교와 추론
- Search / MCP 사용 판단. Jev 후보는 평가 요청에서만 명시적으로 선택
- 결과 통합
- 최종 사용자 답변 생성

Codex runtime은 기존 Windows 사용자 환경에 저장된 ChatGPT 계정 인증을 재사용합니다.

SpendGuard가 `codex login`, OAuth, 브라우저 로그인을 실행하지 않습니다.

사용자 요청 처리 중 저장소 수정, Git 변경, 임의 개발 작업을 제품 기능으로 수행하지 않습니다.

### Search

현재 정보가 필요한 경우에만 사용합니다.

- 현재 가격
- 요금제
- 카드 혜택
- 항공권·숙박
- 판매·예약 조건
- 공개 견적·시세
- 제품 사양
- 공식 정책

원칙:

- 검색하지 않은 최신 정보 생성 금지
- 값·단위·조건·출처·확인 시점 유지
- 검색 결과를 최종 비교에 실제 사용
- 검색 실패를 일반적인 조언으로 숨기지 않음

### MCP / Calculation

재현 가능한 계산은 기존 FastMCP 도구를 사용합니다.

- `calculate_installment`
- `calculate_refinance`
- `calculate_usage_cost`
- `annualize_expense`
- `calculate_tco`
- `compare_costs`
- `calculate_repeated_cost` (단가 × 수량)
- `sum_costs` (항목 합계와 예산 잔액)

계산 결과를 LLM이 임의로 다시 계산하거나 변경하지 않습니다.

### Jev

Jev는 workflow gate나 router가 아닙니다.

반복되는 좁은 semantic if/else 후보에만 사용합니다.

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

## Baseline / Jev 비교

두 실행 모드를 동일한 15개 fixture에서 비교합니다.

```text
baseline
= Codex + Search + MCP

jev
= Codex + Search + MCP
+ 지정된 4개 narrow judgment의 Jev
```

Jev 모드에서도 최종 답변은 Codex가 생성합니다.

Jev의 판단은 Codex 입력에 전달하고 동일 분류를 반복하지 않도록 지시합니다. 이번 sparse 평가의 네 판단은 모두 정보 부족을 뜻하는 `unknown`이어서 생산 경로 적용 이득은 확인되지 않았습니다.

측정:

- scenario success
- 최종 답변 품질
- Search 사용 여부
- MCP 사용 여부
- Jev 사용 여부와 판단 결과
- Codex 실행 횟수
- Jev 요청 횟수
- E2E latency
- failure / timeout / retry

측정할 수 없는 ChatGPT 내부 token, model cost, Web Chat quota는 추정하지 않습니다.

Jev 적용 조건:

- 사전 정의한 judgment 기준 충족
- 최종 scenario success 저하 없음
- Codex 호출 수 또는 E2E latency 개선
- failure / retry 증가 없음

조건을 충족하지 못한 후보는 제품 경로에 적용하지 않습니다.

## 검증

주 검증 데이터는 `chapter_b_sparse_v1`의 정보가 적은 자연어 질문 15개입니다.

검증 원칙:

- 실제 `/api/decisions` 경로 사용
- Search 필요 질문은 실제 조사와 출처 반영 확인
- 계산 질문은 실제 MCP 호출과 결과 확인
- Jev 모드는 실제 Jev 호출 확인
- 이미 제공한 값 재질문 여부 확인
- 선택 정보 부족만으로 흐름 중단 금지
- 근거 없는 숫자·가격·조건 생성 금지
- 실패를 기록만 하고 종료하지 않고 공통 원인을 수정한 뒤 재검증
- 평가 criterion을 결과에 맞춰 변경하지 않음
- 실행하지 않은 테스트나 측정값 기록 금지

대표 기능 검증:

```text
일반 추론
Search
MCP
Search + MCP
Jev 후보
→ 15개 sparse 전체
```

## 기술 구성

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

## 실행

Python 3.13과 `uv`를 사용합니다.

```powershell
codex.cmd login status
codex.cmd exec "Reply with only: OK"
uv sync --all-groups
uv run uvicorn spendguard.main:app --host 127.0.0.1 --port 8000
```

브라우저:

```text
http://127.0.0.1:8000
```

현재 런타임에서는 `.env`와 `.env.example`에서 아래 변수를 사용하지 않습니다.

```text
OPENAI_API_KEY
OPENAI_MODEL
```

Jev를 사용하는 경우 필요한 TypeSafe 설정만 별도로 유지합니다.

## 2026-09-24 실측 상태

- 실제 `/api/decisions` 15개 sparse 평가: baseline 8/15, Jev 10/15 criterion 통과. baseline 자동차 1건은 과거 비정상 종료이며 원인은 보존된 stderr가 없어 `unknown`입니다. 이후 Jev 평가의 자동차 요청은 답변까지 도달했습니다.
- 공통 조사·비교 지침 수정 후 카드 혜택과 가격 협상에서 실제 Search가 수행됐습니다. 수정 전 전체 평가와 수정 후 관련 4건 재검증은 별도 파일로 보존합니다.
- Jev는 지정된 네 후보에서만 호출됐고 네 결과 모두 `unknown`이었습니다. 총 실행 시간은 baseline 675.4초, Jev 758.7초였으며 Jev 도입 이득은 입증되지 않아 기본 UI는 baseline입니다.
- 실제 브라우저에서 질문 제출 후 단일 답변 카드 렌더링을 확인했습니다. 사용자 화면에는 실행 trace가 나오지 않습니다.
- 원시 trace, 수동 검토, criterion 점수와 제약은 [현재 런타임 결과](docs/results/chapter-b-codex-runtime-mvp.md)에 기록했습니다. 과거 Agents/Responses 결과는 아래의 역사 기록입니다.

## 기존 이력

Phase 0~7, Chapter A, Track A 결과는 historical result로 보존합니다.

과거 OpenAI Agents SDK / Responses API 기반 측정은 당시 실제 구현 결과이며, 현재 목표 런타임의 근거로 재해석하지 않습니다.

Track A에서 확인된 방향:

- broad Intent router로 Jev 사용하지 않음
- 추가 정보 필요 여부를 Jev에 맡기지 않음
- Search 필요 여부를 Jev에 맡기지 않음
- Jev는 좁은 semantic judgment만 재평가

## 범위 제외

- 범용 AI 의사결정 플랫폼
- scenario별 독립 workflow
- scenario별 복잡한 typed result schema
- generic `DecisionAnswer` 중심 재구성
- blocking-field engine 중심 설계
- 모든 요청에 Jev gate 적용
- 자동 구매
- 자동 결제
- 자동 계약
- 자동 구독 해지
- 은행·카드 계정 직접 연동
- 투자 자문
- 보험·대출 상품 가입 결정

보험·대출 영역은 비용 비교와 정보 정리에 한정합니다.

## 프로젝트 구조

```text
spendguard-agent/
├── .agents/
├── .project/
├── docs/
│   ├── instructions/
│   └── results/
├── evals/
├── scripts/
├── src/
├── tests/
├── AGENTS.md
├── DESIGN.md
├── README.md
├── pyproject.toml
└── uv.lock
```

## 문서 역할

| 문서 | 역할 |
| --- | --- |
| `.project/plan.md` | 프로젝트 전체 기획 기준 |
| `AGENTS.md` | 저장소 공통 작업 규칙 |
| `DESIGN.md` | Web UI 디자인 기준 |
| `docs/instructions/*` | 현재 작업 범위와 완료 기준 |
| `docs/results/*` | 실제 구현·검증 결과 |

구현과 검증은 기능 단위로 완료한 뒤 커밋합니다.

서로 다른 기능을 하나의 커밋에 섞지 않으며, 사용자의 명시적 지시 없이 push하지 않습니다.
