from anonymai.detectors.presidio_detector import PresidioDetector
from anonymai.models import PIIEntity, PIIType, ScrubResult, ScrubStrategy
from anonymai.scrubbers.mock_strategy import MockScrubStrategy

_DETECTOR = PresidioDetector()

_STRATEGIES = {
    ScrubStrategy.MOCK: MockScrubStrategy(),
}


def find_pii(text: str) -> list[PIIEntity]:
    return _DETECTOR.detect(text)


def scrub(
    text: str,
    strategy: ScrubStrategy = ScrubStrategy.MOCK,
    exclude_pii: list[PIIType] | None = None,
    entities: list[PIIEntity] | None = None,
) -> ScrubResult:
    if entities is None:
        entities = find_pii(text)

    exclude_pii = exclude_pii or []
    entities = [e for e in entities if e.pii_type not in exclude_pii]

    return _STRATEGIES[strategy].scrub(text, entities)


def unscrub(text: str, result: ScrubResult) -> str:
    unscrubbed_text = text
    for replacement, original in sorted(
        result.mapping.items(), key=lambda kv: len(kv[0]), reverse=True
    ):
        unscrubbed_text = unscrubbed_text.replace(replacement, original)
    return unscrubbed_text
