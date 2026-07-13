const API_BASE = "http://localhost:8000";

async function call(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.action === "scrub") {
    call("/scrub", { text: msg.text }).then(
      (result) => sendResponse({ ok: true, result }),
      (err) => sendResponse({ ok: false, error: err.message }),
    );
    return true;
  }
  if (msg.action === "unscrub") {
    call("/unscrub", { text: msg.text, mapping: msg.mapping }).then(
      (result) => sendResponse({ ok: true, result }),
      (err) => sendResponse({ ok: false, error: err.message }),
    );
    return true;
  }
});
