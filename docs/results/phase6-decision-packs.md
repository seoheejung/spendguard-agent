# Phase 6 Decision Packs 결과

## 구현

- `POST /api/decisions`가 기존 OpenAI Agent 분석 결과의 structured intent를 코드-owned Pack mapping으로 연결한다.
- 지원 Pack: Purchase, Recurring Cost, Finance Cost, Ownership Cost, Quote Audit, Budget Optimization.
- 각 Pack의 필수 입력은 `REQUIRED_FIELDS`에서 관리한다. 누락되면 `needs_input` 결과와 필요한 필드만 반환하며 계산·구매 결론을 추정하지 않는다.
- 계산이 필요한 명시적 입력이 있을 때만 기존 stdio MCP Tool(`calculate_installment`, `calculate_refinance`, `calculate_usage_cost`, `annualize_expense`, `calculate_tco`, `compare_costs`)을 재사용한다. Tool 오류는 `tool_error`로 반환하고 확정 결론을 만들지 않는다.
- Phase 5의 `AnalysisResult.external_facts`를 `sources`로 그대로 전달한다. facts, assumptions, calculations, options, risks, next actions, sources는 별도 필드로 유지한다.
- Jev는 production routing에 연결하지 않았다. Phase 2의 `ambiguous-001` 고-confidence 오분류 결과 때문에 confidence 단독 routing을 사용하지 않으며, Pack routing fallback은 Agent intent가 `unknown`이면 Pack 실행을 하지 않고 추가 맥락을 요청한다.
- Decision Workspace에 공통 Decision Pack form과 데이터 기반 Decision Result Card를 추가했다. Pack별 페이지를 복제하지 않았다.

## 초기 절약 시나리오 Coverage

| 시나리오 | Pack | 검증 경로 |
| --- | --- | --- |
| 최저가 비교 | Purchase | 외부 출처·선택지 비용 비교 |
| 구독료 다이어트 | Recurring Cost | 반복 비용 연간 환산·선택지 비교 |
| 통신비 점검 | Recurring Cost | 현재 정보 출처·반복 비용 환산 |
| 보험 중복 찾기 | Recurring Cost | 사용자 제공 비용·선택지 비교 |
| 카드 혜택 최적화 | Budget Optimization | 사용자 제공 예산·선택지 비교 |
| 충동구매 방지 | Purchase | 필수 입력·사용당 비용 |
| 장보기 예산 절감 | Budget Optimization | 예산·선택지 비교 |
| 여행비 최적화 | Budget Optimization | 현재 정보 출처·예산 선택지 비교 |
| 자동차 유지비 계산 | Ownership Cost | TCO MCP 계산 |
| 할부 vs 일시불 | Finance Cost | 할부 MCP 계산 |
| 대출 갈아타기 계산 | Finance Cost | 대환 MCP 계산 |
| 견적서 바가지 체크 | Quote Audit | 견적 항목·선택지 비용 비교 |
| 가격 협상 준비 | Quote Audit | 외부 출처·선택지 비용 비교 |
| 연간 새는 돈 찾기 | Budget Optimization | 반복 지출 연간 환산 |
| 구매 전 최종 심사 | Purchase | 필수 입력·선택지 비교 |

테스트는 시나리오 이름 문자열로 routing하지 않는다. 각 fixture의 intent, required data, research 결과, 계산 입력에 따라 동일 workflow를 실행한다.

## 실제 외부 호출 검증

- 2026-09-19에 설정된 로컬 OpenAI 자격 증명으로 Apple iPhone의 현재 한국 공식 판매 가격 비교 질문을 실행했다. API key는 출력하거나 문서에 기록하지 않았다.
- Purchase Pack 결과: `pack=purchase`, `status=ready`, source 6건의 URL 존재, stdio MCP `compare_costs` 호출을 확인했다.
- 이 검증은 실제 Web Search 및 MCP 연결 여부만 기록하며, 검색 결과의 가격·사양 값을 문서에 재기록하지 않는다.

## 로컬 검증 범위

- 15개 시나리오의 정상 workflow, 6개 Pack 각각의 필수 입력 부족, MCP Tool 오류, Phase 5 source 분리, 기존 Tool 이름만 호출되는지를 검증했다.
- `ambiguous-001` fixture의 원문과 expected intent `unknown`이 유지됨을 검증했다.
- API는 Stub Agent와 실제 stdio MCP Client 조합으로 Recurring Cost Pack의 `annualize_expense` 재사용을 검증했다.
- Workspace 계약은 `/api/decisions`, Decision Pack form, data-driven result card, facts/assumptions/calculations/sources 표시를 검증했다.

## 범위 제외

- 자동 구매, 자동 계약, 자동 구독 해지
- 은행·카드 계정 직접 연동, 신용평가, 투자 자문
- Multi-Agent, 가격 예측 모델, Phase 7 End-to-End Evaluation
