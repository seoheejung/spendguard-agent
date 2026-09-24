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

await command("Network.setCacheDisabled", { cacheDisabled: true });
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
    const apiCalls = [];
    window.fetch = async (url) => {
      apiCalls.push(url);
      await new Promise((resolve) => setTimeout(resolve, 100));
      return new Response(JSON.stringify({ status: "ready", answer: "서울/인천 출발 왕복 기준의 참고 가격대를 확인했습니다. 여행 날짜에 따라 실제 가격은 달라질 수 있습니다." }), { status: 200 });
    };
    document.querySelector('#question').value = '나고야 항공권을 37만원에 사려고 해.';
    document.querySelector('#decision-form').dispatchEvent(new Event('submit', { bubbles: true, cancelable: true }));
    const pending = {
      blockerVisible: !document.querySelector('#processing-blocker').hidden,
      progressVisible: !!document.querySelector('.processing-track'),
      scenariosDisplay: getComputedStyle(document.querySelector('.scenario-section')).display,
    };
    return new Promise((resolve) => setTimeout(() => {
      const questionPanel = document.querySelector('#question-panel').getBoundingClientRect();
      const result = document.querySelector('#decision-result').getBoundingClientRect();
      resolve(JSON.stringify({
        pending,
        apiCalls,
        legacyRemoved: !document.querySelector('#required-data') && !document.querySelector('#inspector'),
        scenariosDisplay: getComputedStyle(document.querySelector('.scenario-section')).display,
        resultHidden: document.querySelector('#decision-result').hidden,
        conclusion: document.querySelector('.conclusion-card p:last-child')?.textContent,
        resultGap: Math.round(result.top - questionPanel.bottom),
      }));
    }, 260));
  })()`,
  awaitPromise: true,
  returnByValue: true,
});
const result = { initial: JSON.parse(initial.result.value), flow: JSON.parse(flow.result.value) };
console.log(JSON.stringify(result, null, 2));
if (result.flow.apiCalls.join(",") !== "/api/decisions") throw new Error("Unexpected API request path");
if (!result.flow.pending.blockerVisible || result.flow.pending.scenariosDisplay !== "none") throw new Error("Pending UI state regressed");
if (!result.flow.legacyRemoved || result.flow.resultHidden || result.flow.scenariosDisplay !== "none") throw new Error("One-shot result visibility regressed");
if (!result.flow.conclusion.includes("서울/인천 출발")) throw new Error("Final comparison was not rendered");
if (result.flow.resultGap < 0 || result.flow.resultGap > 40) throw new Error("Result is not directly below the question");
socket.close();
