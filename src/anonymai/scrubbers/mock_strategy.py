import json
import random
import string
from importlib import resources

from anonymai.models import PIIEntity, PIIType, ScrubResult
from anonymai.scrubbers.base import Scrubber

_WORD_BANK: dict[str, list[str]] = json.loads(
    resources.files("anonymai.data").joinpath("mock_words.json").read_text()
)

_EMAIL_DOMAINS = ["example.com", "mailbox.net", "inboxpro.com", "cloudpost.io", "mailhub.org"]

_GENERATED_TYPES = {PIIType.EMAIL_ADDRESS, PIIType.PHONE_NUMBER}


def _fake_email() -> str:
    local = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"{local}@{random.choice(_EMAIL_DOMAINS)}"


def _fake_phone() -> str:
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"


_GENERATORS = {
    PIIType.EMAIL_ADDRESS: _fake_email,
    PIIType.PHONE_NUMBER: _fake_phone,
}


def _pick_replacement(pii_type: PIIType, original: str) -> str:
    if pii_type in _GENERATED_TYPES:
        return _GENERATORS[pii_type]()
    choices = [w for w in _WORD_BANK[pii_type.value] if w.lower() != original.lower()]
    return random.choice(choices)


class MockScrubStrategy(Scrubber):
    def scrub(self, text: str, entities: list[PIIEntity]) -> ScrubResult:
        replacement_by_original: dict[str, str] = {}
        for entity in entities:
            key = entity.text.lower()
            if key not in replacement_by_original:
                replacement_by_original[key] = _pick_replacement(entity.pii_type, entity.text)

        scrubbed_text = text
        for entity in sorted(entities, key=lambda e: e.start, reverse=True):
            replacement = replacement_by_original[entity.text.lower()]
            scrubbed_text = scrubbed_text[: entity.start] + replacement + scrubbed_text[entity.end :]

        mapping = {}
        for entity in entities:
            replacement = replacement_by_original[entity.text.lower()]
            mapping[replacement] = entity.text

        return ScrubResult(scrubbed_text=scrubbed_text, mapping=mapping)
