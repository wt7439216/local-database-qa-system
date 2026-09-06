const state = {
  baseUrl: sessionStorage.getItem("qaBaseUrl") || window.location.origin,
  pairingCode: sessionStorage.getItem("qaPairingCode") || "",
  token: sessionStorage.getItem("qaToken") || "",
  busy: false,
  currentJobId: "",
  lanUrls: [],
  localHost: false,
  history: [],
};

const MAX_HISTORY_TURNS = 3;

const $ = (selector) => document.querySelector(selector);
const statusEl = $("#serviceStatus");
const form = $("#questionForm");
const input = $("#questionInput");
const askButton = $("#askButton");
const cancelButton = $("#cancelButton");
const answerBody = $("#answerBody");
const evidenceList = $("#evidenceList");
const settingsDialog = $("#settingsDialog");
const emptyStateHTML = answerBody.innerHTML;
let currentAnswerEl = null;

function startTurn(question) {
  const empty = answerBody.querySelector(".empty-state");
  if (empty) empty.remove();
  const turn = document.createElement("article");
  turn.className = "answer-turn";
  const heading = document.createElement("div");
  heading.className = "turn-question";
  heading.textContent = question;
  const content = document.createElement("div");
  content.className = "answer-content";
  turn.append(heading, content);
  answerBody.appendChild(turn);
  currentAnswerEl = content;
  $("#clearButton").hidden = false;
  answerBody.scrollTop = answerBody.scrollHeight;
  return content;
}

function renderAnswerInto(el, text, loading = false) {
  const escaped = escapeHtml(text);
  // 流式阶段按纯文本显示（避免半截 markdown 闪烁），完成后做完整渲染。
  const content = loading ? escaped : renderMarkdown(escaped);
  const withCitations = content.replace(/\[(\d+)\]/g, '<span class="citation-ref" data-cite="$1">[$1]</span>');
  el.innerHTML = loading
    ? `<div class="answer-loading"><span class="pulse"></span>${withCitations}</div>`
    : withCitations;
  answerBody.scrollTop = answerBody.scrollHeight;
}

// 每 token 全量重建 innerHTML 在长回答和手机上会卡，按动画帧合帧渲染。
let pendingStreamText = "";
let streamFrame = 0;
function scheduleStreamRender(text) {
  pendingStreamText = text;
  if (!streamFrame) {
    streamFrame = requestAnimationFrame(() => {
      streamFrame = 0;
      if (currentAnswerEl) renderAnswerInto(currentAnswerEl, pendingStreamText, true);
    });
  }
}

function setStatus(text, kind = "") {
  statusEl.className = `status-pill ${kind}`.trim();
  statusEl.innerHTML = `<span class="status-dot"></span>${escapeHtml(text)}`;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 1800);
}

function authHeaders() {
  if (state.token) return { Authorization: `Bearer ${state.token}` };
  return {};
}

function openSettings() {
  if (settingsDialog.open) return;
  $("#settingsButton").click();
}

async function legacyCopy(text) {
  const area = document.createElement("textarea");
  area.value = text;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.appendChild(area);
  area.select();
  let copied = false;
  try {
    copied = document.execCommand("copy");
  } catch (_error) {
    copied = false;
  }
  area.remove();
  return copied;
}

async function copyText(text) {
  // The async clipboard API only exists in secure contexts; phones reaching
  // the service over LAN HTTP need the execCommand fallback.
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (_error) {
      return legacyCopy(text);
    }
  }
  return legacyCopy(text);
}

async function pair(code) {
  const response = await fetch(`${state.baseUrl}/api/v2/pair`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "配对失败");
  state.token = data.token;
  state.pairingCode = code;
  sessionStorage.setItem("qaToken", state.token);
  sessionStorage.setItem("qaPairingCode", code);
}

async function autoPairOnThisComputer() {
  if (state.token || state.baseUrl !== window.location.origin) return;
  try {
    const response = await fetch(`${state.baseUrl}/api/v2/bootstrap`);
    if (!response.ok) return;
    const data = await response.json();
    state.lanUrls = data.lan_urls || [];
    state.localHost = true;
    if (data.pairing_code) await pair(data.pairing_code);
  } catch (_error) {
    // Remote devices enter the code shown on the host computer.
  }
}

async function checkHealth() {
  setStatus("正在连接");
  try {
    await autoPairOnThisComputer();
    const response = await fetch(`${state.baseUrl}/api/v2/health`, { headers: authHeaders() });
    if (!response.ok) {
      if (response.status === 401) openSettings();
      throw new Error(response.status === 401 ? "需要配对" : "服务不可用");
    }
    const data = await response.json();
    setStatus(data.degraded ? "可用 · 关键词模式" : "服务就绪", "ready");
    $("#chunkCount").textContent = data.chunks ?? "—";
    $("#documentCount").textContent = data.documents ?? 1;
    if (data.library_name) $("#libraryName").textContent = data.library_name;
    return data;
  } catch (error) {
    setStatus(error.message || "连接失败", "error");
    return null;
  }
}

function setBusy(busy) {
  state.busy = busy;
  input.disabled = busy;
  askButton.disabled = busy;
  cancelButton.hidden = !busy;
  askButton.innerHTML = busy
    ? "<span>正在处理</span><span aria-hidden=\"true\">…</span>"
    : "<span>发送问题</span><span aria-hidden=\"true\">→</span>";
}

function renderSources(sources = []) {
  $("#sourceCount").textContent = sources.length;
  if (!sources.length) {
    evidenceList.innerHTML = `<div class="evidence-empty"><span aria-hidden="true">◎</span><p>这次回答没有可验证的教材出处。</p></div>`;
    return;
  }
  evidenceList.innerHTML = sources.map((source, index) => `
    <article class="evidence-card" id="source-${source.id || index + 1}">
      <strong>[${source.id || index + 1}] ${escapeHtml(source.title || source.source || "教材片段")}</strong>
      <p>${escapeHtml(source.quote || source.text || "")}</p>
      <div class="evidence-meta">${escapeHtml(source.location || source.source || "")}</div>
    </article>`).join("");
}

function selectQuestion(question) {
  input.value = question;
  input.dispatchEvent(new Event("input"));
  input.focus();
}

function appendRecoverySuggestions(answerEl) {
  const questions = [
    ["查看全书目录", "这本书有哪些章节？"],
    ["介绍这本教材", "介绍下这本书。"],
    ["概括第三章", "第三章主要讲什么？"],
  ];
  const box = document.createElement("div");
  box.className = "suggestions recovery-suggestions";
  box.setAttribute("aria-label", "换个问法");
  for (const [label, question] of questions) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.question = question;
    button.textContent = label;
    box.appendChild(button);
  }
  answerEl.appendChild(box);
}

async function ask(question) {
  setBusy(true);
  setStatus("正在排队");
  const answerEl = startTurn(question);
  renderAnswerInto(answerEl, "正在理解问题并查找教材内容…", true);
  renderSources([]);
  let streamedAnswer = "";
  try {
    const response = await fetch(`${state.baseUrl}/api/v2/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ question, history: state.history }),
    });
    const created = await response.json();
    if (!response.ok) {
      if (response.status === 401) openSettings();
      throw new Error(created.error || "请求失败");
    }
    state.currentJobId = created.job_id;

    const eventsResponse = await fetch(`${state.baseUrl}/api/v2/jobs/${encodeURIComponent(state.currentJobId)}/events`, { headers: authHeaders() });
    if (!eventsResponse.ok || !eventsResponse.body) throw new Error("无法读取回答进度");
    const reader = eventsResponse.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let finalResult = null;
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim()) continue;
        const event = JSON.parse(line);
        if (event.event === "status") setStatus(event.message || "正在处理");
        if (event.event === "token") {
          streamedAnswer += event.text || "";
          scheduleStreamRender(streamedAnswer);
          setStatus("正在生成回答");
        }
        if (event.event === "final") finalResult = event.result;
        if (event.event === "error") throw new Error(event.message || "回答失败");
        if (event.event === "cancelled") throw new Error("回答已取消");
      }
      if (done) break;
    }
    if (!finalResult) throw new Error("服务未返回完整结果");
    renderAnswerInto(answerEl, finalResult.answer || "没有生成回答。");
    if (finalResult.out_of_scope) appendRecoverySuggestions(answerEl);
    renderSources(finalResult.citations || finalResult.sources || []);
    $("#copyButton").disabled = !finalResult.answer;
    $("#copyButton").dataset.answer = finalResult.answer || "";
    state.history.push({ question, answer: finalResult.answer || "" });
    if (state.history.length > MAX_HISTORY_TURNS) state.history.shift();
    if (finalResult.citation_verified === false) {
      toast("部分引用未通过原文核对，请谨慎采信");
    }
    setStatus(finalResult.out_of_scope ? "未找到可靠依据" : "回答完成", "ready");
    return finalResult;
  } catch (error) {
    renderAnswerInto(answerEl, `暂时无法完成回答：${error.message || error}`);
    setStatus(error.message === "回答已取消" ? "已取消" : "请求失败", "error");
    throw error;
  } finally {
    state.currentJobId = "";
    setBusy(false);
  }
}

async function cancelCurrentJob() {
  if (!state.currentJobId) return;
  cancelButton.disabled = true;
  try {
    await fetch(`${state.baseUrl}/api/v2/jobs/${encodeURIComponent(state.currentJobId)}`, { method: "DELETE", headers: authHeaders() });
    setStatus("正在取消");
  } finally {
    cancelButton.disabled = false;
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = input.value.trim();
  if (question && !state.busy) ask(question).catch(() => {});
});
cancelButton.addEventListener("click", cancelCurrentJob);
input.addEventListener("input", () => { $("#questionCount").textContent = `${input.value.length} / 2000`; });
input.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") form.requestSubmit();
});
document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => selectQuestion(button.dataset.question));
});
answerBody.addEventListener("click", (event) => {
  const button = event.target.closest("[data-question]");
  if (button) {
    selectQuestion(button.dataset.question);
    return;
  }
  const cite = event.target.closest("[data-cite]");
  if (cite) {
    const card = document.getElementById(`source-${cite.dataset.cite}`);
    if (card) {
      card.scrollIntoView({ behavior: "smooth", block: "start" });
      card.classList.add("highlight");
      setTimeout(() => card.classList.remove("highlight"), 1600);
    }
  }
});
$("#copyButton").addEventListener("click", async (event) => {
  const copied = await copyText(event.currentTarget.dataset.answer || "");
  toast(copied ? "回答已复制" : "复制失败，请手动选择文本后复制");
});
$("#settingsButton").addEventListener("click", () => {
  $("#serverUrl").value = state.baseUrl === window.location.origin ? "" : state.baseUrl;
  $("#pairingCode").value = state.pairingCode;
  $("#connectionHint").textContent = state.lanUrls.length
    ? `手机可访问：${state.lanUrls.join("，")}`
    : "只在可信局域网内连接。配对码仅保留在当前浏览器会话。";
  $("#shutdownButton").hidden = !state.localHost;
  settingsDialog.showModal();
});
$("#cancelSettings").addEventListener("click", () => settingsDialog.close());
$("#settingsForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const configured = $("#serverUrl").value.trim().replace(/\/+$/, "");
  state.baseUrl = configured || window.location.origin;
  state.token = "";
  state.pairingCode = $("#pairingCode").value.trim();
  sessionStorage.setItem("qaBaseUrl", state.baseUrl);
  sessionStorage.removeItem("qaToken");
  try {
    if (state.pairingCode) await pair(state.pairingCode);
    const health = await checkHealth();
    if (health) settingsDialog.close();
  } catch (error) {
    setStatus(error.message || "配对失败", "error");
  }
});
$("#clearButton").addEventListener("click", () => {
  state.history = [];
  answerBody.innerHTML = emptyStateHTML;
  currentAnswerEl = null;
  $("#clearButton").hidden = true;
  renderSources([]);
  $("#copyButton").disabled = true;
  $("#copyButton").dataset.answer = "";
});
$("#shutdownButton").addEventListener("click", async () => {
  if (!state.localHost) return;
  const response = await fetch(`${state.baseUrl}/api/v2/shutdown`, { method: "POST", headers: authHeaders() });
  if (response.ok) {
    settingsDialog.close();
    setStatus("服务已停止", "error");
    state.history = [];
    $("#clearButton").hidden = true;
    renderAnswerInto(startTurn("本地服务"), "本地服务已安全停止，可以关闭此页面。\n\n再次使用时重新启动程序即可。");
  }
});

function registerModelTools() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  const lifecycle = new AbortController();
  try {
    Promise.resolve(context.registerTool({
      name: "ask_textbook",
      title: "向本地教材提问",
      description: "在当前本地教材库中检索问题，生成带页码和原文证据的回答，并更新页面。",
      inputSchema: {
        type: "object",
        properties: { question: { type: "string", minLength: 1, maxLength: 2000 } },
        required: ["question"],
        additionalProperties: false,
      },
      annotations: { readOnlyHint: false, untrustedContentHint: false },
      async execute(value) {
        const question = String(value?.question || "").trim();
        if (!question) throw new Error("question 不能为空");
        input.value = question;
        input.dispatchEvent(new Event("input"));
        return await ask(question);
      },
    }, { signal: lifecycle.signal })).catch(() => {});
  } catch (_error) {
    // WebMCP is optional; the normal interface remains complete.
  }
}

registerModelTools();
checkHealth();
