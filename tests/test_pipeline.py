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


class _LowConfidenceSolver(BaseSolver):
    """Solver that returns results below confidence threshold."""

    def __init__(
        self,
        ctype: CaptchaType = CaptchaType.TEXT,
        confidence: float = 0.3,
        solver_name: str = "LowConfidence",
    ):
        self._ctype = ctype
        self._confidence = confidence
        self._name = solver_name

    @property
    def captcha_type(self) -> CaptchaType:
        return self._ctype

    @property
    def name(self) -> str:
        return self._name

    def can_solve(self, solver_input: SolverInput) -> bool:
        return True

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        return CaptchaResult(
            solution="low-confidence-answer",
            captcha_type=self._ctype.value,
            confidence=self._confidence,
            solver_name=self.name,
            elapsed_ms=2.0,
        )


class _FailingSolver(BaseSolver):
    """Solver that always raises an exception."""

    def __init__(self, ctype: CaptchaType = CaptchaType.TEXT, solver_name: str = "Failing"):
        self._ctype = ctype
        self._name = solver_name

    @property
    def captcha_type(self) -> CaptchaType:
        return self._ctype

    @property
    def name(self) -> str:
        return self._name

    def can_solve(self, solver_input: SolverInput) -> bool:
        return True

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        raise RuntimeError("Simulated solver failure")


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

    @pytest.mark.asyncio
    async def test_asolve_returns_result(self, sample_text_image: bytes):
        """asolve() should return a CaptchaResult using async path."""
        pipeline = _build_pipeline_with_stubs()
        result = await pipeline.asolve(image=sample_text_image, captcha_type="text")
        assert isinstance(result, CaptchaResult)
        assert result.solution == "stubbed"
        assert result.captcha_type == "text"

    @pytest.mark.asyncio
    async def test_asolve_with_file_path(self, tmp_image_file):
        """asolve() works with file paths too."""
        pipeline = _build_pipeline_with_stubs()
        result = await pipeline.asolve(image=tmp_image_file)
        assert isinstance(result, CaptchaResult)
        assert result.solution == "stubbed"

    @pytest.mark.asyncio
    async def test_asolve_with_explicit_enum_type(self, sample_text_image: bytes):
        """asolve() works with CaptchaType enum."""
        pipeline = _build_pipeline_with_stubs()
        result = await pipeline.asolve(
            image=sample_text_image, captcha_type=CaptchaType.MATH
        )
        assert isinstance(result, CaptchaResult)
        assert result.captcha_type == "math"

    # --- New tests for retry/fallback chains ---

    def test_fallback_to_second_solver(self, sample_text_image: bytes):
        """When the first solver is below threshold, fall back to next registered solver."""
        registry = SolverRegistry()
        # Low-confidence solver registered first (higher priority)
        registry.register(_LowConfidenceSolver(CaptchaType.TEXT, confidence=0.3), priority=10)
        # Good solver registered second (lower priority)
        registry.register(_StubSolver(CaptchaType.TEXT), priority=0)
        pipeline = SolverPipeline(settings=Settings(), registry=registry)
        result = pipeline.solve(image=sample_text_image, captcha_type="text")
        # Should get the stub solver's high-confidence result
        assert result.confidence == 0.99
        assert result.solution == "stubbed"

    def test_best_result_returned_when_all_below_threshold(self, sample_text_image: bytes):
        """When all solvers are below threshold, return the best result."""
        registry = SolverRegistry()
        registry.register(
            _LowConfidenceSolver(CaptchaType.TEXT, confidence=0.3, solver_name="Low1"),
            priority=10,
        )
        registry.register(
            _LowConfidenceSolver(CaptchaType.TEXT, confidence=0.5, solver_name="Low2"),
            priority=0,
        )
        pipeline = SolverPipeline(settings=Settings(min_confidence=0.9), registry=registry)
        result = pipeline.solve(image=sample_text_image, captcha_type="text")
        # Should return the higher confidence result
        assert result.confidence == 0.5
        assert result.solver_name == "Low2"

    def test_exception_in_solver_does_not_crash(self, sample_text_image: bytes):
        """A solver that raises should not crash the pipeline; fallback should work."""
        registry = SolverRegistry()
        registry.register(_FailingSolver(CaptchaType.TEXT, solver_name="Crasher"), priority=10)
        registry.register(_StubSolver(CaptchaType.TEXT), priority=0)
        pipeline = SolverPipeline(settings=Settings(), registry=registry)
        result = pipeline.solve(image=sample_text_image, captcha_type="text")
        assert result.confidence == 0.99
        assert result.solution == "stubbed"

    def test_all_solvers_fail_raises_runtime_error(self, sample_text_image: bytes):
        """If every solver raises, pipeline should raise RuntimeError."""
        registry = SolverRegistry()
        registry.register(_FailingSolver(CaptchaType.TEXT, solver_name="Crasher1"))
        pipeline = SolverPipeline(settings=Settings(), registry=registry)
        with pytest.raises(RuntimeError, match="All solvers failed"):
            pipeline.solve(image=sample_text_image, captcha_type="text")

    def test_fallback_to_cloud_config(self):
        """The fallback_to_cloud setting should exist and default to True."""
        settings = Settings()
        assert settings.fallback_to_cloud is True

    def test_fallback_to_cloud_disabled(self):
        """fallback_to_cloud can be explicitly disabled."""
        settings = Settings(fallback_to_cloud=False)
        assert settings.fallback_to_cloud is False

    def test_no_solver_for_type_raises(self, sample_text_image: bytes):
        """Requesting a type with no registered solver should raise ValueError."""
        registry = SolverRegistry()
        # Only register MATH, then request TEXT
        registry.register(_StubSolver(CaptchaType.MATH))
        pipeline = SolverPipeline(settings=Settings(), registry=registry)
        with pytest.raises(ValueError, match="No solver registered"):
            pipeline.solve(image=sample_text_image, captcha_type="text")
