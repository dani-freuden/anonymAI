from abc import ABC, abstractmethod

from anonymai.models import PIIEntity


class PIIDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> list[PIIEntity]:
        """Find PII entities in text."""
