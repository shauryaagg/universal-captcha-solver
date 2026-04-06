"""Abstract model backend interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class BoundingBox:
    x: float
    y: float
    width: float
    height: float
    label: str = ""
    confidence: float = 0.0


class ModelBackend(ABC):
    @abstractmethod
    def ocr(self, image: bytes) -> str:
        """Extract text from image."""
        ...

    @abstractmethod
    def classify_image(self, image: bytes, labels: list[str] | None = None) -> str:
        """Classify an image, optionally from given labels."""
        ...

    @abstractmethod
    def detect_objects(self, image: bytes) -> list[BoundingBox]:
        """Detect and locate objects in image."""
        ...

    @abstractmethod
    def transcribe_audio(self, audio: bytes) -> str:
        """Transcribe audio to text."""
        ...
