import calendar
import datetime
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
_URL_DOMAINS = ["example.com", "sample.org", "placeholder.net", "demo-site.io"]


def _random_str(charset: str, n: int) -> str:
    return "".join(random.choices(charset, k=n))


def _digits(n: int) -> str:
    return _random_str(string.digits, n)


def _fake_email() -> str:
    local = _random_str(string.ascii_lowercase, 8)
    return f"{local}@{random.choice(_EMAIL_DOMAINS)}"


def _fake_phone() -> str:
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"


def _fake_credit_card() -> str:
    return " ".join(_digits(4) for _ in range(4))


def _fake_crypto() -> str:
    alphabet = string.ascii_letters + string.digits
    return "1" + _random_str(alphabet, random.randint(25, 34))


def _fake_date_time() -> str:
    year, month = random.randint(1950, 2024), random.randint(1, 12)
    day = random.randint(1, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day).strftime("%B %d, %Y")


def _fake_iban() -> str:
    country = _random_str(string.ascii_uppercase, 2)
    return f"{country}{_digits(2)}{_random_str(string.ascii_uppercase + string.digits, 18)}"


def _fake_ip_address() -> str:
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def _fake_mac_address() -> str:
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))


def _fake_medical_license() -> str:
    return _random_str(string.ascii_uppercase, 2) + _digits(7)


def _fake_uk_nhs() -> str:
    return f"{_digits(3)} {_digits(3)} {_digits(4)}"


def _fake_url() -> str:
    path = _random_str(string.ascii_lowercase, 6)
    return f"https://{random.choice(_URL_DOMAINS)}/{path}"


def _fake_us_bank_number() -> str:
    return _digits(random.randint(8, 12))


def _fake_us_driver_license() -> str:
    return random.choice(string.ascii_uppercase) + _digits(7)


def _fake_us_itin() -> str:
    return f"9{random.randint(0, 9)}{random.randint(0, 9)}-{random.randint(70, 88)}-{_digits(4)}"


def _fake_us_passport() -> str:
    return random.choice(string.ascii_uppercase) + _digits(8)


def _fake_us_ssn() -> str:
    return f"{_digits(3)}-{_digits(2)}-{_digits(4)}"


_GENERATORS = {
    PIIType.EMAIL_ADDRESS: _fake_email,
    PIIType.PHONE_NUMBER: _fake_phone,
    PIIType.CREDIT_CARD: _fake_credit_card,
    PIIType.CRYPTO: _fake_crypto,
    PIIType.DATE_TIME: _fake_date_time,
    PIIType.IBAN_CODE: _fake_iban,
    PIIType.IP_ADDRESS: _fake_ip_address,
    PIIType.MAC_ADDRESS: _fake_mac_address,
    PIIType.MEDICAL_LICENSE: _fake_medical_license,
    PIIType.UK_NHS: _fake_uk_nhs,
    PIIType.URL: _fake_url,
    PIIType.US_BANK_NUMBER: _fake_us_bank_number,
    PIIType.US_DRIVER_LICENSE: _fake_us_driver_license,
    PIIType.US_ITIN: _fake_us_itin,
    PIIType.US_PASSPORT: _fake_us_passport,
    PIIType.US_SSN: _fake_us_ssn,
}
_GENERATED_TYPES = set(_GENERATORS)


def _pick_replacement(pii_type: PIIType, original: str, avoid: set[str] = frozenset()) -> str:
    if pii_type in _GENERATED_TYPES:
        return _GENERATORS[pii_type]()
    choices = [w for w in _WORD_BANK[pii_type.value] if w.lower() != original.lower() and w.lower() not in avoid]
    # ponytail: falls back to ignoring `avoid` if it exhausts the bank; a repeat
    # replacement word is far cheaper to accept than crashing on an empty choice.
    return random.choice(choices or _WORD_BANK[pii_type.value])


def _pick_person_tokens(n: int, avoid: set[str]) -> list[str]:
    bank = [w for w in _WORD_BANK[PIIType.PERSON.value] if w.lower() not in avoid]
    if n > len(bank):
        bank = _WORD_BANK[PIIType.PERSON.value]  # ponytail: same fallback as _pick_replacement
    return random.sample(bank, k=n) if n <= len(bank) else random.choices(bank, k=n)


def _person_replacements(
    entities: list[PIIEntity],
    known_mapping: dict[str, str] | None = None,
    used_replacement_words: set[str] = frozenset(),
) -> dict[str, str]:
    """Map each distinct PERSON mention (lowercased) to a replacement name.

    A short mention (e.g. "Daniel") made up entirely of tokens from a
    longer mention seen elsewhere in the same text (e.g. "Daniel Cohen")
    reuses that mention's replacement tokens position-for-position, so the
    same person keeps the same fake name everywhere instead of each
    surface form getting an independently randomized one.

    known_mapping (replacement -> original from earlier scrub() calls in
    the same conversation) seeds the same alias matching, so a bare
    "Daniel" in a later message can still alias to "Daniel Cohen" from an
    earlier one even though this call never saw the full name.
    """
    seen: list[str] = []
    seen_set: set[str] = set()
    for entity in entities:
        if entity.pii_type == PIIType.PERSON and entity.text.lower() not in seen_set:
            seen_set.add(entity.text.lower())
            seen.append(entity.text.lower())
    surface_forms = sorted(seen, key=lambda text: -len(text.split()))

    canonicals: list[tuple[list[str], list[str]]] = []
    for replacement, original in (known_mapping or {}).items():
        orig_tokens = original.lower().split()
        repl_tokens = replacement.split()
        # Multi-token only: a single-token known mention (e.g. a LOCATION like
        # "Paris") can't tell us anything a full alias for a *shorter* mention
        # would need, and single-token exact reuse is already handled by
        # known_original_to_replacement in scrub() — restricting to >=2 tokens
        # keeps this from mistaking an unrelated same-shaped mapping entry
        # (any type) for a PERSON canonical.
        if (
            len(orig_tokens) >= 2
            and len(orig_tokens) == len(repl_tokens)
            and all(any(c.isalpha() for c in t) for t in orig_tokens)
        ):
            canonicals.append((orig_tokens, repl_tokens))

    replacement_by_text: dict[str, str] = {}
    for text in surface_forms:
        tokens = text.split()
        # ponytail: when two distinct canonicals both contain a shared token
        # (e.g. "Daniel Cohen" and "David Cohen"), a later bare "Cohen"
        # resolves to whichever was registered first — real disambiguation
        # needs coreference resolution, out of scope here.
        match = next((c for c in canonicals if set(tokens) <= set(c[0])), None)
        if match:
            orig_tokens, repl_tokens = match
            replacement = " ".join(repl_tokens[orig_tokens.index(t)] for t in tokens)
        else:
            repl_tokens = _pick_person_tokens(len(tokens), avoid=set(tokens) | used_replacement_words)
            replacement = " ".join(repl_tokens)
            canonicals.append((tokens, repl_tokens))
        replacement_by_text[text] = replacement
    return replacement_by_text


class MockScrubStrategy(Scrubber):
    def scrub(
        self, text: str, entities: list[PIIEntity], known_mapping: dict[str, str] | None = None
    ) -> ScrubResult:
        known_mapping = known_mapping or {}
        known_original_to_replacement = {o.lower(): r for r, o in known_mapping.items()}
        # Words already spent as replacements this conversation: excluding them
        # from new picks keeps two different originals from colliding onto the
        # same replacement (which would silently overwrite one's mapping entry).
        used_replacement_words = {w.lower() for repl in known_mapping for w in repl.split()}

        replacement_by_original: dict[str, str] = _person_replacements(
            entities, known_mapping, used_replacement_words
        )
        for entity in entities:
            key = entity.text.lower()
            if key in replacement_by_original:
                continue
            if key in known_original_to_replacement:
                replacement_by_original[key] = known_original_to_replacement[key]
            else:
                replacement_by_original[key] = _pick_replacement(
                    entity.pii_type, entity.text, used_replacement_words
                )

        scrubbed_text = text
        for entity in sorted(entities, key=lambda e: e.start, reverse=True):
            replacement = replacement_by_original[entity.text.lower()]
            scrubbed_text = scrubbed_text[: entity.start] + replacement + scrubbed_text[entity.end :]

        mapping = dict(known_mapping)
        for entity in entities:
            replacement = replacement_by_original[entity.text.lower()]
            mapping[replacement] = entity.text

        return ScrubResult(scrubbed_text=scrubbed_text, mapping=mapping)
