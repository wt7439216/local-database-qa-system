// Library Manager (Phase D / v3.3) — minimal, safety-first management page.
// Reuses the same pairing token as the QA page (sessionStorage).

const state = {
  baseUrl: sessionStorage.getItem("qaBaseUrl") || window.location.origin,
  token: sessionStorage.getItem("qaToken") || "",
};

const $ = (selector) => document.querySelector(selector);
const statusEl = $("#serviceStatus");

function setStatus(text, kind = "") {
  statusEl.className = `status-pill ${kind}`.trim();
  statusEl.innerHTML = `<span class="status-dot"></span>${text}`;
}

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => el.classList.remove("show"), 2600);
}

function authHeaders(extra = {}) {
  const headers = { ...extra };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  return headers;
}

async function api(path, options = {}) {
  const response = await fetch(`${state.baseUrl}${path}`, {
    headers: authHeaders(options.body ? { "Content-Type": "application/json" } : {}),
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = data.error || `请求失败（${response.status}）`;
    throw new Error(message);
  }
  return data;
}

function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

function fmtTime(value) {
  if (!value) return "—";
  return String(value).replace("T", " ").slice(0, 19);
}

function renderStatistics(statistics) {
  $("#statKb").textContent = statistics.knowledge_bases ?? "—";
  $("#statDocs").textContent = statistics.documents ?? "—";
  $("#statReady").textContent = statistics.retrievable_documents ?? "—";
  $("#statChunks").textContent = statistics.chunks ?? "—";
  $("#statTags").textContent = statistics.tags ?? "—";
}

function renderKnowledgeBases(knowledgeBases) {
  const tbody = $("#kbTable tbody");
  tbody.innerHTML = knowledgeBases.map((kb) => `
    <tr>
      <td>${escapeHtml(kb.name)}</td>
      <td>${escapeHtml(kb.description || "")}</td>
      <td>${kb.document_count ?? 0}</td>
      <td>${kb.chunk_count ?? 0}</td>
      <td><div class="row-actions">
        ${kb.knowledge_base_id !== "kb-default"
          ? `<button class="mini-button danger" data-kb-delete="${escapeHtml(kb.knowledge_base_id)}">删除</button>`
          : '<span class="muted">默认</span>'}
      </div></td>
    </tr>`).join("");
  const select = $("#importKb");
  select.innerHTML = knowledgeBases.map((kb) =>
    `<option value="${escapeHtml(kb.knowledge_base_id)}">${escapeHtml(kb.name)}</option>`).join("");
}

function documentActions(doc) {
  const actions = [];
  if (doc.enabled) {
    actions.push(`<button class="mini-button" data-doc-disable="${doc.document_id}">停用</button>`);
  } else if (doc.status === "READY") {
    actions.push(`<button class="mini-button" data-doc-enable="${doc.document_id}">启用</button>`);
  }
  if (doc.status === "FAILED_INDEX") {
    actions.push(`<button class="mini-button" data-doc-retry-index="${doc.document_id}">重试索引</button>`);
  }
  if (doc.status === "DELETE_FAILED") {
    actions.push(`<button class="mini-button" data-doc-retry-delete="${doc.document_id}">重试删除</button>`);
  }
  if (doc.status !== "DELETING" && doc.status !== "DELETE_FAILED") {
    actions.push(`<button class="mini-button" data-doc-tags="${doc.document_id}">标签</button>`);
  }
  if (doc.status !== "DELETING") {
    actions.push(`<button class="mini-button danger" data-doc-delete="${doc.document_id}">删除</button>`);
  }
  return actions.join("");
}

function renderDocuments(documents) {
  const tbody = $("#docTable tbody");
  if (!documents.length) {
    tbody.innerHTML = '<tr><td colspan="9" class="muted">还没有导入文档。使用上方表单导入，或保留 CLI 导入方式。</td></tr>';
    return;
  }
  tbody.innerHTML = documents.map((doc) => `
    <tr>
      <td>${escapeHtml(doc.title || doc.document_id)}${doc.last_error ? `<div class="error-text">${escapeHtml(doc.last_error)}</div>` : ""}</td>
      <td>${escapeHtml(doc.document_type || doc.source_type || "—")}</td>
      <td><span class="status-chip ${escapeHtml(doc.status)}">${escapeHtml(doc.status)}${doc.enabled ? "" : " · 停用"}</span></td>
      <td>${doc.enabled ? "是" : "否"}</td>
      <td>${doc.chunk_count ?? 0}</td>
      <td>${escapeHtml(doc.tags || "—")}</td>
      <td>${escapeHtml(doc.source_display || doc.source_name || "—")}</td>
      <td>${escapeHtml(fmtTime(doc.updated_at))}</td>
      <td><div class="row-actions">${documentActions(doc)}</div></td>
    </tr>`).join("");
}

async function refresh() {
  const data = await api("/api/v3/library");
  renderStatistics(data.statistics || {});
  renderKnowledgeBases(data.knowledge_bases || []);
  renderDocuments(data.documents || []);
}

async function handleDocumentAction(action, documentId) {
  if (action === "delete") {
    // 二次确认：删除会移除该文档全部内容与索引 points，不可恢复。
    if (!window.confirm("确认删除该文档？其全部片段、索引与标签将被移除，且不可恢复。")) return;
    await api(`/api/v3/library/documents/${encodeURIComponent(documentId)}`, { method: "DELETE" });
    toast("文档已删除");
  } else if (action === "disable") {
    await api(`/api/v3/library/documents/${encodeURIComponent(documentId)}/disable`, { method: "POST", body: "{}" });
    toast("已停用（默认检索不再包含）");
  } else if (action === "enable") {
    await api(`/api/v3/library/documents/${encodeURIComponent(documentId)}/enable`, { method: "POST", body: "{}" });
    toast("已启用");
  } else if (action === "retry-index") {
    const result = await api(`/api/v3/library/documents/${encodeURIComponent(documentId)}/retry-index`, { method: "POST", body: "{}" });
    toast(result.status === "READY" ? "索引已恢复" : `仍为 ${result.status}`);
  } else if (action === "retry-delete") {
    await api(`/api/v3/library/documents/${encodeURIComponent(documentId)}/retry-delete`, { method: "POST", body: "{}" });
    toast("删除已完成");
  } else if (action === "tags") {
    const current = window.prompt("标签（用逗号分隔；留空清除全部标签）");
    if (current === null) return;
    const tags = current.split(/[,，、]/).map((item) => item.trim()).filter(Boolean);
    await api(`/api/v3/library/documents/${encodeURIComponent(documentId)}/tags`, {
      method: "POST", body: JSON.stringify({ tags }),
    });
    toast("标签已更新");
  }
}

$("#docTable").addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-doc-delete], button[data-doc-disable], button[data-doc-enable], button[data-doc-retry-index], button[data-doc-retry-delete], button[data-doc-tags]");
  if (!button) return;
  const dataset = button.dataset;
  const action = dataset.docDelete ? "delete"
    : dataset.docDisable ? "disable"
    : dataset.docEnable ? "enable"
    : dataset.docRetryIndex ? "retry-index"
    : dataset.docRetryDelete ? "retry-delete"
    : "tags";
  const documentId = dataset.docDelete || dataset.docDisable || dataset.docEnable || dataset.docRetryIndex || dataset.docRetryDelete || dataset.docTags;
  try {
    await handleDocumentAction(action, documentId);
    await refresh();
  } catch (error) {
    toast(error.message || "操作失败");
  }
});

$("#kbTable").addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-kb-delete]");
  if (!button) return;
  if (!window.confirm("确认删除该知识库？（仅允许删除不含文档的空知识库）")) return;
  try {
    await api(`/api/v3/library/knowledge-bases/${encodeURIComponent(button.dataset.kbDelete)}`, { method: "DELETE" });
    toast("知识库已删除");
    await refresh();
  } catch (error) {
    toast(error.message || "操作失败");
  }
});

$("#kbCreateForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    await api("/api/v3/library/knowledge-bases", {
      method: "POST",
      body: JSON.stringify({ name: $("#kbName").value, description: $("#kbDescription").value }),
    });
    $("#kbName").value = "";
    $("#kbDescription").value = "";
    toast("知识库已创建");
    await refresh();
  } catch (error) {
    toast(error.message || "创建失败");
  }
});

$("#importForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const tags = $("#importTags").value.split(/[,，、]/).map((item) => item.trim()).filter(Boolean);
  try {
    const result = await api("/api/v3/library/documents", {
      method: "POST",
      body: JSON.stringify({
        action: "import",
        path: $("#importPath").value.trim(),
        knowledge_base_id: $("#importKb").value || undefined,
        tags,
      }),
    });
    const duplicates = result.duplicate_candidates || [];
    toast(`导入完成：${result.import_status || result.status}` +
      (duplicates.length ? `（注意：与 ${duplicates.length} 个文档内容相同）` : ""));
    $("#importPath").value = "";
    $("#importTags").value = "";
    await refresh();
  } catch (error) {
    toast(error.message || "导入失败");
  }
});

async function start() {
  setStatus("正在连接");
  try {
    await refresh();
    setStatus("服务就绪", "ready");
  } catch (error) {
    setStatus(error.message === "请求失败（401）" || error.message.includes("401") ? "需要配对（先在问答页连接）" : (error.message || "连接失败"), "error");
  }
}

start();
