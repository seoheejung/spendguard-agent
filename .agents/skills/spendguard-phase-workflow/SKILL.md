---
name: spendguard-phase-workflow
description: Use when implementing or verifying the current SpendGuard phase according to the project plan and phase instruction.
---

# SpendGuard Phase Workflow

## Purpose

SpendGuard의 현재 Phase를 기획 범위 안에서 구현하고 검증하기 위한 반복 작업 절차

## Workflow

1. 사용자의 현재 지시 확인
2. `.project/plan.md`에서 프로젝트 범위 확인
3. 현재 `docs/instructions/phaseN-*.md` 확인
4. 관련 기존 코드와 테스트 확인
5. 현재 Phase 범위만 구현
6. 현재 Phase에서 요구하는 외부 SDK와 공식 문서 확인
7. 관련 테스트와 실제 실행 검증
8. 실패 원인과 미완료 항목 확인
9. 실제 결과만 `docs/results/`에 기록
10. 현재 상태가 바뀐 경우 README 반영
11. `git diff`와 `git status` 확인
12. 현재 Phase 완료 기준 확인

## Boundaries

- 미래 Phase 기능 선반영 금지
- 근거 없는 구조 변경 금지
- 검증하지 않은 실행 결과 작성 금지
- 현재 Phase에서 필요하지 않은 패키지 추가 금지
- 평가 없이 모델 우위 주장 금지
- 평가 없이 confidence threshold 설정 금지
- `.project/plan.md` 변경은 사용자가 기획 변경을 명시한 경우에만 수행

## Completion

현재 Phase instruction에 정의된 완료 기준과 검증 항목을 모두 확인한 경우에만 완료로 기록
