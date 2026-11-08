// 共享前端工具（P3）：app.js 与 library.js 通过 ESM import 复用，
// 消除此前两份重复的 $/toast/setStatus/escapeHtml/authHeaders 定义。

export const $ = (selector) => document.querySelector(selector);

export function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

let toastTimer = 0;
export function toast(message, duration = 2200) {
  const el = $("#toast");
  if (!el) return;
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove("show"), duration);
}

export function setStatus(text, kind = "") {
  const statusEl = $("#serviceStatus");
  if (!statusEl) return;
  statusEl.className = `status-pill ${kind}`.trim();
  statusEl.innerHTML = `<span class="status-dot"></span>${escapeHtml(text)}`;
}

export function authHeaders(extra = {}) {
  const headers = { ...extra };
  const token = sessionStorage.getItem("qaToken") || "";
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

export async function api(path, options = {}) {
  const base = sessionStorage.getItem("qaBaseUrl") || window.location.origin;
  const response = await fetch(`${base}${path}`, {
    headers: authHeaders(options.body ? { "Content-Type": "application/json" } : {}),
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || `请求失败（${response.status}）`);
  }
  return data;
}
