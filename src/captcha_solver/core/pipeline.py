"""Main solving pipeline: detect -> preprocess -> solve -> return."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from captcha_solver.config import Settings
from captcha_solver.core.detector import CaptchaDetector
from captcha_solver.core.registry import SolverRegistry
from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType, SolverInput

logger = logging.getLogger(__name__)


class SolverPipeline:
    def __init__(
        self,
        settings: Settings | None = None,
        registry: SolverRegistry | None = None,
        detector: CaptchaDetector | None = None,
    ):
        self.settings = settings or Settings()
        self.detector = detector or CaptchaDetector()
        self.registry = registry or self._build_default_registry()

    def _build_default_registry(self) -> SolverRegistry:
        from captcha_solver.solvers import get_default_solvers

        registry = SolverRegistry()
        for solver in get_default_solvers():
            registry.register(solver)
        return registry

    def solve(
        self,
        image: bytes | str | Path | None = None,
        captcha_type: CaptchaType | str | None = None,
        **kwargs: Any,
    ) -> CaptchaResult:
        """Solve a captcha.

        Args:
            image: Image bytes, file path, or Path object
            captcha_type: Optional type hint (skip auto-detection)
            **kwargs: Additional fields for SolverInput
        """
        # Build input
        solver_input = self._build_input(image, **kwargs)

        # Resolve captcha type
        resolved_type = self._resolve_type(captcha_type, solver_input)

        # Get solver
        solver = self.registry.get_solver(resolved_type)
        logger.debug("Using solver: %s for type: %s", solver.name, resolved_type)

        # Preprocess
        solver_input = solver.preprocess(solver_input)

        # Solve with retry
        best_result: CaptchaResult | None = None
        attempts = self.settings.max_retries + 1

        for attempt in range(attempts):
            result = solver.solve(solver_input)
            logger.debug("Attempt %d: confidence=%.2f", attempt + 1, result.confidence)

            if best_result is None or result.confidence > best_result.confidence:
                best_result = result

            if result.confidence >= self.settings.min_confidence:
                return result

            # Try next solver in list if available
            all_solvers = self.registry.get_all_solvers(resolved_type)
            if attempt + 1 < len(all_solvers):
                solver = all_solvers[attempt + 1]
                solver_input = solver.preprocess(solver_input)

        return best_result  # type: ignore[return-value]

    async def asolve(
        self,
        image: bytes | str | Path | None = None,
        captcha_type: CaptchaType | str | None = None,
        **kwargs: Any,
    ) -> CaptchaResult:
        """Async version of solve."""
        solver_input = self._build_input(image, **kwargs)
        resolved_type = self._resolve_type(captcha_type, solver_input)
        solver = self.registry.get_solver(resolved_type)
        solver_input = solver.preprocess(solver_input)
        return await solver.asolve(solver_input)

    def detect(self, image: bytes | str | Path) -> tuple[CaptchaType, float]:
        """Detect captcha type from image."""
        solver_input = self._build_input(image)
        return self.detector.detect_with_confidence(solver_input)

    def _build_input(self, image: bytes | str | Path | None = None, **kwargs: Any) -> SolverInput:
        image_bytes: bytes | None = None

        if isinstance(image, (str, Path)):
            path = Path(image)
            if not path.exists():
                raise FileNotFoundError(f"Image not found: {path}")
            image_bytes = path.read_bytes()
        elif isinstance(image, bytes):
            image_bytes = image
        elif image is not None:
            raise TypeError(f"Unsupported image type: {type(image)}")

        return SolverInput(
            image=image_bytes,
            page_url=kwargs.get("page_url"),
            site_key=kwargs.get("site_key"),
            metadata=kwargs.get("metadata", {}),
        )

    def _resolve_type(
        self, captcha_type: CaptchaType | str | None, solver_input: SolverInput
    ) -> CaptchaType:
        if captcha_type is not None:
            if isinstance(captcha_type, str):
                return CaptchaType(captcha_type)
            return captcha_type
        return self.detector.detect(solver_input)


# Singleton pipeline
_default_pipeline: SolverPipeline | None = None


def get_default_pipeline() -> SolverPipeline:
    global _default_pipeline  # noqa: PLW0603
    if _default_pipeline is None:
        _default_pipeline = SolverPipeline()
    return _default_pipeline
