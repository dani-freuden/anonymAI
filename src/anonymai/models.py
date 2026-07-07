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
