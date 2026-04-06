"""Tests for captcha_solver.core.pipeline.SolverPipeline."""

import pytest

from captcha_solver.config import Settings
from captcha_solver.core.pipeline import SolverPipeline
from captcha_solver.core.registry import SolverRegistry
from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput


class _StubSolver(BaseSolver):
    """Solver that always succeeds without needing real backends."""

    def __init__(self, ctype: CaptchaType = CaptchaType.TEXT):
        self._ctype = ctype

    @property
    def captcha_type(self) -> CaptchaType:
        return self._ctype

    @property
    def name(self) -> str:
        return "StubSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return True

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        return CaptchaResult(
            solution="stubbed",
            captcha_type=self._ctype.value,
            confidence=0.99,
            solver_name=self.name,
            elapsed_ms=1.0,
        )


def _build_pipeline_with_stubs() -> SolverPipeline:
    registry = SolverRegistry()
    registry.register(_StubSolver(CaptchaType.TEXT))
    registry.register(_StubSolver(CaptchaType.MATH))
    registry.register(_StubSolver(CaptchaType.SLIDER))
    return SolverPipeline(settings=Settings(), registry=registry)


class TestSolverPipeline:
    def test_creation_with_defaults(self):
        pipeline = SolverPipeline()
        assert pipeline.settings is not None
        assert pipeline.detector is not None
        assert pipeline.registry is not None

    def test_solve_with_file_path(self, tmp_image_file):
        """Solve using a file path."""
        pipeline = _build_pipeline_with_stubs()
        result = pipeline.solve(image=tmp_image_file)
        assert isinstance(result, CaptchaResult)
        assert result.solution == "stubbed"

    def test_solve_with_raw_bytes(self, sample_text_image: bytes):
        """Solve using raw image bytes."""
        pipeline = _build_pipeline_with_stubs()
        result = pipeline.solve(image=sample_text_image)
        assert isinstance(result, CaptchaResult)
        assert result.solution == "stubbed"

    def test_solve_with_explicit_type(self, sample_text_image: bytes):
        """Passing captcha_type skips auto-detection."""
        pipeline = _build_pipeline_with_stubs()
        result = pipeline.solve(image=sample_text_image, captcha_type="text")
        assert result.captcha_type == "text"

    def test_solve_with_enum_type(self, sample_text_image: bytes):
        """Passing CaptchaType enum also works."""
        pipeline = _build_pipeline_with_stubs()
        result = pipeline.solve(image=sample_text_image, captcha_type=CaptchaType.TEXT)
        assert result.captcha_type == "text"

    def test_detect(self, sample_text_image: bytes):
        """detect() returns a tuple of (CaptchaType, confidence)."""
        pipeline = _build_pipeline_with_stubs()
        ctype, confidence = pipeline.detect(sample_text_image)
        assert isinstance(ctype, CaptchaType)
        assert isinstance(confidence, float)

    def test_file_not_found(self):
        pipeline = _build_pipeline_with_stubs()
        with pytest.raises(FileNotFoundError):
            pipeline.solve(image="/nonexistent/captcha.png")

    def test_invalid_type_raises(self, sample_text_image: bytes):
        pipeline = _build_pipeline_with_stubs()
        with pytest.raises(ValueError):
            pipeline.solve(image=sample_text_image, captcha_type="nonexistent_type")

    def test_unsupported_image_type(self):
        pipeline = _build_pipeline_with_stubs()
        with pytest.raises(TypeError, match="Unsupported image type"):
            pipeline.solve(image=12345)
