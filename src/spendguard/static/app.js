const state = { question: "", data: {}, decision: null, scenarioId: null, activeScenarioGroup: "사기 전에", requestInFlight: false };

const scenarioDefinitions = [
  { id: "price-comparison", group: "사기 전에", label: "최저가 비교", promptTemplate: "[제품명]을 사려고 해. 같은 제품뿐 아니라 비슷한 대안까지 찾아서 가격과 조건을 비교해줘.", inputHints: ["제품명"], guidance: "[제품명]을 먼저 고치세요.", icon: "tag" },
  { id: "impulse-purchase", group: "사기 전에", label: "충동구매 방지", promptTemplate: "[제품명]을 [가격]원에 살까 고민 중이야. 얼마나 자주 쓸지, 대체할 방법은 없는지, 이 돈을 다른 데 썼을 때까지 고려해서 사도 괜찮은지 따져줘.", inputHints: ["제품명", "가격"], guidance: "[제품명]부터 고치고 Tab으로 다음 값으로 이동하세요.", icon: "pause" },
  { id: "purchase-review", group: "사기 전에", label: "구매 전 최종 심사", promptTemplate: "[제품명]을 [가격]원에 사려고 해. 지금 사는 것과 기다리는 것, 중고로 사는 것, 다른 제품을 고르는 것까지 비교해서 비용 면에서 어떤 차이가 있는지 보여줘.", inputHints: ["제품명", "가격"], guidance: "[제품명]부터 고치고 Tab으로 다음 값으로 이동하세요.", icon: "shield" },
  { id: "subscription-audit", group: "매달 새는 돈", label: "구독료 다이어트", promptTemplate: "결제 중인 구독 목록을 아래에 붙여넣을게. 기능이 겹치거나 거의 쓰지 않는 서비스를 찾아서 무엇부터 정리하면 좋을지 알려줘.", inputHints: ["구독 목록"], guidance: "원문 아래 새 줄에 구독 목록을 붙여넣으세요.", pasteNote: "카드사·은행 앱에서 복사한 내역이나 표 형식의 지출내역을 붙여넣을 수 있습니다.", icon: "repeat" },
  { id: "mobile-plan", group: "매달 새는 돈", label: "통신비 점검", promptTemplate: "현재 요금제와 월 데이터 사용량을 줄게. 필요 이상으로 내고 있는 비용이 있는지 보고, 더 맞는 요금제가 있는지 비교해줘.", inputHints: ["요금제", "데이터 사용량"], guidance: "원문 아래 새 줄에 현재 요금제와 월 데이터 사용량을 적으세요.", icon: "signal" },
  { id: "insurance-overlap", group: "매달 새는 돈", label: "보험 중복 찾기", promptTemplate: "가입한 보험의 보장 내용과 보험료를 아래에 붙여넣을게. 서로 겹치는 보장과 필요 이상으로 많이 들어간 부분이 있는지 구분해줘.", inputHints: ["보험 보장 내용", "보험료"], guidance: "원문 아래 새 줄에 가입한 보험 보장 내용과 보험료를 붙여넣으세요.", pasteNote: "카드사·은행 앱에서 복사한 내역이나 표 형식의 지출내역을 붙여넣을 수 있습니다.", icon: "shield" },
  { id: "annual-leaks", group: "매달 새는 돈", label: "연간 새는 돈 찾기", promptTemplate: "최근 3개월 지출내역을 아래에 붙여넣을게. 만족도는 거의 떨어뜨리지 않으면서 줄일 수 있는 지출을 찾아서 1년 기준 절감액을 계산해줘.", inputHints: ["최근 3개월 지출내역"], guidance: "원문 아래 새 줄에 최근 3개월 지출내역을 붙여넣으세요.", pasteNote: "카드사·은행 앱에서 복사한 내역이나 표 형식의 지출내역을 붙여넣을 수 있습니다.", icon: "wallet" },
  { id: "installment", group: "큰돈 계산", label: "할부 vs 일시불", promptTemplate: "[가격]원짜리 제품을 [금리]%로 [개월]개월 할부하려고 해. 일시불과 비교해서 실제로 얼마를 더 내는지 계산해줘.", inputHints: ["가격", "금리", "개월"], guidance: "[가격]부터 고치고 Tab으로 다음 값으로 이동하세요.", icon: "calculator" },
  { id: "refinance", group: "큰돈 계산", label: "대출 갈아타기 계산", promptTemplate: "대출잔액 [잔액]원, 현재 금리 [금리]%, 남은 기간 [기간]이야. 금리를 [새 금리]%로 낮췄을 때 총이자가 얼마나 줄어드는지 계산해줘.", inputHints: ["잔액", "현재 금리", "남은 기간", "새 금리"], guidance: "[잔액]부터 고치고 Tab으로 다음 값으로 이동하세요.", icon: "swap" },
  { id: "car-ownership", group: "큰돈 계산", label: "자동차 유지비 계산", promptTemplate: "[차량]을 보유하면 보험료, 세금, 연료비, 정비비, 감가상각까지 포함해서 앞으로 5년 동안 실제로 얼마가 드는지 계산해줘.", inputHints: ["차량"], guidance: "[차량]을 먼저 고치세요.", icon: "car" },
  { id: "card-benefits", group: "생활비 줄이기", label: "카드 혜택 최적화", promptTemplate: "최근 한 달 소비내역을 아래에 붙여넣을게. 내 지출 패턴에서 실제로 받을 수 있는 카드 혜택을 비교하고 어디서 가장 많이 아낄 수 있는지 계산해줘.", inputHints: ["최근 한 달 소비내역"], guidance: "원문 아래 새 줄에 최근 한 달 소비내역을 붙여넣으세요.", pasteNote: "카드사·은행 앱에서 복사한 내역이나 표 형식의 지출내역을 붙여넣을 수 있습니다.", icon: "card" },
  { id: "grocery-budget", group: "생활비 줄이기", label: "장보기 예산 절감", promptTemplate: "일주일 식비는 [예산]원이고 [인원]명이 먹어. 재료를 최대한 돌려 쓰면서 예산 안에서 장볼 목록과 식단을 짜줘.", inputHints: ["예산", "인원"], guidance: "[예산]부터 고치고 Tab으로 다음 값으로 이동하세요.", icon: "basket" },
  { id: "travel-budget", group: "생활비 줄이기", label: "여행비 최적화", promptTemplate: "[여행지]로 [기간] 동안 여행할 거야. 여행 만족도는 크게 떨어뜨리지 않으면서 항공숙박교통식비를 줄일 수 있는 방법을 찾아줘.", inputHints: ["여행지", "기간"], guidance: "[여행지]부터 고치고 Tab으로 다음 값으로 이동하세요.", icon: "plane" },
  { id: "quote-audit", group: "계약하기 전에", label: "견적서 바가지 체크", promptTemplate: "받은 견적 내용을 아래에 붙여넣을게. 가격이 유독 높아 보이는 항목, 꼭 필요한 항목, 빼거나 조정해볼 만한 항목을 구분해줘.", inputHints: ["견적 내용"], guidance: "원문 아래 새 줄에 받은 견적 내용을 붙여넣으세요.", pasteNote: "카드사·은행 앱에서 복사한 내역이나 표 형식의 지출내역을 붙여넣을 수 있습니다.", icon: "receipt" },
  { id: "price-negotiation", group: "계약하기 전에", label: "가격 협상 준비", promptTemplate: "[상품/서비스] 계약을 앞두고 있어. 가격이나 조건에서 협상해볼 만한 부분을 찾아주고, 실제로 어떻게 말하면 좋을지도 써줘.", inputHints: ["상품/서비스"], guidance: "[상품/서비스]를 먼저 고치세요.", icon: "handshake" },
];

const scenarioGroups = ["사기 전에", "매달 새는 돈", "큰돈 계산", "생활비 줄이기", "계약하기 전에"];
const scenarioById = new Map(scenarioDefinitions.map((scenario) => [scenario.id, scenario]));
let activePlaceholderIndex = -1;

const fieldDefinitions = {
  target: { label: "무엇을 고려하고 있나요?", type: "text" },
  purpose: { label: "어떤 목적으로 필요한가요?", type: "text" },
  "price or price_confirmation_needed": { label: "현재 가격 또는 확인이 필요한 가격", type: "text", key: "price", hint: "예: 80000원 또는 현재 가격 확인" },
  item: { label: "어떤 지출인가요?", type: "text" },
  current_cost: { label: "현재 비용", type: "number", unit: "원" },
  amount: { label: "금액", type: "number", unit: "원" },
  term_months: { label: "기간", type: "number", unit: "개월" },
  rate_or_comparison: { label: "이자율 또는 비교 기준", type: "text", hint: "예: 연 4.5% 또는 기존 조건과 비교" },
  ownership_months: { label: "보유 기간", type: "number", unit: "개월" },
  quote_items: { label: "견적 항목", type: "text", key: "quote_items", hint: "예: 에어컨 수리" },
  "budget or expenses": { label: "예산", type: "number", key: "budget", unit: "원" },
};

const calculationLabels = {
  calculate_installment: "할부 비용",
  calculate_refinance: "대환 비용 비교",
  calculate_usage_cost: "단위당 비용",
  annualize_expense: "연간 비용",
  calculate_tco: "총 보유 비용",
  compare_costs: "선택지 비용 비교",
};

const resultFieldLabels = {
  monthly_payment: "월 납입액",
  total_payment: "총 납입액",
  total_interest: "총 이자",
  new_remaining_total: "새 조건의 잔여 총액",
  savings: "절감액",
  cost_per_unit: "단위당 비용",
  annual_amount: "연간 금액",
  tco: "총 보유 비용",
  lowest_cost_option: "가장 낮은 비용의 선택지",
  lowest_total_cost: "가장 낮은 총비용",
};

function resultFieldLabel(key) {
  if (key.startsWith("difference_from_")) return `${key.slice("difference_from_".length)} 대비 차이`;
  return resultFieldLabels[key] || key.replaceAll("_", " ");
}

const questionForm = document.querySelector("#decision-form");
const question = document.querySelector("#question");
const requiredData = document.querySelector("#required-data");
const requiredDataForm = document.querySelector("#required-data-form");
const requiredDataFields = document.querySelector("#required-data-fields");
const resultSection = document.querySelector("#decision-result");
const decisionCards = document.querySelector("#decision-cards");
const status = document.querySelector("#decision-status");
const error = document.querySelector("#error");
const inspector = document.querySelector("#inspector");
const inspectorContent = document.querySelector("#inspector-content");
const scenarioGroupsContainer = document.querySelector("#scenario-groups");
const templateGuidance = document.querySelector("#template-guidance");
const workspace = document.querySelector("#workspace");
const siteHeader = document.querySelector(".site-header");
const processingBlocker = document.querySelector("#processing-blocker");
const processingMessage = document.querySelector("#processing-message");

function setStatus(value, statusName) {
  status.querySelector(".status-label").textContent = value;
  status.dataset.status = statusName;
}

function setProgress(active) {
  document.body.dataset.decisionStage = active;
  const messages = {
    request: "요청을 확인하고 있어요",
    work: "가격과 조건을 확인하고 있어요",
    details: "필요한 정보를 정리하고 있어요",
    result: "결과를 정리하고 있어요",
  };
  processingMessage.textContent = messages[active] || messages.request;
}

function setRequestLock(locked) {
  document.body.classList.toggle("is-request-pending", locked);
  workspace.inert = locked;
  siteHeader.inert = locked;
  processingBlocker.hidden = !locked;
}

const iconShapes = {
  tag: [["path", { d: "M20.6 13.4 13.4 20.6a2 2 0 0 1-2.8 0L3 13V4h9l8.6 8.6a.6.6 0 0 1 0 .8Z" }], ["circle", { cx: "7.5", cy: "8.5", r: "1" }]],
  pause: [["circle", { cx: "12", cy: "12", r: "8.5" }], ["path", { d: "M10 9v6m4-6v6" }]],
  shield: [["path", { d: "M12 2.8 19 5.6v5.7c0 4.5-3 8.5-7 9.9-4-1.4-7-5.4-7-9.9V5.6l7-2.8Z" }], ["path", { d: "m8.7 11.9 2.1 2.1 4.5-4.7" }]],
  repeat: [["path", { d: "M17 2.5A9.5 9.5 0 1 0 21.5 12" }], ["path", { d: "M17 2.5v5h-5M7 21.5v-5h5" }]],
  signal: [["path", { d: "M4.5 18.5a10.6 10.6 0 0 1 15 0M7.5 15.5a6.4 6.4 0 0 1 9 0M10.5 12.5a2.1 2.1 0 0 1 3 0" }], ["path", { d: "M12 19.5h.01" }]],
  wallet: [["path", { d: "M3 7.5h18v11H3zM16 12h5M7 7.5V5.8A2.8 2.8 0 0 1 9.8 3h4.4A2.8 2.8 0 0 1 17 5.8v1.7" }], ["circle", { cx: "16", cy: "13", r: "1" }]],
  calculator: [["rect", { x: "4", y: "2.5", width: "16", height: "19", rx: "2" }], ["path", { d: "M7.5 6.5h9M8 11h.01M12 11h.01M16 11h.01M8 15h.01M12 15h.01M16 15h.01" }]],
  swap: [["path", { d: "M7 7h12l-3-3m3 3-3 3M17 17H5l3 3m-3-3 3-3" }]],
  car: [["path", { d: "m5 16 1.5-6h11L19 16M4 16h16v3H4zM7 19v2m10-2v2" }], ["circle", { cx: "7.5", cy: "16.5", r: ".8" }], ["circle", { cx: "16.5", cy: "16.5", r: ".8" }]],
  card: [["rect", { x: "3", y: "5", width: "18", height: "14", rx: "2" }], ["path", { d: "M3 9h18M7 15h3" }]],
  basket: [["path", { d: "M4 9h16l-1.4 10H5.4L4 9ZM9 9l3-5 3 5M8 13h.01m4 0h.01m4 0h.01" }]],
  plane: [["path", { d: "m3 11 18-7-6 16-3-6-6-3Z" }], ["path", { d: "m12 14 3-3" }]],
  receipt: [["path", { d: "M6 2.5h12v19l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4-2 1.4v-19Z" }], ["path", { d: "M9 7h6M9 11h6M9 15h4" }]],
  handshake: [["path", { d: "m8 12 2.2 2.2a1.7 1.7 0 0 0 2.4 0l1.5-1.5a1.7 1.7 0 0 0 0-2.4L12 8.2a2.3 2.3 0 0 0-3.2 0L7.5 9.5" }], ["path", { d: "m4 9 3-3 3 3m7 6 1.5 1.5 2-2-3-3" }]],
};

function createScenarioIcon(name) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "scenario-icon");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  for (const [tag, attributes] of iconShapes[name] || iconShapes.tag) {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [attribute, value] of Object.entries(attributes)) node.setAttribute(attribute, value);
    svg.append(node);
  }
  return svg;
}

function createHintList(hints) {
  const list = document.createElement("span");
  list.className = "scenario-hints";
  for (const hint of hints) list.append(Object.assign(document.createElement("span"), { textContent: hint }));
  return list;
}

function renderScenarioGroups() {
  scenarioGroupsContainer.replaceChildren();
  const tabs = document.createElement("div");
  tabs.className = "scenario-group-tabs";
  tabs.setAttribute("role", "tablist");
  for (const groupName of scenarioGroups) {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.className = "scenario-group-tab";
    tab.dataset.scenarioGroup = groupName;
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", String(groupName === state.activeScenarioGroup));
    tab.textContent = groupName;
    tabs.append(tab);
  }
  scenarioGroupsContainer.append(tabs);

  const scenarios = scenarioDefinitions.filter((scenario) => scenario.group === state.activeScenarioGroup);
  const group = document.createElement("section");
  group.className = "scenario-group";
  group.dataset.count = String(scenarios.length);
  group.append(Object.assign(document.createElement("h3"), { textContent: state.activeScenarioGroup }));
  const cards = document.createElement("div");
  cards.className = "scenario-group-grid";
  for (const scenario of scenarios) {
    const card = document.createElement("button");
    card.className = `scenario-card${scenario.id === "purchase-review" ? " scenario-card-emphasis" : ""}`;
    card.type = "button";
    card.dataset.scenarioId = scenario.id;
    card.append(createScenarioIcon(scenario.icon), Object.assign(document.createElement("strong"), { textContent: scenario.label }), createHintList(scenario.inputHints));
    cards.append(card);
  }
  group.append(cards);
  scenarioGroupsContainer.append(group);
}

function placeholderRanges() {
  return [...question.value.matchAll(/\[[^\]]+\]/g)].map((match) => ({ start: match.index, end: match.index + match[0].length }));
}

function selectPlaceholder(index) {
  const placeholders = placeholderRanges();
  if (!placeholders[index]) return false;
  activePlaceholderIndex = index;
  question.focus({ preventScroll: true });
  question.setSelectionRange(placeholders[index].start, placeholders[index].end);
  return true;
}

function setScenarioSelection(id) {
  scenarioGroupsContainer.querySelectorAll("[data-scenario-id]").forEach((card) => {
    card.dataset.selected = String(card.dataset.scenarioId === id);
  });
}

function renderTemplateGuidance(scenario, preserveCurrentQuestion = false) {
  templateGuidance.replaceChildren();
  const title = document.createElement("strong");
  title.textContent = preserveCurrentQuestion ? "작성 중인 질문은 그대로 유지했어요." : `${scenario.label} · 필요한 값`;
  const detail = document.createElement("span");
  detail.textContent = preserveCurrentQuestion ? "템플릿으로 바꾸려면 아래 버튼을 누르세요." : scenario.guidance;
  templateGuidance.append(title, detail);
  if (!preserveCurrentQuestion) templateGuidance.append(createHintList(scenario.inputHints));
  if (!preserveCurrentQuestion && scenario.pasteNote) {
    templateGuidance.append(Object.assign(document.createElement("span"), { className: "paste-note", textContent: scenario.pasteNote }));
  }
  if (preserveCurrentQuestion) {
    const apply = document.createElement("button");
    apply.type = "button";
    apply.textContent = "템플릿으로 바꾸기";
    apply.addEventListener("click", () => applyScenarioTemplate(scenario));
    templateGuidance.append(apply);
  }
  templateGuidance.hidden = false;
}

function applyScenarioTemplate(scenario) {
  state.scenarioId = scenario.id;
  question.value = scenario.promptTemplate;
  setScenarioSelection(scenario.id);
  renderTemplateGuidance(scenario);
  activePlaceholderIndex = -1;
  if (!selectPlaceholder(0)) {
    question.focus({ preventScroll: true });
    question.setSelectionRange(question.value.length, question.value.length);
  }
  document.querySelector("#question-panel").scrollIntoView({ behavior: "smooth", block: "center" });
}

function selectScenario(scenario) {
  const previousScenario = scenarioById.get(state.scenarioId);
  const currentQuestion = question.value.trim();
  const currentIsUntouchedTemplate = previousScenario && currentQuestion === previousScenario.promptTemplate;
  if (currentQuestion && !currentIsUntouchedTemplate) {
    renderTemplateGuidance(scenario, true);
    return;
  }
  applyScenarioTemplate(scenario);
}

function setError(message) {
  error.textContent = message;
  error.hidden = !message;
}

function listCard(title, values, className = "") {
  const card = document.createElement("article");
  card.className = `result-card solid-panel ${className}`;
  if (title) card.append(Object.assign(document.createElement("h3"), { textContent: title }));
  const list = document.createElement("ul");
  for (const value of values.length ? values : ["확인된 내용이 없습니다."]) {
    list.append(Object.assign(document.createElement("li"), { textContent: value }));
  }
  card.append(list);
  return card;
}

function valueRows(values) {
  const list = document.createElement("dl");
  list.className = "value-list";
  for (const [key, value] of Object.entries(values)) {
    const term = document.createElement("dt");
    term.textContent = resultFieldLabel(key);
    const detail = document.createElement("dd");
    detail.textContent = typeof value === "object" ? Object.values(value).join(", ") : String(value);
    const row = document.createElement("div");
    row.className = "value-row";
    row.append(term, detail);
    list.append(row);
  }
  return list;
}

function keyNumbers(decision) {
  const values = {};
  for (const entry of decision.calculations) {
    for (const [key, value] of Object.entries(entry.calculation.result)) {
      if (key !== "currency" && typeof value !== "object") values[key] = value;
    }
  }
  return values;
}

function renderDecisionResult(decision) {
  decisionCards.replaceChildren();
  const conclusion = document.createElement("article");
  conclusion.className = "result-card solid-panel conclusion-card";
  conclusion.append(
    Object.assign(document.createElement("p"), { className: "eyebrow", textContent: decision.status === "needs_input" ? "다음 단계" : "결론" }),
    Object.assign(document.createElement("p"), { textContent: decision.conclusion }),
  );
  decisionCards.append(conclusion);

  const numbers = keyNumbers(decision);
  if (Object.keys(numbers).length) {
    const card = document.createElement("article");
    card.className = "result-card solid-panel key-number-card";
    card.append(Object.assign(document.createElement("h3"), { textContent: "핵심 숫자" }), valueRows(numbers));
    decisionCards.append(card);
  }
  if (decision.options.length) decisionCards.append(listCard("선택지", decision.options, "options-card"));
  if (decision.risks.length) decisionCards.append(listCard("주의할 점", decision.risks, "risks-card"));
  if (decision.next_actions.length) decisionCards.append(listCard("다음 할 일", decision.next_actions, "actions-card"));
  resultSection.hidden = false;
  document.body.classList.add("has-decision", "has-active-decision");
}

function definitionFor(missingField) {
  return fieldDefinitions[missingField] || { label: missingField.replaceAll("_", " "), type: "text" };
}

function renderRequiredData(missingFields) {
  decisionCards.replaceChildren();
  resultSection.hidden = true;
  inspector.hidden = true;
  document.body.classList.remove("has-decision", "inspector-open");
  requiredDataFields.replaceChildren();
  for (const missingField of missingFields) {
    const definition = definitionFor(missingField);
    const key = definition.key || missingField;
    const wrapper = document.createElement("div");
    wrapper.className = "field-with-unit";
    const inputId = `required-${key.replaceAll(" ", "-")}`;
    const label = document.createElement("label");
    label.htmlFor = inputId;
    label.textContent = definition.label;
    const input = document.createElement("input");
    input.id = inputId;
    input.name = key;
    input.type = definition.type;
    input.required = true;
    input.autocomplete = "off";
    input.value = state.data[key] || "";
    if (definition.type === "number") input.inputMode = "decimal";
    if (definition.hint) input.placeholder = definition.hint;
    wrapper.append(label, input);
    if (definition.unit) wrapper.append(Object.assign(document.createElement("span"), { className: "input-unit", textContent: definition.unit }));
    requiredDataFields.append(wrapper);
  }
  document.querySelector("#required-data-note").textContent = "답변을 만들기 전에 이 정보만 확인할게요.";
  requiredData.hidden = false;
  requiredData.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateDataFromForm() {
  for (const input of requiredDataFields.querySelectorAll("input")) {
    if (input.name === "quote_items") {
      state.data.quote_items = [{ name: input.value }];
    } else {
      state.data[input.name] = input.value;
    }
  }
}

function enteredFacts() {
  return Object.entries(state.data).map(([key, value]) => {
    const label = definitionFor(key).label;
    if (Array.isArray(value)) return `${label}: ${value.map((item) => item.name).join(", ")}`;
    return `${label}: ${value}`;
  });
}

function inspectorSection(title, content) {
  const section = document.createElement("section");
  section.className = "inspector-card";
  section.append(Object.assign(document.createElement("h3"), { textContent: title }), content);
  return section;
}

function sourceList(sources) {
  const list = document.createElement("div");
  list.className = "source-list";
  for (const source of sources) {
    const item = document.createElement("article");
    const link = document.createElement("a");
    link.href = source.source_url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = source.source_name;
    item.append(
      Object.assign(document.createElement("p"), { textContent: source.value }),
      link,
      Object.assign(document.createElement("p"), { className: "form-note", textContent: `조회 시각: ${source.retrieved_at}` }),
    );
    list.append(item);
  }
  return list;
}

function renderInspector() {
  const decision = state.decision;
  if (!decision) return;
  inspectorContent.replaceChildren();
  inspectorContent.append(inspectorSection("사실", listCard("", [...decision.facts, ...enteredFacts()])));
  if (decision.calculations.length) {
    const calculations = document.createElement("div");
    for (const calculation of decision.calculations) {
      const item = document.createElement("article");
      item.className = "trace-item";
      item.append(Object.assign(document.createElement("h4"), { textContent: calculationLabels[calculation.tool] || "계산 결과" }), valueRows(calculation.calculation.result));
      calculations.append(item);
    }
    inspectorContent.append(inspectorSection("계산", calculations));
  }
  if (decision.sources.length) inspectorContent.append(inspectorSection("출처", sourceList(decision.sources)));
  if (decision.assumptions.length) inspectorContent.append(inspectorSection("가정", listCard("", decision.assumptions)));

  const technical = document.createElement("details");
  technical.className = "technical-details";
  technical.append(Object.assign(document.createElement("summary"), { textContent: "기술 세부 정보" }));
  const content = document.createElement("div");
  content.append(Object.assign(document.createElement("p"), { textContent: `결정 유형: ${decision.pack || "unknown"}` }));
  for (const calculation of decision.calculations) {
    content.append(
      Object.assign(document.createElement("p"), { textContent: `도구: ${calculation.tool}` }),
      Object.assign(document.createElement("code"), { textContent: calculation.calculation.formula }),
    );
  }
  technical.append(content);
  inspectorContent.append(technical);
  inspector.hidden = false;
  document.body.classList.add("inspector-open");
}

async function requestDecision() {
  if (state.requestInFlight) return;
  state.requestInFlight = true;
  const buttons = document.querySelectorAll("#decision-form button, #required-data-form button");
  buttons.forEach((button) => { button.disabled = true; });
  questionForm.setAttribute("aria-busy", "true");
  requiredDataForm.setAttribute("aria-busy", "true");
  setRequestLock(true);
  requiredData.hidden = true;
  resultSection.hidden = true;
  inspector.hidden = true;
  document.body.classList.remove("has-decision", "inspector-open");
  document.body.classList.add("has-active-decision");
  setError("");
  setStatus("요청 확인 중", "checking");
  setProgress("request");
  try {
    const preflight = await fetch("/api/research-needed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: state.question }),
    });
    if (!preflight.ok) throw new Error("현재 정보 확인 여부를 알 수 없습니다.");
    if ((await preflight.json()).needed) {
      setStatus("정보 조사 중", "researching");
      setProgress("work");
    } else {
      setStatus("추가 정보 확인 중", "checking");
      setProgress("details");
    }
    const response = await fetch("/api/decisions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: state.question, data: state.data }),
    });
    const decision = await response.json();
    if (!response.ok) throw new Error(decision.detail || "결정 요청을 완료하지 못했습니다.");
    state.decision = decision;
    if (decision.status === "needs_input") {
      setStatus("추가 정보 필요", "needs-input");
      setProgress("details");
      renderRequiredData(decision.missing_fields);
    } else if (decision.status === "ready") {
      renderDecisionResult(decision);
      renderInspector();
      setStatus("준비됨", "ready");
      setProgress("result");
      resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      renderDecisionResult(decision);
      setStatus("검토 필요", "review-needed");
      setProgress("result");
    }
  } catch (cause) {
    setError(cause.message);
    setStatus("추가 정보 필요", "needs-input");
  } finally {
    state.requestInFlight = false;
    setRequestLock(false);
    buttons.forEach((button) => { button.disabled = false; });
    questionForm.removeAttribute("aria-busy");
    requiredDataForm.removeAttribute("aria-busy");
  }
}

questionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  state.question = question.value.trim();
  state.data = {};
  if (state.question) await requestDecision();
});

requiredDataForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  updateDataFromForm();
  await requestDecision();
});

renderScenarioGroups();
question.placeholder = scenarioDefinitions[new Date().getDate() % scenarioDefinitions.length].promptTemplate;

scenarioGroupsContainer.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-scenario-group]");
  if (tab) {
    state.activeScenarioGroup = tab.dataset.scenarioGroup;
    renderScenarioGroups();
    return;
  }
  const card = event.target.closest("[data-scenario-id]");
  if (!card) return;
  selectScenario(scenarioById.get(card.dataset.scenarioId));
});

question.addEventListener("keydown", (event) => {
  if (event.key !== "Tab" || !state.scenarioId || activePlaceholderIndex < 0) return;
  const placeholders = placeholderRanges();
  const nextIndex = event.shiftKey ? activePlaceholderIndex - 1 : activePlaceholderIndex + 1;
  if (nextIndex < 0 || nextIndex >= placeholders.length) return;
  event.preventDefault();
  selectPlaceholder(nextIndex);
});

setProgress("request");

document.querySelector("[data-new-decision]").addEventListener("click", () => {
  state.question = "";
  state.data = {};
  state.decision = null;
  state.scenarioId = null;
  activePlaceholderIndex = -1;
  question.value = "";
  templateGuidance.hidden = true;
  setScenarioSelection("");
  requiredData.hidden = true;
  resultSection.hidden = true;
  inspector.hidden = true;
  document.body.classList.remove("has-decision", "has-active-decision", "inspector-open");
  setProgress("request");
  setError("");
  setStatus("준비됨", "ready");
});

document.querySelector("[data-inspect]").addEventListener("click", () => {
  if (inspector.hidden) {
    renderInspector();
    document.querySelector("#close-inspector").focus();
  } else {
    inspector.hidden = true;
    document.body.classList.remove("inspector-open");
  }
});
document.querySelector("#close-inspector").addEventListener("click", () => {
  inspector.hidden = true;
  document.body.classList.remove("inspector-open");
});
