"""ONNX Runtime inference backend."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from captcha_solver.models.backend import BoundingBox, ModelBackend


class OnnxBackend(ModelBackend):
    def __init__(
        self, model_dir: str = "~/.cache/captcha-solver/models", gpu_enabled: bool = False
    ):
        self.model_dir = Path(model_dir).expanduser()
        self.gpu_enabled = gpu_enabled
        self._sessions: dict[str, Any] = {}  # cache loaded sessions

    def _get_session(self, model_name: str) -> Any:
        """Load ONNX model, caching the session."""
        if model_name in self._sessions:
            return self._sessions[model_name]

        import onnxruntime as ort

        model_path = self.model_dir / f"{model_name}.onnx"
        if not model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {model_path}. "
                f"Run 'captcha-solver models download {model_name}'"
            )

        providers = (
            ["CUDAExecutionProvider", "CPUExecutionProvider"]
            if self.gpu_enabled
            else ["CPUExecutionProvider"]
        )
        session = ort.InferenceSession(str(model_path), providers=providers)
        self._sessions[model_name] = session
        return session

    def ocr(self, image: bytes) -> str:
        """OCR using ONNX model. Returns extracted text."""
        try:
            session = self._get_session("text_ocr_v1")
        except FileNotFoundError:
            raise RuntimeError(
                "No OCR model found. Download one with: "
                "captcha-solver models download text-ocr-v1\n"
                "Or set model_backend='cloud' to use cloud vision APIs."
            )
        from captcha_solver.preprocessing.image import normalize_for_model

        input_array = normalize_for_model(image)
        input_name = session.get_inputs()[0].name
        result = session.run(None, {input_name: input_array})
        return self._decode_ocr_output(result)

    def _decode_ocr_output(self, result: list[Any]) -> str:
        """Decode ONNX model output to string. Override for specific models."""
        output = result[0]
        if isinstance(output, np.ndarray) and output.ndim >= 2:
            indices = np.argmax(output, axis=-1).flatten()
            charset = "0123456789abcdefghijklmnopqrstuvwxyz"
            return "".join(charset[i] for i in indices if i < len(charset))
        return str(output)

    def classify_image(self, image: bytes, labels: list[str] | None = None) -> str:
        """Classify an image using ONNX model."""
        try:
            session = self._get_session("classifier_v1")
        except FileNotFoundError:
            raise RuntimeError("No classifier model found.")
        from captcha_solver.preprocessing.image import normalize_for_model

        input_array = normalize_for_model(image)
        input_name = session.get_inputs()[0].name
        result = session.run(None, {input_name: input_array})
        idx = int(np.argmax(result[0]))
        if labels and idx < len(labels):
            return labels[idx]
        return str(idx)

    def detect_objects(self, image: bytes) -> list[BoundingBox]:
        """Detect objects in image. Not yet implemented."""
        raise NotImplementedError("Object detection requires Phase 2+ models")

    def transcribe_audio(self, audio: bytes) -> str:
        """Transcribe audio to text. Not yet implemented."""
        raise NotImplementedError("Audio transcription requires Phase 3 audio models")
