const targets = await (await fetch("http://127.0.0.1:9444/json/list")).json();
const target = targets.find((item) => item.type === "page");
if (!target) throw new Error("No Chrome page target available");

const socket = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((resolve, reject) => {
  socket.addEventListener("open", resolve, { once: true });
  socket.addEventListener("error", reject, { once: true });
});
let nextId = 1;
const pending = new Map();
socket.addEventListener("message", ({ data }) => {
  const message = JSON.parse(data);
  if (message.id && pending.has(message.id)) {
    const { resolve, reject } = pending.get(message.id);
    pending.delete(message.id);
    message.error ? reject(new Error(message.error.message)) : resolve(message.result);
  }
});
function command(method, params = {}) {
  const id = nextId++;
  socket.send(JSON.stringify({ id, method, params }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject }));
}
const pause = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));

await command("Emulation.setDeviceMetricsOverride", { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
await command("Page.navigate", { url: "http://127.0.0.1:8000/" });
await pause(350);
const initial = await command("Runtime.evaluate", {
  expression: `(() => {
    const composer = document.querySelector('.question-composer').getBoundingClientRect();
    const scenarios = document.querySelector('#scenario-groups').getBoundingClientRect();
    document.querySelector('[data-scenario-group="매달 새는 돈"]').click();
    return JSON.stringify({
      scrollWidth: document.documentElement.scrollWidth,
      viewportWidth: innerWidth,
      tabCount: document.querySelectorAll('[data-scenario-group]').length,
      defaultCards: 3,
      selectedGroupCards: document.querySelectorAll('.scenario-card').length,
      composerWidth: Math.round(composer.width),
      scenarioWidth: Math.round(scenarios.width),
    });
  })()`,
  returnByValue: true,
});
const flow = await command("Runtime.evaluate", {
  expression: `(() => {
    window.fetch = async (url) => {
      await new Promise((resolve) => setTimeout(resolve, 100));
      if (url === "/api/research-needed") return new Response(JSON.stringify({ needed: true }), { status: 200 });
      return new Response(JSON.stringify({ status: "needs_input", conclusion: "internal", facts: [], assumptions: [], missing_fields: ["target"], calculations: [], options: [], risks: [], next_actions: [], sources: [] }), { status: 200 });
    };
    document.querySelector('#question').value = '상품을 비교해줘';
    document.querySelector('#decision-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    const pending = {
      blockerVisible: !document.querySelector('#processing-blocker').hidden,
      progressVisible: !!document.querySelector('.processing-track'),
      scenariosDisplay: getComputedStyle(document.querySelector('.scenario-section')).display,
    };
    return new Promise((resolve) => setTimeout(() => {
      const questionPanel = document.querySelector('#question-panel').getBoundingClientRect();
      const required = document.querySelector('#required-data').getBoundingClientRect();
      resolve(JSON.stringify({
        pending,
        requiredVisible: !document.querySelector('#required-data').hidden,
        scenariosDisplay: getComputedStyle(document.querySelector('.scenario-section')).display,
        resultHidden: document.querySelector('#decision-result').hidden,
        inspectorHidden: document.querySelector('#inspector').hidden,
        directlyBelowQuestion: required.top >= questionPanel.bottom && required.top - questionPanel.bottom < 40,
      }));
    }, 260));
  })()`,
  awaitPromise: true,
  returnByValue: true,
});
console.log(JSON.stringify({ initial: JSON.parse(initial.result.value), flow: JSON.parse(flow.result.value) }, null, 2));
socket.close();
