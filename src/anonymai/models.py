from dataclasses import dataclass
from enum import Enum


class PIIType(str, Enum):
    """Values match Presidio's entity_type strings exactly, so a Presidio
    result can be turned into a PIIType with no translation table."""

    PERSON = "PERSON"
    LOCATION = "LOCATION"
    ORGANIZATION = "ORGANIZATION"
    NRP = "NRP"
    EMAIL_ADDRESS = "EMAIL_ADDRESS"
    PHONE_NUMBER = "PHONE_NUMBER"
    CREDIT_CARD = "CREDIT_CARD"
    CRYPTO = "CRYPTO"
    DATE_TIME = "DATE_TIME"
    IBAN_CODE = "IBAN_CODE"
    IP_ADDRESS = "IP_ADDRESS"
    MAC_ADDRESS = "MAC_ADDRESS"
    MEDICAL_LICENSE = "MEDICAL_LICENSE"
    UK_NHS = "UK_NHS"
    URL = "URL"
    US_BANK_NUMBER = "US_BANK_NUMBER"
    US_DRIVER_LICENSE = "US_DRIVER_LICENSE"
    US_ITIN = "US_ITIN"
    US_PASSPORT = "US_PASSPORT"
    US_SSN = "US_SSN"


class ScrubStrategy(Enum):
    MOCK = "mock"


@dataclass(frozen=True)
class PIIEntity:
    text: str
    pii_type: PIIType
    start: int
    end: int
    score: float


@dataclass(frozen=True)
class ScrubResult:
    scrubbed_text: str
    mapping: dict[str, str]  # replacement -> original
