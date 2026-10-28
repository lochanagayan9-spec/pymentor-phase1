// PyMentor Client Application
document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const btnSend = document.getElementById("btn-send");
  const sessionIdDisplay = document.getElementById("session-id-display");
  const sessionBadge = document.getElementById("session-badge");
  const btnResetSession = document.getElementById("btn-reset-session");
  const btnViewLogs = document.getElementById("btn-view-logs");
  const logsModal = document.getElementById("logs-modal");
  const btnCloseModal = document.getElementById("btn-close-modal");
  const btnRefreshLogs = document.getElementById("btn-refresh-logs");
  const logsTableBody = document.getElementById("logs-table-body");
  const chipsContainer = document.getElementById("chips-container");

  // State
  let sessionId = localStorage.getItem("pymentor_session_id");
  if (!sessionId) {
    sessionId = generateUUID();
    localStorage.setItem("pymentor_session_id", sessionId);
  }

  updateSessionDisplay();

  // Configure Marked.js
  if (window.marked) {
    marked.setOptions({
      breaks: true,
      gfm: true,
      highlight: function (code, lang) {
        if (lang && hljs.getLanguage(lang)) {
          return hljs.highlight(code, { language: lang }).value;
        }
        return hljs.highlightAuto(code).value;
      }
    });
  }

  // Auto-resize textarea
  userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 140) + "px";
  });

  // Handle Enter key (Shift+Enter for newline)
  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Handle Form Submission
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    // Reset input
    userInput.value = "";
    userInput.style.height = "auto";
    btnSend.disabled = true;

    // Append User Message Bubble
    appendUserMessage(message);

    // Show Typing Indicator
    const typingId = showTypingIndicator();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: message
        })
      });

      removeTypingIndicator(typingId);

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        const errorText = errData.detail || "Server returned an error. Please try again.";
        appendAssistantMessage(
          `**Error (${response.status})**: ${errorText}`,
          0,
          "error"
        );
        return;
      }

      const data = await response.json();
      appendAssistantMessage(data.response, data.response_time_ms, data.status, data.model_used);
    } catch (err) {
      removeTypingIndicator(typingId);
      appendAssistantMessage(
        `**Connection Error**: Unable to reach PyMentor server. Please check your internet connection and verify the server is running.\n\n*Details: ${err.message}*`,
        0,
        "error"
      );
    } finally {
      btnSend.disabled = false;
      userInput.focus();
    }
  });

  // Suggestion Chips
  chipsContainer.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    const prompt = chip.getAttribute("data-prompt");
    if (prompt) {
      userInput.value = prompt;
      userInput.style.height = "auto";
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Session Badge Copy
  sessionBadge.addEventListener("click", () => {
    navigator.clipboard.writeText(sessionId).then(() => {
      const orig = sessionIdDisplay.textContent;
      sessionIdDisplay.textContent = "Copied ID!";
      setTimeout(() => {
        sessionIdDisplay.textContent = orig;
      }, 1500);
    });
  });

  // Reset Session
  btnResetSession.addEventListener("click", async () => {
    if (confirm("Reset current conversation memory and start a fresh session?")) {
      try {
        await fetch("/api/session/reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sessionId })
        });
      } catch (e) {
        console.warn("Reset error:", e);
      }
      sessionId = generateUUID();
      localStorage.setItem("pymentor_session_id", sessionId);
      updateSessionDisplay();

      // Clear UI
      chatMessages.innerHTML = `
        <div class="message-row assistant-row">
          <div class="avatar">??</div>
          <div class="bubble assistant-bubble">
            <div class="assistant-name">PyMentor</div>
            <div class="bubble-content markdown-body">
              <p>Memory cleared! I am ready for a fresh Python exploration. Ask me about syntax, memory models, functions, or paste a snippet to analyze.</p>
            </div>
          </div>
        </div>
      `;
    }
  });

  // View Logs Modal
  btnViewLogs.addEventListener("click", () => {
    logsModal.style.display = "flex";
    loadLogsAndAnalytics();
  });

  btnCloseModal.addEventListener("click", () => {
    logsModal.style.display = "none";
  });

  logsModal.addEventListener("click", (e) => {
    if (e.target === logsModal) {
      logsModal.style.display = "none";
    }
  });

  btnRefreshLogs.addEventListener("click", () => {
    loadLogsAndAnalytics();
  });

  // Functions
  function updateSessionDisplay() {
    sessionIdDisplay.textContent = `Session: ${sessionId.slice(0, 8)}...`;
  }

  function appendUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row user-row";
    row.innerHTML = `
      <div class="avatar">??</div>
      <div class="bubble user-bubble">${escapeHtml(text)}</div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
  }

    function appendAssistantMessage(markdownText, latencyMs, status, modelUsed) {
    const row = document.createElement("div");
    row.className = "message-row assistant-row";

    let parsedHtml = "";
    if (window.marked) {
      parsedHtml = marked.parse(markdownText);
    } else {
      parsedHtml = `<pre>${escapeHtml(markdownText)}</pre>`;
    }

    const latencyTag = latencyMs > 0 ? `<span class="latency-badge">? ${latencyMs} ms</span>` : "";
        const statusTag = status ? `<span class="status-tag status-${status}">${status.replace("_", " ")}</span>` : "";
    const modelTag = (modelUsed && modelUsed !== "none") ? `<span class="model-badge">?? ${modelUsed}</span>` : "";

    row.innerHTML = `
      <div class="avatar">??</div>
      <div class="bubble assistant-bubble">
        <div class="assistant-name">PyMentor</div>
        <div class="bubble-content markdown-body">${parsedHtml}</div>
        <div class="bubble-footer">
                    <div style="display:flex; align-items:center; gap:8px;">${statusTag}${modelTag}</div>
          <div>${latencyTag}</div>
        </div>
      </div>
    `;

    chatMessages.appendChild(row);

    // Attach copy buttons to code blocks
    row.querySelectorAll("pre").forEach((pre) => {
      const code = pre.querySelector("code");
      if (!code) return;
      const copyBtn = document.createElement("button");
      copyBtn.className = "code-copy-btn";
      copyBtn.textContent = "Copy";
      copyBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(code.innerText).then(() => {
          copyBtn.textContent = "Copied!";
          setTimeout(() => (copyBtn.textContent = "Copy"), 1800);
        });
      });
      pre.appendChild(copyBtn);
    });

    scrollToBottom();
  }

  function showTypingIndicator() {
    const id = "typing-" + Date.now();
    const row = document.createElement("div");
    row.id = id;
    row.className = "message-row assistant-row";
    row.innerHTML = `
      <div class="avatar">??</div>
      <div class="bubble assistant-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    chatMessages.appendChild(row);
    scrollToBottom();
    return id;
  }

  function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  }

  function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  async function loadLogsAndAnalytics() {
    try {
      // 1. Fetch Analytics
      const resAnalytics = await fetch("/api/logs/analytics");
      if (resAnalytics.ok) {
        const stats = await resAnalytics.json();
        document.getElementById("metric-total").textContent = stats.total_messages;
        document.getElementById("metric-latency").textContent = `${stats.avg_latency_ms} ms`;
        document.getElementById("metric-tokens").textContent = stats.total_tokens.toLocaleString();
        document.getElementById("metric-success").textContent = stats.success_count;
        document.getElementById("metric-oos").textContent = stats.out_of_scope_count;
      }

      // 2. Fetch Recent Logs
      const resLogs = await fetch("/api/logs?limit=40");
      if (resLogs.ok) {
        const data = await resLogs.json();
        if (data.logs.length === 0) {
          logsTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted);">No interactions logged yet. Ask a question to generate logs!</td></tr>`;
          return;
        }

        logsTableBody.innerHTML = data.logs.map(log => {
          const shortTime = log.timestamp.split("T")[1]?.slice(0, 8) || log.timestamp;
          const statusClass = `pill-${log.status}`;
          const shortQuery = log.user_message.length > 50 ? log.user_message.slice(0, 48) + "..." : log.user_message;
          const shortReply = log.bot_response.length > 70 ? log.bot_response.slice(0, 68) + "..." : log.bot_response;

          return `
            <tr>
              <td><strong>#${log.id}</strong></td>
              <td title="${log.timestamp}">${shortTime}</td>
              <td><span class="log-status-pill ${statusClass}">${log.status}</span></td>
              <td><code>${log.response_time_ms} ms</code></td>
              <td>${escapeHtml(shortQuery)}</td>
              <td title="${escapeHtml(log.bot_response)}">${escapeHtml(shortReply)}</td>
            </tr>
          `;
        }).join("");
      }
    } catch (e) {
      logsTableBody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--accent-red);">Failed to load logs: ${e.message}</td></tr>`;
    }
  }

  function generateUUID() {
    return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, function (c) {
      const r = (Math.random() * 16) | 0;
      const v = c === "x" ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
