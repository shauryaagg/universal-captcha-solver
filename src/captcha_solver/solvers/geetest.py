"""GeeTest captcha solver."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput

if TYPE_CHECKING:
    from captcha_solver.models.backend import ModelBackend


class GeeTestSolver(BaseSolver):
    """Solve GeeTest captchas (slide, click, icon variants)."""

    def __init__(self, backend: ModelBackend | None = None):
        self._backend = backend

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.GEETEST

    @property
    def name(self) -> str:
        return "GeeTestSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.image is not None

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        if solver_input.image is None:
            raise ValueError("GeeTestSolver requires an image")

        start = time.perf_counter()

        # Determine GeeTest challenge type from metadata
        challenge_type = solver_input.metadata.get("geetest_type", "slide")

        if challenge_type == "slide":
            result = self._solve_slide(solver_input)
        elif challenge_type == "click":
            result = self._solve_click(solver_input)
        elif challenge_type == "icon":
            result = self._solve_icon(solver_input)
        else:
            result = self._solve_slide(solver_input)  # Default to slide

        elapsed = (time.perf_counter() - start) * 1000
        result.elapsed_ms = elapsed
        return result

    def _solve_slide(self, solver_input: SolverInput) -> CaptchaResult:
        """Solve GeeTest slide challenge -- find gap offset."""
        from captcha_solver.solvers.slider import SliderSolver

        slider = SliderSolver()
        result = slider.solve(solver_input)
        # Re-tag as GeeTest
        return CaptchaResult(
            solution=result.solution,
            captcha_type=CaptchaType.GEETEST.value,
            confidence=result.confidence,
            solver_name=self.name,
            elapsed_ms=result.elapsed_ms,
            raw={"challenge_type": "slide", "offset": result.solution},
        )

    def _solve_click(self, solver_input: SolverInput) -> CaptchaResult:
        """Solve GeeTest click challenge -- identify and return click coordinates."""
        backend = self._get_backend()

        # Use cloud vision to detect objects and their positions
        objects = backend.detect_objects(solver_input.image)

        if not objects:
            # Fallback: use classify to describe what to click
            description = backend.classify_image(solver_input.image)
            return CaptchaResult(
                solution=description,
                captcha_type=CaptchaType.GEETEST.value,
                confidence=0.5,
                solver_name=self.name,
                elapsed_ms=0,
                raw={"challenge_type": "click", "description": description},
            )

        # Return coordinates as "x1,y1|x2,y2|..."
        coords = "|".join(
            f"{int(obj.x + obj.width / 2)},{int(obj.y + obj.height / 2)}"
            for obj in objects
        )

        return CaptchaResult(
            solution=coords,
            captcha_type=CaptchaType.GEETEST.value,
            confidence=0.70,
            solver_name=self.name,
            elapsed_ms=0,
            raw={"challenge_type": "click", "objects": len(objects)},
        )

    def _solve_icon(self, solver_input: SolverInput) -> CaptchaResult:
        """Solve GeeTest icon matching challenge."""
        backend = self._get_backend()

        # Use cloud vision to classify the icons
        description = backend.classify_image(
            solver_input.image,
            labels=solver_input.metadata.get("icon_labels"),
        )

        return CaptchaResult(
            solution=description,
            captcha_type=CaptchaType.GEETEST.value,
            confidence=0.65,
            solver_name=self.name,
            elapsed_ms=0,
            raw={"challenge_type": "icon"},
        )

    def _get_backend(self) -> ModelBackend:
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
