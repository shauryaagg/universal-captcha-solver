"""Cloud API inference backend."""
from __future__ import annotations

from captcha_solver.models.backend import BoundingBox, ModelBackend


class CloudBackend(ModelBackend):
    """Cloud vision backend (GPT-4V, Claude Vision). Full implementation in Phase 2."""

    def __init__(self, provider: str = "openai", api_key: str | None = None):
        self.provider = provider
        self.api_key = api_key

    def ocr(self, image: bytes) -> str:
        raise NotImplementedError(
            "Cloud OCR backend coming in Phase 2. "
            "Install: pip install universal-captcha-solver[cloud]"
        )

    def classify_image(self, image: bytes, labels: list[str] | None = None) -> str:
        raise NotImplementedError("Cloud classification coming in Phase 2.")

    def detect_objects(self, image: bytes) -> list[BoundingBox]:
        raise NotImplementedError("Cloud object detection coming in Phase 2.")

    def transcribe_audio(self, audio: bytes) -> str:
        raise NotImplementedError("Cloud audio transcription coming in Phase 2.")
