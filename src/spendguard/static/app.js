const state = { question: "", decision: null, turns: [], conversationId: null, activeRecordId: null, viewingHistoryId: null, historyDisabled: false, scenarioId: null, activeScenarioGroup: "사기 전에", requestInFlight: false };

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

const questionForm = document.querySelector("#decision-form");
const question = document.querySelector("#question");
const resultSection = document.querySelector("#decision-result");
const followUpActions = document.querySelector("#follow-up-actions");
const workflowPanel = document.querySelector("#workflow-panel");
const workflowState = document.querySelector("#workflow-state");
const workflowMetrics = document.querySelector("#workflow-metrics");
const decisionCards = document.querySelector("#decision-cards");
const status = document.querySelector("#decision-status");
const error = document.querySelector("#error");
const scenarioGroupsContainer = document.querySelector("#scenario-groups");
const templateGuidance = document.querySelector("#template-guidance");
const workspace = document.querySelector("#workspace");
const siteHeader = document.querySelector(".site-header");
const processingBlocker = document.querySelector("#processing-blocker");
const processingMessage = document.querySelector("#processing-message");
const cancelRequest = document.querySelector("#cancel-request");
const processingDetail = document.querySelector("#processing-detail");
const originalQuestion = document.querySelector("#original-question");
const originalQuestionText = document.querySelector("#original-question-text");
const showFollowUp = document.querySelector("#show-follow-up");
const followUpForm = document.querySelector("#follow-up-form");
const followUpQuestion = document.querySelector("#follow-up-question");
const followUpSuggestions = document.querySelector("#follow-up-suggestions");
const historyPanel = document.querySelector("#history-panel");
const historyList = document.querySelector("#history-list");
const historyEmpty = document.querySelector("#history-empty");
const historyTrigger = document.querySelector("#open-history");
const clearHistoryButton = document.querySelector("#clear-history");
const historyDetail = document.querySelector("#history-detail");
const historyDetailDate = document.querySelector("#history-detail-date");
const returnActiveDecision = document.querySelector("#return-active-decision");
const historySources = document.querySelector("#history-sources");
const historySuggestions = document.querySelector("#history-suggestions");
const HISTORY_KEY = "spendguard:decision-history:v1";
const HISTORY_LIMIT = 30;
const REQUEST_WAIT_LIMIT_MS = 250_000;
let activeRequestController = null;

function readDecisionHistory() {
  try {
    const records = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(records)
      ? records.filter((record) => record && typeof record.id === "string"
        && typeof record.firstQuestion === "string" && typeof record.answer === "string")
        .slice(0, HISTORY_LIMIT)
      : [];
  } catch {
    return [];
  }
}

function writeDecisionHistory(records) {
  const retained = records.slice(0, HISTORY_LIMIT);
  if (!retained.length) {
    try {
      localStorage.setItem(HISTORY_KEY, "[]");
      return true;
    } catch {
      return false;
    }
  }
  while (retained.length) {
    try {
      localStorage.setItem(HISTORY_KEY, JSON.stringify(retained));
      return true;
    } catch {
      retained.pop();
    }
  }
  return false;
}

function historyTitle(questionText) {
  const line = questionText.split(/\r?\n/).map((item) => item.trim()).find(Boolean) || "소비 판단";
  const characters = Array.from(line);
  return characters.length > 52 ? `${characters.slice(0, 52).join("")}…` : line;
}

function historyDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, "0")}.${String(date.getDate()).padStart(2, "0")}`;
}

function historySourcesFrom(decision) {
  return Array.isArray(decision.sources)
    ? decision.sources.filter((source) => source && typeof source.url === "string" && /^https?:\/\//.test(source.url))
      .slice(0, 12).map((source) => ({ title: String(source.title || source.url), url: source.url }))
    : [];
}

function saveDecisionRecord(decision, askedQuestion, isFollowUp) {
  if (state.historyDisabled) return;
  const now = new Date().toISOString();
  const records = readDecisionHistory();
  const index = records.findIndex((record) => record.id === state.activeRecordId);
  const firstTurn = state.turns[0];
  const record = index >= 0 ? records.splice(index, 1)[0] : {
    id: crypto.randomUUID(),
    title: historyTitle(firstTurn?.question || askedQuestion),
    firstQuestion: firstTurn?.question || askedQuestion,
    answer: firstTurn?.answer || decision.answer,
    suggestedFollowups: [],
    sources: [],
    latestFollowup: null,
    createdAt: now,
    updatedAt: now,
  };
  if (isFollowUp) record.latestFollowup = { question: askedQuestion, answer: decision.answer };
  record.suggestedFollowups = Array.isArray(decision.suggested_followups)
    ? decision.suggested_followups.filter((item) => typeof item === "string" && item.trim()).slice(0, 3)
    : [];
  const sources = historySourcesFrom(decision);
  if (sources.length) record.sources = sources;
  record.updatedAt = now;
  if (writeDecisionHistory([record, ...records])) state.activeRecordId = record.id;
}

function fitQuestionHeight() {
  question.style.height = "auto";
  const height = Math.min(320, Math.max(44, question.scrollHeight));
  question.style.height = `${height}px`;
  question.style.overflowY = question.scrollHeight > 320 ? "auto" : "hidden";
}

const progressMessages = {
  queued: "답변을 준비하고 있어요.",
  thinking: "질문을 살펴보고 있어요.",
  searching: "현재 정보를 확인하고 있어요.",
  calculating: "비용을 계산하고 있어요.",
  writing: "답변을 정리하고 있어요.",
};

function setStatus(value, name) {
  status.querySelector(".status-label").textContent = value;
  status.dataset.status = name;
}

function setProgress(message) {
  processingMessage.textContent = message;
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
  fitQuestionHeight();
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

function appendAnswerInline(parent, text) {
  const markup = /\*\*([^*]+)\*\*|\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
  let position = 0;
  for (const match of text.matchAll(markup)) {
    parent.append(document.createTextNode(text.slice(position, match.index)));
    if (match[1]) {
      const strong = document.createElement("strong");
      strong.textContent = match[1];
      parent.append(strong);
    } else {
      const link = document.createElement("a");
      link.href = match[3];
      link.target = "_blank";
      link.rel = "noreferrer noopener";
      link.textContent = match[2];
      parent.append(link);
    }
    position = match.index + match[0].length;
  }
  parent.append(document.createTextNode(text.slice(position)));
}

function renderAnswer(text) {
  const body = document.createElement("div");
  body.className = "answer-body";
  const lines = String(text).trim().split(/\r?\n/);
  let list = null;
  let paragraph = null;
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index];
    const trimmed = line.trim();
    if (!trimmed) {
      list = null;
      paragraph = null;
      continue;
    }
    if (trimmed.startsWith("|") && /^\|[\s:|-]+\|$/.test((lines[index + 1] || "").trim())) {
      list = null;
      paragraph = null;
      const wrapper = document.createElement("div");
      wrapper.className = "answer-table-wrap";
      const table = document.createElement("table");
      const rows = [trimmed];
      index += 2;
      while (index < lines.length && lines[index].trim().startsWith("|")) {
        rows.push(lines[index].trim());
        index += 1;
      }
      index -= 1;
      for (const [rowIndex, row] of rows.entries()) {
        const tr = document.createElement("tr");
        for (const cell of row.slice(1, -1).split("|")) {
          const element = document.createElement(rowIndex === 0 ? "th" : "td");
          appendAnswerInline(element, cell.trim());
          tr.append(element);
        }
        table.append(tr);
      }
      wrapper.append(table);
      body.append(wrapper);
      continue;
    }
    const heading = trimmed.match(/^#{1,4}\s+(.+)$/);
    if (heading) {
      list = null;
      paragraph = null;
      const element = document.createElement("h3");
      appendAnswerInline(element, heading[1]);
      body.append(element);
      continue;
    }
    const bullet = trimmed.match(/^[-*]\s+(.+)$/);
    const numbered = trimmed.match(/^\d+[.)]\s+(.+)$/);
    if (bullet || numbered) {
      paragraph = null;
      const tag = bullet ? "ul" : "ol";
      if (!list || list.tagName.toLowerCase() !== tag) {
        list = document.createElement(tag);
        body.append(list);
      }
      const item = document.createElement("li");
      appendAnswerInline(item, (bullet || numbered)[1]);
      list.append(item);
      continue;
    }
    list = null;
    if (trimmed.startsWith("> ")) {
      paragraph = null;
      const quote = document.createElement("blockquote");
      appendAnswerInline(quote, trimmed.slice(2));
      body.append(quote);
      continue;
    }
    if (!paragraph) {
      paragraph = document.createElement("p");
      body.append(paragraph);
    } else {
      paragraph.append(document.createTextNode(" "));
    }
    appendAnswerInline(paragraph, trimmed);
  }
  return body;
}

function renderDecisionResult(decision, askedQuestion, isFollowUp) {
  if (!isFollowUp) decisionCards.replaceChildren();
  if (isFollowUp) {
    const followUpCard = document.createElement("div");
    followUpCard.className = "follow-up-question-card";
    followUpCard.append(
      Object.assign(document.createElement("span"), { textContent: "추가 질문" }),
      Object.assign(document.createElement("p"), { textContent: askedQuestion }),
    );
    decisionCards.append(followUpCard);
  }
  const conclusion = document.createElement("article");
  conclusion.className = `result-card solid-panel conclusion-card${isFollowUp ? " follow-up-answer" : ""}`;
  conclusion.append(renderAnswer(decision.answer));
  decisionCards.append(conclusion);
  resultSection.hidden = false;
  followUpActions.hidden = false;
  const suggestions = Array.isArray(decision.suggested_followups)
    ? decision.suggested_followups.filter((item) => typeof item === "string" && item.trim()).slice(0, 3)
    : [];
  followUpSuggestions.replaceChildren(...suggestions.map((suggestion) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "suggestion-chip";
    chip.textContent = suggestion;
    chip.addEventListener("click", () => {
      followUpQuestion.value = suggestion;
      followUpQuestion.focus();
    });
    return chip;
  }));
  followUpQuestion.placeholder = suggestions[0] || "이 결과에서 더 궁금한 점을 물어보세요.";
  showFollowUp.hidden = false;
  document.body.classList.add("has-decision", "has-active-decision");
}

function renderDecisionHistory() {
  const records = readDecisionHistory();
  historyEmpty.hidden = records.length > 0;
  clearHistoryButton.hidden = records.length === 0;
  historyList.replaceChildren(...records.map((record) => {
    const item = document.createElement("article");
    item.className = "history-item";
    const open = document.createElement("a");
    open.className = "history-item-open";
    open.dataset.historyId = record.id;
    open.href = `#history/${encodeURIComponent(record.id)}`;
    const heading = document.createElement("span");
    heading.className = "history-item-heading";
    heading.append(
      Object.assign(document.createElement("strong"), { textContent: record.title || historyTitle(record.firstQuestion) }),
      Object.assign(document.createElement("time"), { textContent: historyDate(record.updatedAt || record.createdAt), dateTime: record.updatedAt || record.createdAt }),
    );
    const preview = document.createElement("span");
    preview.className = "history-item-preview";
    const summary = typeof record.latestFollowup?.answer === "string" ? record.latestFollowup.answer : record.answer;
    preview.textContent = summary.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/[#*|]/g, "").trim().slice(0, 130);
    open.append(heading, preview);
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "history-item-delete";
    remove.dataset.deleteHistoryId = record.id;
    remove.textContent = "삭제";
    remove.setAttribute("aria-label", `${record.title || historyTitle(record.firstQuestion)} 기록 삭제`);
    item.append(open, remove);
    return item;
  }));
}

function setHistoryOpen(open) {
  if (open && state.requestInFlight) return;
  historyPanel.hidden = !open;
  historyTrigger.setAttribute("aria-expanded", String(open));
  document.body.classList.toggle("history-open", open);
  if (open) {
    renderDecisionHistory();
    historyPanel.scrollIntoView({ block: "start" });
  }
}

function syncHistoryLocation() {
  let route;
  try {
    route = decodeURIComponent(window.location.hash.slice(1));
  } catch {
    route = "";
  }
  if (route === "history") {
    setHistoryOpen(true);
    return;
  }
  if (route.startsWith("history/")) {
    const record = readDecisionHistory().find((item) => item.id === route.slice(8));
    if (record) {
      showDecisionRecord(record);
      return;
    }
    window.history.replaceState(null, "", "#history");
    setHistoryOpen(true);
    return;
  }
  setHistoryOpen(false);
  if (state.viewingHistoryId) {
    if (state.turns.length) restoreActiveDecision();
    else resetDecision();
  }
}

function showDecisionRecord(record) {
  setHistoryOpen(false);
  state.viewingHistoryId = record.id;
  document.body.classList.add("viewing-history");
  originalQuestionText.textContent = record.firstQuestion;
  originalQuestion.hidden = false;
  renderDecisionResult({ answer: record.answer, suggested_followups: [] }, record.firstQuestion, false);
  if (record.latestFollowup?.question && record.latestFollowup?.answer) {
    renderDecisionResult({ answer: record.latestFollowup.answer, suggested_followups: [] }, record.latestFollowup.question, true);
  }
  followUpActions.hidden = true;
  followUpForm.hidden = true;
  showFollowUp.hidden = true;
  workflowPanel.hidden = true;
  historyDetailDate.textContent = `처음 저장 ${historyDate(record.createdAt)} · 최근 수정 ${historyDate(record.updatedAt)}`;
  returnActiveDecision.hidden = !state.turns.length;
  historySources.replaceChildren();
  for (const source of Array.isArray(record.sources) ? record.sources : []) {
    if (!source || typeof source.url !== "string" || !/^https?:\/\//.test(source.url)) continue;
    const link = document.createElement("a");
    link.href = source.url;
    link.target = "_blank";
    link.rel = "noreferrer noopener";
    link.textContent = typeof source.title === "string" && source.title ? source.title : source.url;
    historySources.append(link);
  }
  historySources.hidden = !historySources.childElementCount;
  historySuggestions.replaceChildren(...(Array.isArray(record.suggestedFollowups)
    ? record.suggestedFollowups.filter((item) => typeof item === "string" && item.trim()).slice(0, 3)
    : []).map((suggestion) => Object.assign(document.createElement("span"), { className: "suggestion-chip", textContent: suggestion })));
  historySuggestions.hidden = !historySuggestions.childElementCount;
  historyDetail.hidden = false;
  setError("");
  setStatus("서비스 정상 운영 중", "ready");
  originalQuestion.scrollIntoView({ block: "start" });
}

function restoreActiveDecision() {
  if (!state.turns.length) return;
  state.viewingHistoryId = null;
  document.body.classList.remove("viewing-history");
  originalQuestionText.textContent = state.turns[0].question;
  originalQuestion.hidden = false;
  for (const [index, turn] of state.turns.entries()) {
    renderDecisionResult({
      answer: turn.answer,
      suggested_followups: index === state.turns.length - 1 ? state.decision?.suggested_followups : [],
    }, turn.question, index > 0);
  }
  historyDetail.hidden = true;
  followUpActions.hidden = false;
  followUpForm.hidden = false;
  showFollowUp.hidden = true;
  workflowPanel.hidden = false;
  originalQuestion.scrollIntoView({ block: "start" });
}

async function requestDecision(askedQuestion, isFollowUp = false) {
  if (state.requestInFlight || state.viewingHistoryId) return;
  state.requestInFlight = true;
  const controller = new AbortController();
  activeRequestController = controller;
  const requestId = crypto.randomUUID();
  const startedAt = performance.now();
  let progressInFlight = false;
  let timedOut = false;
  const timer = window.setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_WAIT_LIMIT_MS);
  const elapsedTimer = window.setInterval(() => {
    processingDetail.textContent = `경과 시간 ${Math.floor((performance.now() - startedAt) / 1000)}초`;
  }, 1000);
  const progressTimer = window.setInterval(async () => {
    if (progressInFlight || controller.signal.aborted) return;
    progressInFlight = true;
    try {
      const response = await fetch(`/api/decisions/progress/${requestId}`, { signal: controller.signal, cache: "no-store" });
      if (response.ok) {
        const progress = await response.json();
        if (progressMessages[progress.stage]) setProgress(progressMessages[progress.stage]);
      }
    } catch {
      // The decision request handles connection errors.
    } finally {
      progressInFlight = false;
    }
  }, 3000);
  const submit = isFollowUp ? followUpForm.querySelector("button[type=submit]") : questionForm.querySelector("button[type=submit]");
  submit.disabled = true;
  (isFollowUp ? followUpForm : questionForm).setAttribute("aria-busy", "true");
  setRequestLock(true);
  if (!isFollowUp) {
    resultSection.hidden = true;
    followUpActions.hidden = true;
    workflowPanel.hidden = true;
    document.body.classList.remove("has-decision");
  }
  document.body.classList.add("has-active-decision");
  setError("");
  setStatus("분석 중", "checking");
  setProgress("질문을 분석하고 있어요.");
  processingDetail.textContent = "경과 시간 0초";
  try {
    const history = state.turns.length <= 6
      ? state.turns
      : [state.turns[0], ...state.turns.slice(-5)];
    const response = await fetch("/api/decisions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: askedQuestion, mode: "jev", history: isFollowUp ? history : [], conversation_id: isFollowUp ? state.conversationId : null, request_id: requestId }),
      signal: controller.signal,
    });
    if (!response.ok) {
      const failure = await response.json().catch(() => ({}));
      if (response.status === 429 && failure.detail?.code === "codex_usage_limit") {
        throw new Error("codex_usage_limit");
      }
      throw new Error("Decision request failed");
    }
    const decision = await response.json();
    if (decision.status !== "ready" || !decision.answer) throw new Error("Decision answer missing");
    state.decision = decision;
    state.conversationId = decision.metadata?.conversation_id || state.conversationId;
    state.turns.push({ question: askedQuestion, answer: decision.answer });
    if (!isFollowUp) {
      originalQuestionText.textContent = askedQuestion;
      originalQuestion.hidden = false;
    } else {
      followUpQuestion.value = "";
      followUpForm.hidden = true;
    }
    renderDecisionResult(decision, askedQuestion, isFollowUp);
    workflowPanel.hidden = false;
    workflowState.textContent = "✓ 완료";
    const metrics = decision.metadata || {};
    const searchCount = metrics.search_calls ?? 0;
    const calculationCount = metrics.mcp_calls?.filter((call) => call.tool !== "update_decision_state").length ?? 0;
    const steps = workflowPanel.querySelectorAll(".workflow-steps li");
    steps[1].querySelector("small").textContent = searchCount ? `${searchCount}회 검색했어요.` : "이번 질문은 검색이 필요하지 않았어요.";
    steps[2].querySelector("small").textContent = calculationCount ? `${calculationCount}회 계산했어요.` : "별도 금액 계산이 필요하지 않았어요.";
    workflowMetrics.textContent = `검색 ${searchCount}회 · 계산 ${calculationCount}회 · 총 ${Math.round((metrics.latency_ms || 0) / 1000)}초`;
    followUpForm.hidden = false;
    showFollowUp.hidden = true;
    setStatus("서비스 정상 운영 중", "ready");
    saveDecisionRecord(decision, askedQuestion, isFollowUp);
    (isFollowUp ? decisionCards.lastElementChild : resultSection).scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (requestError) {
    setError(controller.signal.aborted
      ? (timedOut ? "분석 시간이 길어져 요청을 종료했어요. 다시 시도해 주세요." : "분석을 중단했어요.")
      : requestError.message === "codex_usage_limit"
        ? "현재 Codex 사용 한도에 도달했습니다. 초기화 후 다시 시도해 주세요."
      : "분석 중 문제가 생겼어요. 잠시 후 다시 시도해 주세요.");
    setStatus("분석을 완료하지 못했어요", "error");
  } finally {
    window.clearTimeout(timer);
    window.clearInterval(elapsedTimer);
    window.clearInterval(progressTimer);
    if (activeRequestController === controller) activeRequestController = null;
    state.requestInFlight = false;
    setRequestLock(false);
    submit.disabled = false;
    (isFollowUp ? followUpForm : questionForm).removeAttribute("aria-busy");
  }
}

cancelRequest.addEventListener("click", () => activeRequestController?.abort());
questionForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  state.question = question.value.trim();
  if (state.question) await requestDecision(state.question);
});
showFollowUp.addEventListener("click", () => {
  showFollowUp.hidden = true;
  followUpForm.hidden = false;
  followUpQuestion.focus();
  followUpForm.scrollIntoView({ behavior: "smooth", block: "nearest" });
});
followUpForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const nextQuestion = followUpQuestion.value.trim();
  if (nextQuestion) await requestDecision(nextQuestion, true);
});

renderScenarioGroups();
question.placeholder = scenarioDefinitions[new Date().getDate() % scenarioDefinitions.length].promptTemplate;
fitQuestionHeight();
question.addEventListener("input", fitQuestionHeight);
window.addEventListener("resize", fitQuestionHeight);
scenarioGroupsContainer.addEventListener("click", (event) => {
  const tab = event.target.closest("[data-scenario-group]");
  if (tab) {
    state.activeScenarioGroup = tab.dataset.scenarioGroup;
    renderScenarioGroups();
    return;
  }
  const card = event.target.closest("[data-scenario-id]");
  if (card) selectScenario(scenarioById.get(card.dataset.scenarioId));
});
question.addEventListener("keydown", (event) => {
  if (event.key !== "Tab" || !state.scenarioId || activePlaceholderIndex < 0) return;
  const placeholders = placeholderRanges();
  const nextIndex = event.shiftKey ? activePlaceholderIndex - 1 : activePlaceholderIndex + 1;
  if (nextIndex < 0 || nextIndex >= placeholders.length) return;
  event.preventDefault();
  selectPlaceholder(nextIndex);
});
function resetDecision() {
  state.question = "";
  state.decision = null;
  state.turns = [];
  state.conversationId = null;
  state.activeRecordId = null;
  state.viewingHistoryId = null;
  state.historyDisabled = false;
  state.scenarioId = null;
  activePlaceholderIndex = -1;
  question.value = "";
  fitQuestionHeight();
  templateGuidance.hidden = true;
  setScenarioSelection("");
  resultSection.hidden = true;
  followUpActions.hidden = true;
  workflowPanel.hidden = true;
  originalQuestion.hidden = true;
  showFollowUp.hidden = true;
  followUpForm.hidden = true;
  followUpQuestion.value = "";
  decisionCards.replaceChildren();
  historyDetail.hidden = true;
  document.body.classList.remove("has-decision", "has-active-decision", "viewing-history");
  setError("");
  setStatus("서비스 정상 운영 중", "ready");
}

window.addEventListener("hashchange", syncHistoryLocation);
returnActiveDecision.addEventListener("click", () => { window.location.hash = "question"; });
historyList.addEventListener("click", (event) => {
  const remove = event.target.closest("[data-delete-history-id]");
  if (remove) {
    const id = remove.dataset.deleteHistoryId;
    writeDecisionHistory(readDecisionHistory().filter((record) => record.id !== id));
    if (state.activeRecordId === id) {
      state.activeRecordId = null;
      state.historyDisabled = true;
    }
    if (state.viewingHistoryId === id) {
      if (state.turns.length) restoreActiveDecision();
      else resetDecision();
    }
    renderDecisionHistory();
    return;
  }
});
clearHistoryButton.addEventListener("click", () => {
  if (!window.confirm("최근 소비 판단 기록을 모두 삭제할까요?")) return;
  try {
    localStorage.removeItem(HISTORY_KEY);
  } catch {
    return;
  }
  if (state.activeRecordId) state.historyDisabled = true;
  state.activeRecordId = null;
  if (state.viewingHistoryId) {
    if (state.turns.length) restoreActiveDecision();
    else resetDecision();
  }
  renderDecisionHistory();
});
document.querySelector("[data-new-decision]").addEventListener("click", () => {
  setHistoryOpen(false);
  resetDecision();
});
syncHistoryLocation();
