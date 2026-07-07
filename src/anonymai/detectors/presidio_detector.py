from functools import lru_cache

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

from anonymai.detectors.base import PIIDetector
from anonymai.models import PIIEntity, PIIType

_SUPPORTED_ENTITIES = [t.value for t in PIIType]

_NLP_CONFIGURATION = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
}


@lru_cache(maxsize=1)
def _get_analyzer() -> AnalyzerEngine:
    nlp_engine = NlpEngineProvider(nlp_configuration=_NLP_CONFIGURATION).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
    # Presidio's default SpacyRecognizer only declares PERSON/LOCATION/NRP/
    # DATE_TIME as supported; extend it so ORG -> ORGANIZATION is surfaced too.
    spacy_recognizer = analyzer.registry.get_recognizers(
        language="en", entities=["PERSON"]
    )[0]
    if PIIType.ORGANIZATION.value not in spacy_recognizer.supported_entities:
        spacy_recognizer.supported_entities.append(PIIType.ORGANIZATION.value)
    return analyzer


def _drop_overlaps(entities: list[PIIEntity]) -> list[PIIEntity]:
    """Different recognizers can tag the same span (e.g. an email also
    matching as ORGANIZATION); keep only the highest-confidence entity for
    each overlapping region so downstream replacement never double-edits
    the same text."""
    accepted: list[PIIEntity] = []
    for entity in sorted(entities, key=lambda e: e.score, reverse=True):
        if not any(entity.start < a.end and a.start < entity.end for a in accepted):
            accepted.append(entity)
    return sorted(accepted, key=lambda e: e.start)


class PresidioDetector(PIIDetector):
    def detect(self, text: str) -> list[PIIEntity]:
        results = _get_analyzer().analyze(
            text=text, entities=_SUPPORTED_ENTITIES, language="en"
        )
        entities = []
        for result in results:
            try:
                pii_type = PIIType(result.entity_type)
            except ValueError:
                continue
            entities.append(
                PIIEntity(
                    text=text[result.start : result.end],
                    pii_type=pii_type,
                    start=result.start,
                    end=result.end,
                    score=result.score,
                )
            )
        return _drop_overlaps(entities)
