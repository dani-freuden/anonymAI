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
