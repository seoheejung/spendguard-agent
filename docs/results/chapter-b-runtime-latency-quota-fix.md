# Chapter B runtime latency and quota fix

## 변경

- SpendGuard 실행에만 `gpt-6-luna`와 low reasoning 적용. 설치된 Codex CLI 0.156.1의 모델 캐시에 두 설정이 표시됨.
- Search 시작 기준 최대 4회 또는 첫 Search 시작 후 60초. 예산 도달 시 세션을 이어서 Search 없이 답변 완료.
- 후속 질문은 서버에 보관한 세션 ID로 `codex exec resume` 사용. 기존 근거로 먼저 답하고 새 현재 정보가 필요할 때만 Search를 활성화. 사용 한도 오류는 HTTP 429와 `codex_usage_limit`으로 반환.
- 결과 화면에 원 질문, 진행 단계, 실제 호출 수와 지연 시간, 비교 답변, 후속 질문 배치.

## 검증

- `python -m pytest -q -p no:cacheprovider tests/test_codex_runtime.py`: 6개 통과. 가짜 CLI로 Search 예산 후 재개, 후속 질문 세션 재사용, 한도 오류를 확인.
- `python -m pytest -q -p no:cacheprovider tests/test_calculations.py tests/test_mcp.py`: 19개 통과.
- `node --check src/spendguard/static/app.js`, Python `compileall`, `git diff --check`: 통과.
- 로컬 정적 화면에서 데스크톱과 390px 화면의 가로 넘침 없음, 결과와 후속 질문의 순서 확인.

## 실제 Codex 검증

권한이 허용된 실행 환경에서 기존 ChatGPT 로그인을 재사용했다. 로그인이나 인증 갱신은 시작하지 않았다.

| 흐름 | 총 지연 시간 | Search | SpendGuard MCP | 결과 |
| --- | ---: | ---: | ---: | --- |
| 변경 전 삼성 비교, 사용자 제공 로그 | 168.1초 | 12회 | 2회 | 비교 답변 |
| 변경 후 삼성 S26 비교 | 39.6초 | 2회 | 1회, `compare_costs` | 130만 원 예산, 판매 가격, 배송, 할인 조건, 대안과 출처를 포함한 답변 |
| 같은 세션의 정정 후속 질문 | 14.1초 | 0회 | 0회 | `exec resume` 사용, S25·S26 점수 방향과 출처가 일치하는 최종 답변 |

첫 후속 질문 실측에서는 CLI가 세션 시작 후 응답 이벤트를 내지 않아 240초 제한에 걸렸다. 이후 후속 질문을 기존 근거로 먼저 처리하고 전체 제한을 120초로 낮췄다. 재검증은 13.5초에 완료됐지만 첫 문장과 수치 표가 모순되어, 공통 비교 지침을 보강하고 동일 세션에서 정정 질문을 확인했다. 검증용 PowerShell 파이프가 한글을 손상시킨 초기 측정은 품질·지연 비교에서 제외했다.

사용 한도 오류의 실제 재발은 없어서 429 경로는 가짜 CLI와 API 테스트로 검증했다.
