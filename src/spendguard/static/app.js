const form = document.querySelector("#analysis-form");
const question = document.querySelector("#question");
const status = document.querySelector("#agent-status");
const result = document.querySelector("#result");
const error = document.querySelector("#error");

function populateList(id, values) {
  const list = document.querySelector(id);
  list.replaceChildren();
  const items = values.length ? values : ["없음"];
  for (const value of items) {
    const item = document.createElement("li");
    item.textContent = value;
    list.append(item);
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  status.textContent = "Agent status: analyzing";
  error.hidden = true;
  result.hidden = true;
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question.value }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "분석 요청에 실패했습니다.");
    document.querySelector("#intent").textContent = body.intent;
    document.querySelector("#summary").textContent = body.summary;
    populateList("#known-facts", body.known_facts);
    populateList("#missing-fields", body.missing_fields);
    populateList("#assumptions", body.assumptions);
    result.hidden = false;
    status.textContent = "Agent status: ready";
  } catch (cause) {
    error.textContent = cause.message;
    error.hidden = false;
    status.textContent = "Agent status: unavailable";
  } finally {
    button.disabled = false;
  }
});
