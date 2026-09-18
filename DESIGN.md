# DESIGN.md

> SpendGuard Web UI 디자인 기준

## 1. 목적

사용자가 결론, 입력 사실, 계산 근거, 외부 출처, 가정을 빠르게 구분할 수 있는 인터페이스 구성

디자인 방향:

`Liquid Glass × Financial Control Room × Retrofuturism`

시각 효과보다 콘텐츠 구조, 확장성, 재사용성, 성능을 우선한다.

## 2. 기본 원칙

- 결론과 중요한 숫자 우선 배치
- 계산과 설명 시각적 분리
- 사실과 가정 구분
- 외부 출처 명시
- 장식보다 정보 위계 우선
- 실제 데이터 없는 Placeholder 영역 생성 금지
- 페이지별 전용 구조보다 재사용 가능한 Layout 우선
- 모션·Glass·Gradient 제거 후에도 정보 구조 유지

## 3. 기본 화면 구조

```text
Header
├── Search / Ask
└── Agent Status

Sidebar
├── Today
├── Decisions
├── Reports
├── Sources
└── Settings

Workspace
├── Question / Input
├── Decision Status
├── Decision Cards
└── Detail / Inspector
```

Decision 상태:

```text
Needs Input
Researching
Calculating
Review
Ready
```

## 4. Layout

- CSS Grid / Flexbox 우선
- 고정 높이 최소화
- 장식 목적 외 Absolute Positioning 최소화
- 카드와 콘텐츠 수 증가에도 구조 유지
- 공통 `Grid`, `Stack`, `Panel`, `Card` 구조 재사용
- 새로운 Decision Type 추가 시 기존 Layout 수정 최소화

## 5. 입력과 결과

### Input

- 자연어 질문 입력 기본
- 필수 정보 누락 시 필요한 입력만 추가 노출
- 숫자는 단위와 통화 함께 표시

### Result

```text
Conclusion
Facts
Calculations
Options
Risks
Sources
```

- 계산식, 입력값, 계산 결과 함께 표시
- 사용자 입력 사실과 외부 확인 사실 분리
- 선택지별 비용과 조건 비교
- 가정은 별도 영역으로 구분

## 6. Visual

### Liquid Glass

사용:

- Navigation
- Floating Control
- Modal / Inspector
- Active Decision Layer

사용하지 않음:

- 계산표
- 긴 본문
- 핵심 숫자 영역 전체

### Color

```text
Deep Ink       Base
Electric Blue  Agent / Research
Acid Lime      Saving / Positive
Hot Orange     Warning
Violet         Jev
Ice Cyan       MCP / Calculation
```

색상만으로 판단 결과를 표현하지 않는다.

### Typography

- 중요한 금액과 수치를 가장 크게 표현
- 계산 Trace는 Monospace 사용 가능
- 과도한 대형 문구 남용 금지

### Retrofuturism

- Thin Grid
- Technical Label
- Monospace Number
- 제한적인 Pixel / CRT 질감

레이아웃 자체를 레트로 UI로 만들지 않는다.

## 7. Motion

Motion은 상태 변화와 사용자 Action에만 사용한다.

```text
Researching → Calculating → Review → Ready
```

허용:

- 상태 전환
- Panel Open / Close
- Navigation 이동
- 데이터 갱신 피드백

금지:

- Video Hero
- 의미 없는 Floating
- 반복 Background Animation
- 과도한 Hover Transform
- 기능과 관계없는 Particle Effect

`prefers-reduced-motion`을 지원한다.

## 8. 반응형과 접근성

- Desktop과 Mobile 모두 정보 우선순위 유지
- Desktop 화면 단순 축소 금지
- 핵심 수치 잘림 방지
- 표는 필요 시 가로 스크롤
- 색상만으로 상태 구분 금지
- Form Label 명시
- Keyboard Navigation 지원
- 충분한 명도 대비 유지

## 9. 성능

- Video Hero, 상시 WebGL, 불필요한 Three.js 사용 금지
- 대형 이미지보다 SVG / CSS 표현 우선
- 과도한 Backdrop Filter 금지
- 화면 밖 Animation 실행 금지
- 시각 효과보다 입력, 탐색, 상태 갱신 속도 우선

## 10. 검증 기준

- 카드가 3개에서 30개로 증가해도 구조가 유지되는가
- 제목과 설명 길이가 늘어나도 깨지지 않는가
- 새로운 Decision Type 추가 시 공통 Component 수정이 최소인가
- Motion, Glass, Gradient를 제거해도 사용할 수 있는가
- 구현되지 않은 기능을 UI가 암시하지 않는가

## 11. 금지 사항

- 기능 범위를 `DESIGN.md`에 정의하지 않는다.
- 구현되지 않은 기능을 UI에 미리 배치하지 않는다.
- 특정 화면에만 맞춘 Layout을 만들지 않는다.
- 콘텐츠 변경을 위해 Component 코드를 직접 수정하는 구조를 만들지 않는다.
- 모델 confidence를 실제 성공 확률처럼 표시하지 않는다.
- 성능보다 시각 효과를 우선하지 않는다.
