"""hCaptcha solver using cloud vision."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput

if TYPE_CHECKING:
    from captcha_solver.models.cloud_backend import CloudBackend


class HCaptchaSolver(BaseSolver):
    def __init__(self, backend: CloudBackend | None = None):
        self._backend = backend

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.HCAPTCHA

    @property
    def name(self) -> str:
        return "HCaptchaSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.image is not None

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        if solver_input.image is None:
            raise ValueError("HCaptchaSolver requires an image")

        start = time.perf_counter()
        backend = self._get_backend()

        prompt_text = solver_input.metadata.get(
            "challenge_prompt",
            "Select all images that match the description.",
        )
        grid_size = solver_input.metadata.get("grid_size", (3, 3))

        positions = backend.solve_grid_captcha(
            solver_input.image, prompt_text, grid_size
        )
        elapsed = (time.perf_counter() - start) * 1000

        return CaptchaResult(
            solution=",".join(str(p) for p in positions),
            captcha_type=CaptchaType.HCAPTCHA.value,
            confidence=0.75,
            solver_name=self.name,
            elapsed_ms=elapsed,
            raw={"positions": positions, "grid_size": list(grid_size)},
        )

    def _get_backend(self) -> CloudBackend:
        if self._backend is not None:
            return self._backend
        from captcha_solver.config import Settings
        from captcha_solver.models.cloud_backend import CloudBackend

        settings = Settings()
        self._backend = CloudBackend(
            provider=settings.cloud_provider,
            api_key=(
                settings.anthropic_api_key
                if settings.cloud_provider == "anthropic"
                else settings.openai_api_key
            ),
        )
        return self._backend
