const toolDefinitions = {
  calculate_installment: {
    label: "할부 비용",
    hint: "원리금 균등 월 납입금, 총 납입금, 총 이자",
    fields: [["principal", "원금", "number"], ["annual_interest_rate_pct", "연 이자율 (%)", "number"], ["term_months", "기간 (개월)", "number"], ["currency", "통화", "text"]],
  },
  calculate_refinance: {
    label: "대출 변경 비용",
    hint: "기존 잔여 비용과 신규 잔여 비용 비교",
    fields: [["remaining_principal", "남은 원금", "number"], ["current_annual_interest_rate_pct", "기존 연 이자율 (%)", "number"], ["current_remaining_months", "기존 남은 기간 (개월)", "number"], ["new_annual_interest_rate_pct", "신규 연 이자율 (%)", "number"], ["new_term_months", "신규 기간 (개월)", "number"], ["refinancing_fee", "변경 수수료", "number"], ["currency", "통화", "text"]],
  },
  calculate_usage_cost: {
    label: "사용당 비용",
    hint: "총비용과 사용 단위 기준",
    fields: [["total_cost", "총비용", "number"], ["units", "사용 단위", "number"], ["currency", "통화", "text"]],
  },
  annualize_expense: {
    label: "연간 비용",
    hint: "기간 지출의 연간 환산",
    fields: [["amount", "금액", "number"], ["period_months", "기간 (개월)", "number"], ["currency", "통화", "text"]],
  },
  calculate_tco: {
    label: "TCO",
    hint: "구매비, 월 보유비, 추가 비용 기준",
    fields: [["purchase_cost", "구매비", "number"], ["monthly_ownership_cost", "월 보유비", "number"], ["ownership_months", "보유 기간 (개월)", "number"], ["additional_cost", "추가 비용", "number"], ["currency", "통화", "text"]],
  },
  compare_costs: {
    label: "비용 비교",
    hint: "선택지 목록 JSON: [{\"name\": \"A\", \"total_cost\": \"100\"}]",
    fields: [["options", "선택지 목록 (JSON)", "json"], ["currency", "통화", "text"]],
  },
};

const state = { agent: null, calculation: null };
const form = document.querySelector("#analysis-form");
const question = document.querySelector("#question");
const agentStatus = document.querySelector("#agent-status");
const decisionStatus = document.querySelector("#decision-status");
const error = document.querySelector("#error");
const calculationForm = document.querySelector("#calculation-form");
const calculationTool = document.querySelector("#calculation-tool");
const calculationFields = document.querySelector("#calculation-fields");
const calculationHint = document.querySelector("#calculation-hint");
const inspector = document.querySelector("#inspector");
const inspectorContent = document.querySelector("#inspector-content");

function setDecisionStatus(value) {
  decisionStatus.textContent = value;
  decisionStatus.dataset.status = value.toLowerCase().replace(" ", "-");
}

function setError(message) {
  error.textContent = message;
  error.hidden = !message;
}

function listCard(title, values) {
  const card = document.createElement("article");
  card.className = "result-card solid-panel";
  const heading = document.createElement("h3");
  heading.textContent = title;
  const list = document.createElement("ul");
  for (const value of values.length ? values : ["없음"]) {
    const item = document.createElement("li");
    item.textContent = value;
    list.append(item);
  }
  card.append(heading, list);
  return card;
}

function renderAgentResult(result) {
  const cards = document.querySelector("#agent-cards");
  cards.replaceChildren();
  const conclusion = document.createElement("article");
  conclusion.className = "result-card solid-panel conclusion-card";
  const intent = document.createElement("h3");
  intent.textContent = result.intent;
  const summary = document.createElement("p");
  summary.textContent = result.summary;
  conclusion.append(Object.assign(document.createElement("p"), { className: "eyebrow", textContent: "INTENT" }), intent, summary);
  cards.append(conclusion, listCard("확인된 사실", result.known_facts), listCard("추가 필요 정보", result.missing_fields), listCard("가정", result.assumptions));
  document.querySelector("#agent-result").hidden = false;
}

function renderSources(result) {
  const section = document.querySelector("#sources");
  const cards = document.querySelector("#source-cards");
  cards.replaceChildren();
  if (!result.research || !result.research.needed) {
    section.hidden = true;
    return;
  }

  document.querySelector("#research-status").textContent = result.research.status;
  document.querySelector("#research-note").textContent = result.research.note;
  for (const fact of result.external_facts) {
    const card = document.createElement("article");
    card.className = "result-card solid-panel";
    const value = document.createElement("p");
    value.textContent = fact.value;
    const source = document.createElement("a");
    source.href = fact.source_url;
    source.target = "_blank";
    source.rel = "noreferrer";
    source.textContent = fact.source_name;
    const retrieved = document.createElement("p");
    retrieved.className = "form-note";
    retrieved.textContent = `Retrieved: ${fact.retrieved_at}`;
    card.append(Object.assign(document.createElement("h3"), { textContent: "확인 사실" }), value, source, retrieved);
    cards.append(card);
  }
  if (!result.external_facts.length) cards.append(listCard("확인 사실", ["확정 가능한 외부 사실이 없습니다."]));
  section.hidden = false;
}

function valueRows(values) {
  const list = document.createElement("dl");
  list.className = "value-list";
  for (const [key, value] of Object.entries(values)) {
    const term = document.createElement("dt");
    term.textContent = key;
    const detail = document.createElement("dd");
    detail.textContent = typeof value === "object" ? JSON.stringify(value) : String(value);
    list.append(term, detail);
  }
  return list;
}

function renderCalculationResult(result) {
  const cards = document.querySelector("#calculation-cards");
  cards.replaceChildren();
  const calculation = result.calculation;
  const resultCard = document.createElement("article");
  resultCard.className = "result-card solid-panel calculation-result-card";
  resultCard.append(Object.assign(document.createElement("h3"), { textContent: "결과" }), valueRows(calculation.result));
  const formulaCard = document.createElement("article");
  formulaCard.className = "result-card solid-panel";
  formulaCard.append(Object.assign(document.createElement("h3"), { textContent: "계산식" }));
  const formula = document.createElement("code");
  formula.textContent = calculation.formula;
  formulaCard.append(formula);
  const intermediateCard = document.createElement("article");
  intermediateCard.className = "result-card solid-panel";
  intermediateCard.append(Object.assign(document.createElement("h3"), { textContent: "중간값" }), valueRows(calculation.intermediate));
  cards.append(resultCard, formulaCard, intermediateCard);
  document.querySelector("#calculation-result-label").textContent = `${result.execution.toUpperCase()} RESULT / ${result.tool}`;
  document.querySelector("#calculation-result").hidden = false;
}

function renderToolFields() {
  const definition = toolDefinitions[calculationTool.value];
  calculationFields.replaceChildren();
  calculationHint.textContent = definition.hint;
  for (const [name, label, type] of definition.fields) {
    const field = document.createElement("div");
    const inputId = `field-${name}`;
    const inputLabel = document.createElement("label");
    inputLabel.htmlFor = inputId;
    inputLabel.textContent = label;
    const input = type === "json" ? document.createElement("textarea") : document.createElement("input");
    input.id = inputId;
    input.name = name;
    input.required = true;
    input.autocomplete = "off";
    if (type === "number") input.inputMode = "decimal";
    if (type === "json") input.placeholder = definition.hint;
    field.append(inputLabel, input);
    calculationFields.append(field);
  }
}

function calculationPayload() {
  const data = {};
  for (const input of calculationFields.querySelectorAll("input, textarea")) {
    data[input.name] = input.name === "options" ? JSON.parse(input.value) : input.value;
  }
  return { tool: calculationTool.value, data };
}

function openInspector(type) {
  const data = state[type];
  if (!data) return;
  inspectorContent.replaceChildren();
  if (type === "agent") {
    inspectorContent.append(listCard("분석 요약", [data.summary]), listCard("확인된 사실", data.known_facts), listCard("추가 필요 정보", data.missing_fields), listCard("가정", data.assumptions));
  } else {
    inspectorContent.append(listCard("실행 정보", [`Tool: ${data.tool}`, `Execution: ${data.execution}`]));
    for (const [title, values] of [["입력", data.calculation.inputs], ["중간값", data.calculation.intermediate], ["결과", data.calculation.result]]) {
      const card = document.createElement("article");
      card.className = "inspector-card";
      card.append(Object.assign(document.createElement("h3"), { textContent: title }), valueRows(values));
      inspectorContent.append(card);
    }
  }
  inspector.hidden = false;
  document.querySelector("#close-inspector").focus();
}

for (const [name, definition] of Object.entries(toolDefinitions)) {
  const option = document.createElement("option");
  option.value = name;
  option.textContent = definition.label;
  calculationTool.append(option);
}
renderToolFields();
calculationTool.addEventListener("change", renderToolFields);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  agentStatus.textContent = "Agent analyzing";
  setDecisionStatus("Needs Input");
  setError("");
  document.querySelector("#agent-result").hidden = true;
  document.querySelector("#sources").hidden = true;
  try {
    const preflight = await fetch("/api/research-needed", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: question.value }) });
    if (!preflight.ok) throw new Error("Research 필요 여부를 확인하지 못했습니다.");
    const researchNeed = await preflight.json();
    if (researchNeed.needed) {
      agentStatus.textContent = "Agent researching";
      setDecisionStatus("Researching");
    }
    const response = await fetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: question.value }) });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Agent 분석 요청에 실패했습니다.");
    state.agent = body;
    renderAgentResult(body);
    renderSources(body);
    setDecisionStatus("Review");
  } catch (cause) {
    setError(cause.message);
    agentStatus.textContent = "Agent unavailable";
    setDecisionStatus("Needs Input");
  } finally {
    if (agentStatus.textContent !== "Agent unavailable") agentStatus.textContent = "Agent ready";
    button.disabled = false;
  }
});

calculationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = calculationForm.querySelector("button");
  button.disabled = true;
  setDecisionStatus("Calculating");
  setError("");
  document.querySelector("#calculation-result").hidden = true;
  try {
    const payload = calculationPayload();
    const execution = document.querySelector("#execution-mode").value;
    const response = await fetch(`/api/calculations/${execution}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const body = await response.json();
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "계산 입력을 확인하세요.");
    state.calculation = body;
    renderCalculationResult(body);
    setDecisionStatus("Ready");
  } catch (cause) {
    setError(cause instanceof SyntaxError ? "선택지 목록 JSON 형식을 확인하세요." : cause.message);
    setDecisionStatus("Needs Input");
  } finally {
    button.disabled = false;
  }
});

document.querySelectorAll("[data-inspect]").forEach((button) => button.addEventListener("click", () => openInspector(button.dataset.inspect)));
document.querySelector("#close-inspector").addEventListener("click", () => { inspector.hidden = true; });
