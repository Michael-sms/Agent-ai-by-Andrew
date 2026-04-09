const app = document.getElementById("app");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const sendBtn = document.getElementById("sendBtn");
const statusText = document.getElementById("statusText");
const newChatBtn = document.getElementById("newChatBtn");
const sessionGroupsNode = document.getElementById("sessionGroups");
const sessionTitleNode = document.getElementById("sessionTitle");
const renameBtn = document.getElementById("renameBtn");
const deleteBtn = document.getElementById("deleteBtn");
const themeSelect = document.getElementById("themeSelect");

const THEME_KEY = "agent-ai-theme-mode";
const themeMedia = window.matchMedia("(prefers-color-scheme: dark)");

let isSending = false;
let currentSessionId = "";
let sessions = [];
let themeMode = "system";

function resolveTheme(mode) {
  if (mode === "system") {
    return themeMedia.matches ? "dark" : "light";
  }
  return mode === "light" ? "light" : "dark";
}

function applyTheme(mode, persist = true) {
  themeMode = ["light", "dark", "system"].includes(mode) ? mode : "system";
  const resolved = resolveTheme(themeMode);
  document.documentElement.setAttribute("data-theme", resolved);
  document.documentElement.classList.remove("theme-light", "theme-dark");
  document.documentElement.classList.add(`theme-${resolved}`);
  if (document.body) {
    document.body.setAttribute("data-theme", resolved);
    document.body.classList.remove("theme-light", "theme-dark");
    document.body.classList.add(`theme-${resolved}`);
  }
  if (themeSelect) {
    themeSelect.value = themeMode;
  }
  if (persist) {
    try {
      window.localStorage.setItem(THEME_KEY, themeMode);
    } catch (_) {
    }
  }

  if (resolved === "light") {
    const lightBg = "linear-gradient(180deg, #ffffff 0%, #f3f6fb 100%)";
    document.documentElement.style.background = lightBg;
    if (document.body) {
      document.body.style.background = lightBg;
    }
  } else {
    document.documentElement.style.background = "";
    if (document.body) {
      document.body.style.background = "";
    }
  }
}

function loadThemeMode() {
  let saved = null;
  try {
    saved = window.localStorage.getItem(THEME_KEY);
  } catch (_) {
  }
  if (saved === "light" || saved === "dark" || saved === "system") {
    return saved;
  }
  return "system";
}

function onSystemThemeChanged() {
  if (themeMode === "system") {
    applyTheme("system", false);
  }
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderInline(text) {
  let html = escapeHtml(text);
  html = html.replace(/`([^`]+)`/g, (_, code) => `<code>${code}</code>`);
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => {
    const safeUrl = String(url).trim();
    if (!/^https?:\/\//i.test(safeUrl)) {
      return label;
    }
    return `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${label}</a>`;
  });
  return html;
}

function markdownToHtml(markdown) {
  const text = String(markdown || "").replace(/\r\n/g, "\n");
  const codeBlocks = [];
  const placeholderText = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
    const token = `@@CODE_BLOCK_${codeBlocks.length}@@`;
    const cls = lang ? ` class="lang-${escapeHtml(lang)}"` : "";
    codeBlocks.push(`<pre><code${cls}>${escapeHtml(code.trimEnd())}</code></pre>`);
    return token;
  });

  const lines = placeholderText.split("\n");
  const htmlParts = [];
  let listType = "";

  const closeList = () => {
    if (!listType) {
      return;
    }
    htmlParts.push(listType === "ol" ? "</ol>" : "</ul>");
    listType = "";
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      continue;
    }
    if (/^@@CODE_BLOCK_\d+@@$/.test(line)) {
      closeList();
      htmlParts.push(line);
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      closeList();
      const level = heading[1].length;
      htmlParts.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    const ordered = line.match(/^\d+\.\s+(.+)$/);
    if (ordered) {
      if (listType !== "ol") {
        closeList();
        listType = "ol";
        htmlParts.push("<ol>");
      }
      htmlParts.push(`<li>${renderInline(ordered[1])}</li>`);
      continue;
    }

    const unordered = line.match(/^[-*]\s+(.+)$/);
    if (unordered) {
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        htmlParts.push("<ul>");
      }
      htmlParts.push(`<li>${renderInline(unordered[1])}</li>`);
      continue;
    }

    closeList();
    htmlParts.push(`<p>${renderInline(line)}</p>`);
  }

  closeList();

  let html = htmlParts.join("\n");
  for (let i = 0; i < codeBlocks.length; i += 1) {
    html = html.replaceAll(`@@CODE_BLOCK_${i}@@`, codeBlocks[i]);
  }
  return html || "<p>(空响应)</p>";
}

async function api(path, options = {}) {
  const resp = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(payload.detail || "请求失败");
  }
  return payload;
}

function setHasMessages(value) {
  if (value) {
    app.classList.add("has-messages");
  } else {
    app.classList.remove("has-messages");
  }
}

function setStatus(text) {
  statusText.textContent = text || "";
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 180)}px`;
}

function appendMessage(role, content, isPending = false) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  if (isPending) {
    div.dataset.pending = "1";
  }
  if (role === "assistant" && !isPending) {
    div.classList.add("markdown");
    div.innerHTML = markdownToHtml(content);
  } else {
    div.textContent = content;
  }
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function clearMessages() {
  messages.innerHTML = "";
}

function renderMessages(session) {
  clearMessages();
  const list = Array.isArray(session.messages) ? session.messages : [];
  for (const message of list) {
    appendMessage(message.role === "assistant" ? "assistant" : "user", message.content || "");
  }
  setHasMessages(list.length > 0);
}

function setSending(sending) {
  isSending = sending;
  sendBtn.disabled = sending;
  input.disabled = sending;
}

function groupKeyByTime(isoTime) {
  const dt = new Date(isoTime);
  if (Number.isNaN(dt.getTime())) {
    return "更早";
  }
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - dt.getTime()) / 86400000);
  if (diffDays <= 30) {
    return "30 天内";
  }
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, "0")}`;
}

function renderSessionList() {
  sessionGroupsNode.innerHTML = "";
  const groups = new Map();
  for (const session of sessions) {
    const key = groupKeyByTime(session.updated_at || session.created_at);
    if (!groups.has(key)) {
      groups.set(key, []);
    }
    groups.get(key).push(session);
  }

  for (const [groupName, groupSessions] of groups.entries()) {
    const block = document.createElement("section");
    const title = document.createElement("div");
    title.className = "session-group-title";
    title.textContent = groupName;
    block.appendChild(title);

    for (const session of groupSessions) {
      const item = document.createElement("div");
      item.className = "session-item" + (session.id === currentSessionId ? " active" : "");
      item.dataset.id = session.id;

      const itemTitle = document.createElement("div");
      itemTitle.className = "session-item-title";
      itemTitle.textContent = session.title || "新对话";

      const preview = document.createElement("div");
      preview.className = "session-item-preview";
      preview.textContent = session.preview || "暂无消息";

      item.appendChild(itemTitle);
      item.appendChild(preview);
      item.addEventListener("click", () => switchSession(session.id));
      block.appendChild(item);
    }

    sessionGroupsNode.appendChild(block);
  }
}

async function reloadSessions() {
  const data = await api("/api/sessions");
  sessions = Array.isArray(data.sessions) ? data.sessions : [];
  const currentExists = sessions.some((item) => item.id === currentSessionId);
  if (!currentSessionId || !currentExists) {
    currentSessionId = data.active_session_id || (sessions[0] && sessions[0].id) || "";
  }
  renderSessionList();
}

async function switchSession(sessionId) {
  if (!sessionId) {
    return;
  }
  try {
    const session = await api(`/api/sessions/${sessionId}`);
    currentSessionId = session.id;
    sessionTitleNode.textContent = session.title || "新对话";
    renderMessages(session);
    await reloadSessions();
    input.focus();
  } catch (error) {
    setStatus(`切换会话失败：${error.message}`);
  }
}

async function createSession() {
  const created = await api("/api/sessions", {
    method: "POST",
    body: JSON.stringify({ title: "新对话" }),
  });
  await reloadSessions();
  await switchSession(created.id);
  setStatus("已创建新对话");
}

async function renameCurrentSession() {
  if (!currentSessionId) {
    await reloadSessions();
    if (!currentSessionId) {
      setStatus("当前没有可重命名会话");
      return;
    }
  }

  const currentExists = sessions.some((item) => item.id === currentSessionId);
  if (!currentExists) {
    await reloadSessions();
  }

  if (!currentSessionId) {
    return;
  }
  const oldTitle = sessionTitleNode.textContent || "新对话";
  const nextTitle = window.prompt("请输入新的会话标题", oldTitle);
  if (!nextTitle || !nextTitle.trim()) {
    return;
  }
  const updated = await api(`/api/sessions/${currentSessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ title: nextTitle.trim() }),
  });
  sessionTitleNode.textContent = updated.title;
  await reloadSessions();
}

async function deleteCurrentSession() {
  if (!currentSessionId) {
    return;
  }
  if (!window.confirm("确定删除当前会话吗？此操作不可撤销。")) {
    return;
  }
  await api(`/api/sessions/${currentSessionId}`, { method: "DELETE" });
  currentSessionId = "";
  await reloadSessions();
  if (sessions.length === 0) {
    await createSession();
    return;
  }
  await switchSession(sessions[0].id);
}

async function sendMessage(message) {
  const userText = message.trim();
  if (!userText || isSending) {
    return;
  }
  if (!currentSessionId) {
    await createSession();
  }

  appendMessage("user", userText);
  const pendingNode = appendMessage("assistant", "正在思考中...", true);
  setHasMessages(true);
  setSending(true);
  setStatus("请求处理中...");

  try {
    const payload = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({
        message: userText,
        session_id: currentSessionId,
      }),
    });

    currentSessionId = payload.session_id;
    sessionTitleNode.textContent = payload.session_title || sessionTitleNode.textContent;
    pendingNode.classList.add("markdown");
    pendingNode.innerHTML = markdownToHtml(payload.answer || "(空响应)");
    setStatus(
      `完成：${payload.total_tool_calls} 次工具调用，耗时 ${Number(payload.total_latency || 0).toFixed(2)}s`
    );
    await reloadSessions();
  } catch (error) {
    pendingNode.textContent = `调用失败：${error.message}`;
    setStatus("请求失败，请检查后端或 API 配置。");
  } finally {
    setSending(false);
    input.value = "";
    autoResize();
    input.focus();
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await sendMessage(input.value);
});

input.addEventListener("input", autoResize);
input.addEventListener("keydown", async (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    await sendMessage(input.value);
  }
});

newChatBtn.addEventListener("click", async () => {
  await createSession();
});

renameBtn.addEventListener("click", async () => {
  await renameCurrentSession();
});

deleteBtn.addEventListener("click", async () => {
  await deleteCurrentSession();
});

if (themeSelect) {
  themeSelect.addEventListener("change", () => {
    applyTheme(themeSelect.value, true);
  });
}

if (typeof themeMedia.addEventListener === "function") {
  themeMedia.addEventListener("change", onSystemThemeChanged);
} else if (typeof themeMedia.addListener === "function") {
  themeMedia.addListener(onSystemThemeChanged);
}

async function init() {
  applyTheme(loadThemeMode(), false);

  try {
    await reloadSessions();
    if (sessions.length === 0) {
      await createSession();
    } else {
      await switchSession(currentSessionId || sessions[0].id);
    }
  } catch (error) {
    setStatus(`初始化失败：${error.message}`);
  }

  autoResize();
  input.focus();
}

init();
