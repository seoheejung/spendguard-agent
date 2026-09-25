# Chapter B runtime latency and quota fix

## 변경

- SpendGuard 실행에만 `gpt-6-luna`와 low reasoning 적용. 설치된 Codex CLI 0.156.1의 모델 캐시에 두 설정이 표시됨.
- Search 시작 기준 최대 4회 또는 첫 Search 시작 후 60초. 예산 도달 시 세션을 이어서 Search 없이 답변 완료.
- 후속 질문은 서버에 보관한 세션 ID로 `codex exec resume` 사용. 사용 한도 오류는 HTTP 429와 `codex_usage_limit`으로 반환.
- 결과 화면에 원 질문, 진행 단계, 실제 호출 수와 지연 시간, 비교 답변, 후속 질문 배치.

## 검증

- `python -m pytest -q -p no:cacheprovider tests/test_codex_runtime.py`: 6개 통과. 가짜 CLI로 Search 예산 후 재개, 후속 질문 세션 재사용, 한도 오류를 확인.
- `python -m pytest -q -p no:cacheprovider tests/test_calculations.py tests/test_mcp.py`: 19개 통과.
- `node --check src/spendguard/static/app.js`, Python `compileall`, `git diff --check`: 통과.
- 로컬 정적 화면에서 데스크톱과 390px 화면의 가로 넘침 없음, 결과와 후속 질문의 순서 확인.

## 실제 Codex 검증 상태

이 실행 환경의 `codex login status`는 `Not logged in`을 반환했다. 로그인이나 인증 갱신을 시작하지 않았으며, 삼성 S26 비교와 후속 질문의 실제 Search/MCP 호출 및 변경 후 지연 시간은 측정하지 않았다. 변경 전 168.1초, Search 12회, MCP 2회는 사용자 제공 로그 값이다.
