# anonymAI

Scrub personal data out of text before sending it to an LLM, then unscrub the
reply so you get your own data back.

Phase 1: a backend-only Python package (no API, no extension yet).

## Setup

```
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
```

## Usage

```python
from anonymai import PIIType, ScrubStrategy, find_pii, scrub, unscrub

text = "My name is Daniel and I'm from Jerusalem."

for entity in find_pii(text):
    print(entity)

result = scrub(text, strategy=ScrubStrategy.MOCK, exclude_pii=[PIIType.LOCATION])
print(result.scrubbed_text)

print(unscrub(result.scrubbed_text, result))
```

See `examples/basic_usage.py` for a full walkthrough. Run tests with `pytest`.

## Phase 2: HTTP API

```
uvicorn anonymai.api:app --reload
```

Open http://localhost:8000 for a browser client (paste text, pick which PII
categories to scrub, copy the result, unscrub it back).

```
curl -X POST localhost:8000/pii -H 'content-type: application/json' \
  -d '{"text": "My name is Daniel and I am from Jerusalem."}'

curl -X POST localhost:8000/scrub -H 'content-type: application/json' \
  -d '{"text": "My name is Daniel and I am from Jerusalem.", "exclude_pii": ["LOCATION"]}'

curl -X POST localhost:8000/unscrub -H 'content-type: application/json' \
  -d '{"text": "<scrubbed_text from /scrub>", "mapping": {"<from /scrub response>": "..."}}'
```

The mapping returned by `/scrub` is not stored server-side — hold onto it
and send it back to `/unscrub`.

## Phase 3: Chrome extension

Adds a Scrub / Unscrub toolbar to the ChatGPT and Gemini compose box.
Requires the phase 2 server running locally
(`uvicorn anonymai.api:app --reload`).

1. Open `chrome://extensions`, enable Developer mode.
2. Click "Load unpacked", select the `extension/` directory.
3. On chatgpt.com or gemini.google.com, type a message, click **Scrub**,
   review the replacement text, then send it yourself as usual.
4. After a reply comes back, click **Unscrub last reply** to see the
   original values in a popup panel.

Gemini's compose/reply selectors haven't been checked against a live tab
(no browser access when this was built) — if the toolbar doesn't show up
or "Unscrub" can't find the reply on gemini.google.com, the DOM selectors
in `extension/content.js` (`COMPOSER_SELECTORS`/`ASSISTANT_SELECTORS`)
need updating to match the current page.

The mapping is held in memory for the tab only — reloading the page clears
it, same as `/unscrub` never being backed by server-side storage.
