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
_MONTHS = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def _digits(n: int) -> str:
    return "".join(random.choices(string.digits, k=n))


def _fake_email() -> str:
    local = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"{local}@{random.choice(_EMAIL_DOMAINS)}"


def _fake_phone() -> str:
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"


def _fake_credit_card() -> str:
    return " ".join(_digits(4) for _ in range(4))


def _fake_crypto() -> str:
    alphabet = string.ascii_letters + string.digits
    return "1" + "".join(random.choices(alphabet, k=random.randint(25, 34)))


def _fake_date_time() -> str:
    return f"{random.choice(_MONTHS)} {random.randint(1, 28)}, {random.randint(1950, 2024)}"


def _fake_iban() -> str:
    country = "".join(random.choices(string.ascii_uppercase, k=2))
    return f"{country}{_digits(2)}{''.join(random.choices(string.ascii_uppercase + string.digits, k=18))}"


def _fake_ip_address() -> str:
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


def _fake_mac_address() -> str:
    return ":".join(f"{random.randint(0, 255):02X}" for _ in range(6))


def _fake_medical_license() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=2)) + _digits(7)


def _fake_uk_nhs() -> str:
    return f"{_digits(3)} {_digits(3)} {_digits(4)}"


def _fake_url() -> str:
    path = "".join(random.choices(string.ascii_lowercase, k=6))
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


_GENERATED_TYPES = {
    PIIType.EMAIL_ADDRESS, PIIType.PHONE_NUMBER, PIIType.CREDIT_CARD, PIIType.CRYPTO,
    PIIType.DATE_TIME, PIIType.IBAN_CODE, PIIType.IP_ADDRESS, PIIType.MAC_ADDRESS,
    PIIType.MEDICAL_LICENSE, PIIType.UK_NHS, PIIType.URL, PIIType.US_BANK_NUMBER,
    PIIType.US_DRIVER_LICENSE, PIIType.US_ITIN, PIIType.US_PASSPORT, PIIType.US_SSN,
}

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
