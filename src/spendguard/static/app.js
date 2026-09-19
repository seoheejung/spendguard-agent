const state = { question: "", data: {}, decision: null };

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

const questionForm = document.querySelector("#decision-form");
const question = document.querySelector("#question");
const requiredData = document.querySelector("#required-data");
const requiredDataForm = document.querySelector("#required-data-form");
const requiredDataFields = document.querySelector("#required-data-fields");
const resultSection = document.querySelector("#decision-result");
const decisionCards = document.querySelector("#decision-cards");
const progress = document.querySelector("#decision-progress");
const status = document.querySelector("#decision-status");
const error = document.querySelector("#error");
const inspector = document.querySelector("#inspector");
const inspectorContent = document.querySelector("#inspector-content");

function setStatus(value) {
  status.textContent = value;
  status.dataset.status = value.toLowerCase().replaceAll(" ", "-");
}

function setProgress(active) {
  progress.hidden = false;
  const steps = ["request", "details", "work", "result"];
  const activeIndex = steps.indexOf(active);
  document.querySelectorAll("[data-progress]").forEach((step) => {
    step.dataset.state = steps.indexOf(step.dataset.progress) <= activeIndex ? "active" : "pending";
  });
}

function setError(message) {
  error.textContent = message;
  error.hidden = !message;
}

function listCard(title, values, className = "") {
  const card = document.createElement("article");
  card.className = `result-card solid-panel ${className}`;
  card.append(Object.assign(document.createElement("h3"), { textContent: title }));
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
    term.textContent = key.replaceAll("_", " ");
    const detail = document.createElement("dd");
    detail.textContent = typeof value === "object" ? Object.values(value).join(", ") : String(value);
    list.append(term, detail);
  }
  return list;
}

function keyNumbers(decision) {
  const values = {};
  for (const entry of decision.calculations) {
    for (const [key, value] of Object.entries(entry.calculation.result)) {
      if (key !== "currency" && typeof value !== "object") values[key.replaceAll("_", " ")] = value;
    }
  }
  return values;
}

function renderDecisionResult(decision) {
  decisionCards.replaceChildren();
  const conclusion = document.createElement("article");
  conclusion.className = "result-card solid-panel conclusion-card";
  conclusion.append(
    Object.assign(document.createElement("p"), { className: "eyebrow", textContent: decision.status === "needs_input" ? "NEXT STEP" : "CONCLUSION" }),
    Object.assign(document.createElement("p"), { textContent: decision.conclusion }),
  );
  decisionCards.append(conclusion);

  const numbers = keyNumbers(decision);
  if (Object.keys(numbers).length) {
    const card = document.createElement("article");
    card.className = "result-card solid-panel key-number-card";
    card.append(Object.assign(document.createElement("h3"), { textContent: "Key numbers" }), valueRows(numbers));
    decisionCards.append(card);
  }
  if (decision.options.length) decisionCards.append(listCard("Options", decision.options));
  if (decision.risks.length) decisionCards.append(listCard("Risks", decision.risks));
  if (decision.next_actions.length) decisionCards.append(listCard("Next actions", decision.next_actions));
  resultSection.hidden = false;
}

function definitionFor(missingField) {
  return fieldDefinitions[missingField] || { label: missingField.replaceAll("_", " "), type: "text" };
}

function renderRequiredData(missingFields) {
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
      Object.assign(document.createElement("p"), { className: "form-note", textContent: `Retrieved: ${source.retrieved_at}` }),
    );
    list.append(item);
  }
  return list;
}

function renderInspector() {
  const decision = state.decision;
  if (!decision) return;
  inspectorContent.replaceChildren();
  inspectorContent.append(inspectorSection("Facts", listCard("", [...decision.facts, ...enteredFacts()])));
  if (decision.calculations.length) {
    const calculations = document.createElement("div");
    for (const calculation of decision.calculations) {
      const item = document.createElement("article");
      item.className = "trace-item";
      item.append(Object.assign(document.createElement("h4"), { textContent: calculationLabels[calculation.tool] || "Calculation" }), valueRows(calculation.calculation.result));
      calculations.append(item);
    }
    inspectorContent.append(inspectorSection("Calculations", calculations));
  }
  if (decision.sources.length) inspectorContent.append(inspectorSection("Sources", sourceList(decision.sources)));
  if (decision.assumptions.length) inspectorContent.append(inspectorSection("Assumptions", listCard("", decision.assumptions)));

  const technical = document.createElement("details");
  technical.className = "technical-details";
  technical.append(Object.assign(document.createElement("summary"), { textContent: "Technical details" }));
  const content = document.createElement("div");
  content.append(Object.assign(document.createElement("p"), { textContent: `Decision type: ${decision.pack || "unknown"}` }));
  for (const calculation of decision.calculations) {
    content.append(
      Object.assign(document.createElement("p"), { textContent: `Tool: ${calculation.tool}` }),
      Object.assign(document.createElement("code"), { textContent: calculation.calculation.formula }),
    );
  }
  technical.append(content);
  inspectorContent.append(technical);
  inspector.hidden = false;
}

async function requestDecision() {
  const button = document.querySelector("#decision-form button");
  button.disabled = true;
  requiredData.hidden = true;
  resultSection.hidden = true;
  setError("");
  setStatus("Checking your request");
  setProgress("request");
  try {
    const preflight = await fetch("/api/research-needed", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: state.question }),
    });
    if (!preflight.ok) throw new Error("현재 정보 확인 여부를 알 수 없습니다.");
    if ((await preflight.json()).needed) {
      setStatus("Researching");
      setProgress("work");
    } else {
      setStatus("Checking details");
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
    renderDecisionResult(decision);
    if (decision.status === "needs_input") {
      setStatus("Needs input");
      setProgress("details");
      renderRequiredData(decision.missing_fields);
    } else if (decision.status === "ready") {
      setStatus("Ready");
      setProgress("result");
      resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
    } else {
      setStatus("Review needed");
      setProgress("result");
    }
  } catch (cause) {
    setError(cause.message);
    setStatus("Needs input");
  } finally {
    button.disabled = false;
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

document.querySelectorAll("[data-template]").forEach((button) => {
  button.addEventListener("click", () => {
    question.value = button.dataset.template;
    question.focus();
    document.querySelector("#question-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

document.querySelector("[data-new-decision]").addEventListener("click", () => {
  state.question = "";
  state.data = {};
  state.decision = null;
  question.value = "";
  requiredData.hidden = true;
  resultSection.hidden = true;
  progress.hidden = true;
  inspector.hidden = true;
  setError("");
  setStatus("Ready to help");
});

document.querySelector("[data-inspect]").addEventListener("click", () => {
  renderInspector();
  document.querySelector("#close-inspector").focus();
});
document.querySelector("#close-inspector").addEventListener("click", () => { inspector.hidden = true; });
