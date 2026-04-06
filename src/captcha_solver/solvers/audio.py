"""Audio captcha solver using speech-to-text."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput

if TYPE_CHECKING:
    from captcha_solver.models.backend import ModelBackend


class AudioSolver(BaseSolver):
    """Solve audio captchas using speech-to-text."""

    def __init__(self, backend: ModelBackend | None = None):
        self._backend = backend

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.AUDIO

    @property
    def name(self) -> str:
        return "AudioSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.audio is not None

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        if solver_input.audio is None:
            raise ValueError("AudioSolver requires audio input")

        start = time.perf_counter()
        backend = self._get_backend()

        text = backend.transcribe_audio(solver_input.audio)
        elapsed = (time.perf_counter() - start) * 1000

        # Clean up: captcha audio usually contains digits or simple words
        text = text.strip().lower()
        # Remove common filler words
        text = text.replace(".", "").replace(",", "").strip()

        return CaptchaResult(
            solution=text,
            captcha_type=CaptchaType.AUDIO.value,
            confidence=0.80,
            solver_name=self.name,
            elapsed_ms=elapsed,
        )

    def _get_backend(self) -> ModelBackend:
        if self._backend is not None:
            return self._backend
        from captcha_solver.config import Settings

        settings = Settings()
        if settings.model_backend == "cloud":
            from captcha_solver.models.cloud_backend import CloudBackend

            self._backend = CloudBackend(
                provider=settings.cloud_provider,
                api_key=(
                    settings.anthropic_api_key
                    if settings.cloud_provider == "anthropic"
                    else settings.openai_api_key
                ),
            )
        else:
            from captcha_solver.models.onnx_backend import OnnxBackend

            self._backend = OnnxBackend(
                model_dir=settings.model_dir,
                gpu_enabled=settings.gpu_enabled,
            )
        return self._backend
