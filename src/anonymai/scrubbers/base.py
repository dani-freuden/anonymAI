from abc import ABC, abstractmethod

from anonymai.models import PIIEntity, ScrubResult


class Scrubber(ABC):
    @abstractmethod
    def scrub(self, text: str, entities: list[PIIEntity]) -> ScrubResult:
        """Replace the given entities in text, returning the scrubbed text
        and a mapping to reverse the replacement later."""
