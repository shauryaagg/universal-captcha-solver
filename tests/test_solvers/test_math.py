"""Tests for captcha_solver.solvers.math_solver.MathSolver and parse_math_expression."""

from unittest.mock import MagicMock

import pytest

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType, SolverInput
from captcha_solver.solvers.math_solver import MathSolver, parse_math_expression


class TestParseMathExpression:
    def test_addition(self):
        assert parse_math_expression("3 + 7") == "10"

    def test_multiplication_unicode(self):
        assert parse_math_expression("12 \u00d7 4") == "48"

    def test_subtraction(self):
        assert parse_math_expression("15 - 8") == "7"

    def test_division(self):
        assert parse_math_expression("20 / 4") == "5"

    def test_what_is_prefix(self):
        assert parse_math_expression("What is 3+4?") == "7"

    def test_multiplication_x(self):
        assert parse_math_expression("100 x 3") == "300"

    def test_multiplication_star(self):
        assert parse_math_expression("6 * 7") == "42"

    def test_invalid_returns_none(self):
        assert parse_math_expression("hello world") is None

    def test_empty_returns_none(self):
        assert parse_math_expression("") is None

    def test_no_operator(self):
        assert parse_math_expression("42") is None

    def test_division_by_zero(self):
        assert parse_math_expression("10 / 0") == "0"

    def test_decimal_result(self):
        result = parse_math_expression("7 / 2")
        assert result == "3.5"

    def test_whitespace_variations(self):
        assert parse_math_expression("  3  +  7  ") == "10"


class TestMathSolver:
    def test_captcha_type(self):
        solver = MathSolver()
        assert solver.captcha_type == CaptchaType.MATH

    def test_name(self):
        solver = MathSolver()
        assert solver.name == "MathSolver"

    def test_can_solve_with_image(self, sample_math_image: bytes):
        solver = MathSolver()
        inp = SolverInput(image=sample_math_image)
        assert solver.can_solve(inp) is True

    def test_can_solve_without_image(self):
        solver = MathSolver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_solve_with_mock_backend(self, sample_math_image: bytes):
        mock_backend = MagicMock()
        mock_backend.ocr.return_value = "3 + 7"

        solver = MathSolver(backend=mock_backend)
        inp = SolverInput(image=sample_math_image)
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == "10"
        assert result.captcha_type == "math"
        assert result.confidence == 0.95
        assert result.solver_name == "MathSolver"
        mock_backend.ocr.assert_called_once()

    def test_solve_unparseable(self, sample_math_image: bytes):
        mock_backend = MagicMock()
        mock_backend.ocr.return_value = "garbage text"

        solver = MathSolver(backend=mock_backend)
        inp = SolverInput(image=sample_math_image)
        result = solver.solve(inp)

        assert result.solution == ""
        assert result.confidence == 0.0
        assert result.raw is not None
        assert "error" in result.raw

    def test_solve_requires_image(self):
        mock_backend = MagicMock()
        solver = MathSolver(backend=mock_backend)
        inp = SolverInput()

        with pytest.raises(ValueError, match="requires an image"):
            solver.solve(inp)
