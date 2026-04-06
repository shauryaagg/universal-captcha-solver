"""Text/image captcha solver using OCR."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from captcha_solver.core.result import CaptchaResult
from captcha_solver.preprocessing.image import denoise, threshold, to_grayscale
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput

if TYPE_CHECKING:
    from captcha_solver.models.backend import ModelBackend


class TextSolver(BaseSolver):
    def __init__(self, backend: ModelBackend | None = None):
        self._backend = backend

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.TEXT

    @property
    def name(self) -> str:
        return "TextSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.image is not None

    def preprocess(self, solver_input: SolverInput) -> SolverInput:
        if solver_input.image is None:
            return solver_input
        image = solver_input.image
        image = to_grayscale(image)
        image = denoise(image)
        image = threshold(image, value=128)
        return SolverInput(
            image=image,
            audio=solver_input.audio,
            page_url=solver_input.page_url,
            site_key=solver_input.site_key,
            metadata=solver_input.metadata,
        )

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        if solver_input.image is None:
            raise ValueError("TextSolver requires an image input")

        start = time.perf_counter()
        backend = self._get_backend()
        text = backend.ocr(solver_input.image)
        elapsed = (time.perf_counter() - start) * 1000

        # Clean up OCR output
        text = text.strip()

        return CaptchaResult(
            solution=text,
            captcha_type=CaptchaType.TEXT.value,
            confidence=0.85,  # Default confidence for OCR
            solver_name=self.name,
            elapsed_ms=elapsed,
        )

    def _get_backend(self) -> ModelBackend:
        if self._backend is not None:
            return self._backend
        from captcha_solver.models.onnx_backend import OnnxBackend

        self._backend = OnnxBackend()
        return self._backend
