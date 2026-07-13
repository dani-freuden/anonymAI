let lastMapping = null;

// Multiple candidates per site since these are third-party DOMs that can
// change without notice — first match wins.
const COMPOSER_SELECTORS = [
  "#prompt-textarea", // ChatGPT
  "div.ql-editor[contenteditable='true']", // Gemini
];
const ASSISTANT_SELECTORS = [
  '[data-message-author-role="assistant"]', // ChatGPT
  "message-content .markdown", // Gemini
];

function getComposer() {
  for (const sel of COMPOSER_SELECTORS) {
    const el = document.querySelector(sel);
    if (el) return el;
  }
  return null;
}

function setComposerText(el, text) {
  el.focus();
  el.innerText = text;
  el.dispatchEvent(new InputEvent("input", { bubbles: true }));
}

function latestAssistantText() {
  for (const sel of ASSISTANT_SELECTORS) {
    const nodes = document.querySelectorAll(sel);
    if (nodes.length) return nodes[nodes.length - 1].innerText;
  }
  return null;
}

function showToast(message, isError = false) {
  let toast = document.getElementById("anonymai-toast");
  if (toast) toast.remove();
  toast = document.createElement("div");
  toast.id = "anonymai-toast";
  toast.className = isError ? "anonymai-toast-error" : "anonymai-toast-ok";
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

function showPanel(title, text) {
  let panel = document.getElementById("anonymai-panel");
  if (panel) panel.remove();
  panel = document.createElement("div");
  panel.id = "anonymai-panel";

  const header = document.createElement("div");
  header.className = "anonymai-panel-header";
  const titleEl = document.createElement("span");
  titleEl.textContent = title;
  const closeBtn = document.createElement("button");
  closeBtn.className = "anonymai-panel-close";
  closeBtn.textContent = "✕";
  closeBtn.onclick = () => panel.remove();
  header.append(titleEl, closeBtn);

  const body = document.createElement("div");
  body.className = "anonymai-panel-body";
  body.textContent = text;

  const footer = document.createElement("div");
  footer.className = "anonymai-panel-footer";
  const copyBtn = document.createElement("button");
  copyBtn.textContent = "Copy";
  copyBtn.onclick = () => {
    navigator.clipboard.writeText(text);
    copyBtn.textContent = "Copied!";
    setTimeout(() => (copyBtn.textContent = "Copy"), 1200);
  };
  footer.append(copyBtn);

  panel.append(header, body, footer);
  document.body.appendChild(panel);
}

function onScrubClick(btn) {
  const composer = getComposer();
  if (!composer) return;
  const text = composer.innerText;
  if (!text.trim()) return;
  btn.disabled = true;
  btn.classList.add("anonymai-busy");
  chrome.runtime.sendMessage({ action: "scrub", text }, (res) => {
    btn.disabled = false;
    btn.classList.remove("anonymai-busy");
    if (!res?.ok) {
      showToast(`Scrub failed: ${res?.error ?? "no response"} — is the server running?`, true);
      return;
    }
    lastMapping = res.result.mapping;
    setComposerText(composer, res.result.scrubbed_text);
    const count = Object.keys(res.result.mapping).length;
    showToast(count ? `Scrubbed ${count} item${count === 1 ? "" : "s"}` : "No PII found");
  });
}

function onUnscrubClick(btn) {
  if (!lastMapping || Object.keys(lastMapping).length === 0) {
    showToast("Nothing to unscrub yet — click Scrub first.", true);
    return;
  }
  const text = latestAssistantText();
  if (!text) {
    showToast("No reply found to unscrub.", true);
    return;
  }
  btn.disabled = true;
  btn.classList.add("anonymai-busy");
  chrome.runtime.sendMessage({ action: "unscrub", text, mapping: lastMapping }, (res) => {
    btn.disabled = false;
    btn.classList.remove("anonymai-busy");
    if (!res?.ok) {
      showToast(`Unscrub failed: ${res?.error ?? "no response"} — is the server running?`, true);
      return;
    }
    showPanel("Unscrubbed reply", res.result.text);
  });
}

function injectButtons() {
  const composer = getComposer();
  if (!composer || document.getElementById("anonymai-scrub-btn")) return;

  const bar = document.createElement("div");
  bar.id = "anonymai-toolbar";

  const scrubBtn = document.createElement("button");
  scrubBtn.id = "anonymai-scrub-btn";
  scrubBtn.className = "anonymai-btn anonymai-btn-primary";
  scrubBtn.innerHTML = "🧹 Scrub";
  scrubBtn.onclick = () => onScrubClick(scrubBtn);

  const unscrubBtn = document.createElement("button");
  unscrubBtn.className = "anonymai-btn";
  unscrubBtn.innerHTML = "🔓 Unscrub last reply";
  unscrubBtn.onclick = () => onUnscrubClick(unscrubBtn);

  bar.append(scrubBtn, unscrubBtn);
  composer.parentElement.insertBefore(bar, composer);
}

const style = document.createElement("style");
style.textContent = `
  #anonymai-toolbar {
    display: flex; gap: 8px; margin-bottom: 8px;
  }
  .anonymai-btn {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 6px 12px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.15);
    background: #2f2f2f; color: #eaeaea; cursor: pointer; font-size: 12.5px;
    font-family: inherit; transition: background 0.15s, transform 0.1s;
  }
  .anonymai-btn:hover { background: #3d3d3d; }
  .anonymai-btn:active { transform: scale(0.97); }
  .anonymai-btn:disabled { opacity: 0.6; cursor: default; }
  .anonymai-btn-primary { background: #10a37f; border-color: #10a37f; color: #fff; }
  .anonymai-btn-primary:hover { background: #0e8f6f; }
  .anonymai-busy { animation: anonymai-pulse 1s ease-in-out infinite; }
  @keyframes anonymai-pulse { 50% { opacity: 0.5; } }

  #anonymai-toast {
    position: fixed; bottom: 24px; right: 24px; z-index: 999999;
    padding: 10px 16px; border-radius: 8px; font-size: 13px; color: #fff;
    box-shadow: 0 4px 16px rgba(0,0,0,0.4);
    animation: anonymai-toast-in 0.2s ease-out;
  }
  .anonymai-toast-ok { background: #10a37f; }
  .anonymai-toast-error { background: #b3382c; }
  @keyframes anonymai-toast-in {
    from { opacity: 0; transform: translateY(6px); }
    to { opacity: 1; transform: translateY(0); }
  }

  #anonymai-panel {
    position: fixed; bottom: 24px; right: 24px; width: 340px;
    background: #1f1f1f; color: #eaeaea; border: 1px solid rgba(255,255,255,0.15);
    border-radius: 10px; z-index: 999999; font-size: 13px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.45);
    animation: anonymai-toast-in 0.2s ease-out;
    overflow: hidden;
  }
  #anonymai-panel .anonymai-panel-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 10px 12px; font-weight: 600; background: #262626;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }
  #anonymai-panel .anonymai-panel-close {
    background: none; border: none; color: #aaa; cursor: pointer; font-size: 13px; padding: 2px 6px;
  }
  #anonymai-panel .anonymai-panel-close:hover { color: #fff; }
  #anonymai-panel .anonymai-panel-body {
    white-space: pre-wrap; padding: 12px; max-height: 300px; overflow-y: auto;
  }
  #anonymai-panel .anonymai-panel-footer {
    padding: 8px 12px; border-top: 1px solid rgba(255,255,255,0.1); text-align: right;
  }
`;
document.head.appendChild(style);

new MutationObserver(injectButtons).observe(document.body, { childList: true, subtree: true });
injectButtons();
