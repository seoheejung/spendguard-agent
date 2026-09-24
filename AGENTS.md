# AGENTS.md

> SpendGuard 저장소 공통 작업 규칙

## Priority

1. 사용자 현재 지시
2. `.project/plan.md`
3. 현재 `docs/instructions/*`
4. `AGENTS.md`
5. `README.md`

`DESIGN.md`는 UI 기준으로만 사용한다.

## Runtime

- 현재 런타임은 `SpendGuard Web → FastAPI → Codex → Search / MCP / optional Jev` 구조를 따른다.
- OpenAI Platform API, `OPENAI_API_KEY`, `OPENAI_MODEL`을 현재 런타임에서 사용하지 않는다.
- 기존 Codex 인증을 재사용하며 실행 중 로그인·OAuth·브라우저 인증을 시작하지 않는다.
- Jev는 지정된 좁은 semantic judgment에만 사용한다.
- 결정적인 계산은 MCP 또는 코드로 처리한다.

## Work

- 현재 요구 범위에 필요한 변경을 수행한다.
- 테스트 케이스별 regex, if, 하드코딩으로 문제를 우회하지 않는다.
- 공통 원인은 공통 실행 경로에서 수정한다.
- 외부 사실·가격·출처·실행 결과를 만들지 않는다.
- 사용자 사실과 시스템 가정을 구분한다.
- 불완전한 입력도 합리적인 가정으로 답할 수 있으면 중단하지 않는다.
- 불필요한 추상화와 범용 framework를 추가하지 않는다.
- 코드 주석은 짧은 명사형으로 작성한다.

## Verification

- 변경 후 실제 동작을 검증한다.
- Search, MCP, Jev는 실제 호출 여부까지 확인한다.
- 실패를 기록만 하고 종료하지 않고 원인을 수정한 뒤 재검증한다.
- 평가 기준을 결과에 맞춰 변경하지 않는다.
- 실행하지 않은 테스트나 측정값을 기록하지 않는다.

## Documentation

- 계획, 작업 지침, 실제 결과를 구분한다.
- README에는 현재 구현 상태만 기록한다.
- 과거 OpenAI Agents / Responses 결과는 historical result로 보존한다.

## Git

- 기능 단위로 작업을 완료하고 검증한 뒤 커밋한다.
- 서로 다른 기능을 하나의 커밋에 섞지 않는다.
- 커밋 메시지는 변경 기능을 명확하게 표현한다.
- 사용자의 명시적 지시 없이 push하지 않는다.