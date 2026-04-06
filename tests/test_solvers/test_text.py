"""Tests for captcha_solver.solvers.text.TextSolver."""

from unittest.mock import MagicMock

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType, SolverInput
from captcha_solver.solvers.text import TextSolver


class TestTextSolver:
    def test_can_solve_with_image(self, sample_text_image: bytes):
        solver = TextSolver()
        inp = SolverInput(image=sample_text_image)
        assert solver.can_solve(inp) is True

    def test_can_solve_without_image(self):
        solver = TextSolver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_captcha_type(self):
        solver = TextSolver()
        assert solver.captcha_type == CaptchaType.TEXT

    def test_name(self):
        solver = TextSolver()
        assert solver.name == "TextSolver"

    def test_preprocess_modifies_image(self, sample_text_image: bytes):
        solver = TextSolver()
        inp = SolverInput(image=sample_text_image)
        processed = solver.preprocess(inp)
        # The preprocessed image should be different (grayscale + denoise + threshold)
        assert processed.image is not None
        assert processed.image != sample_text_image

    def test_preprocess_no_image(self):
        solver = TextSolver()
        inp = SolverInput()
        processed = solver.preprocess(inp)
        assert processed.image is None

    def test_solve_with_mock_backend(self, sample_text_image: bytes):
        """Mock the OCR backend to avoid needing real ONNX model."""
        mock_backend = MagicMock()
        mock_backend.ocr.return_value = "abc123"

        solver = TextSolver(backend=mock_backend)
        inp = SolverInput(image=sample_text_image)
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == "abc123"
        assert result.captcha_type == "text"
        assert result.confidence == 0.85
        assert result.solver_name == "TextSolver"
        assert result.elapsed_ms > 0
        mock_backend.ocr.assert_called_once_with(sample_text_image)

    def test_solve_requires_image(self):
        mock_backend = MagicMock()
        solver = TextSolver(backend=mock_backend)
        inp = SolverInput()

        import pytest

        with pytest.raises(ValueError, match="requires an image"):
            solver.solve(inp)
