# Decision Workspace 재구상 시안

이미지 생성기로 만든 UI 재구상 시안이다. 시안은 실제 기능을 대체하지 않는 시각·구조 참고용이며, 구현되지 않은 데이터나 기능을 제품 화면에 추가하지 않는다.

## 시안

1. [A — Editorial Control Room](concept-a-editorial-control-room.png)
   - 편집형 정보 위계와 분석 중심 레이아웃
2. [B — Decision Cockpit](concept-b-decision-cockpit.png)
   - 결과 카드와 Inspector 분리
3. [C — Decision Brief](concept-c-decision-brief.png)
   - 비교 내용을 solid surface로 강조
4. [D — Consumer Decision Rail](concept-d-consumer-decision-rail.png)
   - 단일 질문, 실제 소비 시나리오, 근거 중심 결과를 연결한 소비자용 제품 화면

## 선택

시안 D를 선택했다. 기존 사이드바·진행 표시·관리형 카드 비율을 버리고, 사용자가 첫 화면에서 비교·계산 서비스임을 바로 이해하도록 단일 질문과 생활 소비 시나리오를 중심에 놓는다.

구현에서는 시안의 단일 질문 흐름을 발전시켜 15개 편집 가능한 템플릿을 제공한다. 카드에는 필요한 입력값을 보여 주고, 대괄호 입력값은 자동 선택 및 `Tab` 이동을 지원한다. 파일 업로드 없이 텍스트를 붙여넣는 시나리오는 그 입력 방식을 원문과 안내에 명시한다.

## Prompt set

- `ui-mockup`: Korean consumer fintech decision utility, desktop 1440px
- Direction D: dark product canvas with one decision composer, grouped real-world spending scenarios, and an evidence-first result workspace
- 공통 제약: 한국어 소비자 UI, 단일 질문 입력, 가짜 수치·차트·개발자 용어·raw output·watermark 제외

## 구현 화면 확인

- [1440px](verification/render-consumer-1440.png)
- [1280px](verification/render-consumer-1280.png)
- [1024px](verification/render-consumer-1024.png)
- [390px](verification/render-consumer-390.png)
- [320px](verification/render-consumer-320.png)

위 캡처는 초기 화면 기준이다. 결과 상태는 검증을 위해서만 별도 임시 데이터로 확인하며 저장하거나 제품 화면에 포함하지 않는다.
