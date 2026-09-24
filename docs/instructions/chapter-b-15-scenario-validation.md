# Chapter B. Codex 런타임과 15개 소비 질문 검증

## 현재 실행 범위

독립 SpendGuard 웹 UI의 질문은 FastAPI `/api/decisions`를 거쳐 현재 Windows 사용자에게 ChatGPT 계정으로 인증된 Codex CLI가 처리한다. Codex가 자연어 이해, 필요한 현재 정보 조사, SpendGuard MCP 계산 사용, 최종 답변을 맡는다. SpendGuard는 직접 OpenAI Platform API를 호출하거나 API key/model 환경 변수에 의존하지 않는다. 자동 로그인과 Platform API fallback도 없다.

질문 정보가 부족해도 명시적인 수정 가능 가정과 현재 확인 가능한 사실로 유용한 답을 작성한다. 검색하지 않은 현재 가격을 만들지 않고, 검색 가격의 값·단위·조건·출처·조회 시점을 최종 판단에 반영한다. 산술은 MCP 반환값을 사용한다. 사용자 화면은 하나의 자연스러운 답변을 표시하며 평가 trace를 노출하지 않는다.

15개 시나리오는 제품 기능 목록이다. 별도 pipeline, regex 라우팅, 시나리오별 answer schema를 만들지 않는다.

## 런타임 경계

- Codex 실행은 임시 작업 디렉터리와 읽기 전용 sandbox를 사용한다. shell, apps, hooks를 끄고 저장소 수정과 임의 명령을 서비스 요청에서 허용하지 않는다.
- 시작 시 현재 사용자 인증을 한 번 확인한다. 질문마다 login status나 OAuth를 실행하지 않는다.
- Codex CLI는 현재 Codex 설정의 모델과 인증을 사용한다. `OPENAI_API_KEY`, `OPENAI_MODEL`, TypeSafe key를 자식 환경에 전달하지 않는다.
- Search는 Codex가 질문 의미로 결정한다. mutable offer와 현재 가격·요금·혜택·정책은 필요한 경우 실제 검색한다. 부실한 검색은 근거 없는 숫자로 대체하지 않는다.
- 결정론적 도구는 `calculate_installment`, `calculate_refinance`, `calculate_usage_cost`, `annualize_expense`, `calculate_tco`, `compare_costs`, `calculate_repeated_cost`, `sum_costs`다.

## Jev 평가 모드

기본 UI는 `baseline`이다. 평가 실행에서 `jev`와 후보를 명시하면 아래 좁은 판단 중 하나만 TypeSafe Jev로 평가하고 Codex의 최종 입력에 전달한다.

| 후보 | 판단 |
| --- | --- |
| 구독료 다이어트 | 중복·저활용 절감 후보인가 |
| 견적서 바가지 체크 | 추가 검토가 필요한 항목인가 |
| 연간 새는 돈 찾기 | 만족도 영향이 낮은 절감 후보인가 |
| 구매 전 최종 심사 | 상세 비교할 가치가 있는 대안인가 |

Jev는 Search 여부, 추가 질문, 금액 계산, 전체 라우팅, 사용자 결론을 결정하지 않는다. Jev 실패는 기록 가능한 API 오류이며 현재 자동 fallback은 없다. 네 후보의 실제 평가 결과가 품질 저하 없이 Codex 호출 수나 E2E 시간을 줄이고 실패가 늘지 않는다는 증거가 있어야 기본 경로 적용을 고려한다.

## 검증

고정 데이터는 `evals/chapter_b_sparse_v1.json`의 15개 질문과 criterion이다. 답변에 맞춰 criterion을 수정하지 않는다. 실제 `/api/decisions`로 baseline 15건을 먼저 실행하고, 같은 fixture의 Jev 모드 15건을 실행한다. 원시 답변, Search와 MCP 호출·입력·결과, Jev 판단, Codex 횟수, latency, 오류·timeout·retry를 남긴다. 측정하지 못한 내부 token, model cost, ChatGPT quota는 기록하지 않는다.

실패는 테스트별 하드코딩으로 때우지 않고 공통 원인을 확인해 수정한다. 과거 오류의 stderr나 상태가 보존되지 않았으면 원인을 `unknown`으로 기록하며 재현만으로 과거 원인을 확정하지 않는다. 이후 비정상 종료의 종료 코드와 stderr는 즉시 평가 아티팩트에 보존한다.

현재 실측, 수정 후 관련 사례 재검증, 남은 실패와 제약은 [Chapter B Codex 런타임 결과](../results/chapter-b-codex-runtime-mvp.md)에 있다. Phase 0~7, Chapter A, Track A 및 중단된 Decision Answer Reconstruction 문서는 역사적 기록이다.
