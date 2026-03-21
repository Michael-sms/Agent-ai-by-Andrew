const app = document.getElementById("app");
const form = document.getElementById("chatForm");
const input = document.getElementById("messageInput");
const messages = document.getElementById("messages");
const sendBtn = document.getElementById("sendBtn");
const statusText = document.getElementById("statusText");
const newChatBtn = document.getElementById("newChatBtn");

let isSending = false;
let messageCount = 0;

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
  messageCount += 1;
  setHasMessages(true);
  return div;
}

function setSending(sending) {
  isSending = sending;
  sendBtn.disabled = sending;
  input.disabled = sending;
}

async function sendMessage(message) {
  const userText = message.trim();
  if (!userText || isSending) {
    return;
  }

  appendMessage("user", userText);
  const pendingNode = appendMessage("assistant", "正在思考中...", true);

  setSending(true);
  setStatus("请求处理中...");

  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText }),
    });

    const payload = await resp.json();
    if (!resp.ok) {
      throw new Error(payload.detail || "请求失败");
    }

    pendingNode.classList.add("markdown");
    pendingNode.innerHTML = markdownToHtml(payload.answer || "(空响应)");
    setStatus(
      `完成：${payload.total_tool_calls} 次工具调用，耗时 ${Number(payload.total_latency || 0).toFixed(2)}s`
    );
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

async function resetConversation() {
  try {
    await fetch("/api/reset", { method: "POST" });
  } catch (_) {
  }

  messages.innerHTML = "";
  messageCount = 0;
  setHasMessages(false);
  setStatus("已开始新对话");
  input.focus();
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

newChatBtn.addEventListener("click", resetConversation);

setHasMessages(false);
autoResize();
input.focus();
