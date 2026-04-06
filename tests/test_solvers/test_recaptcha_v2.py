"""Tests for captcha_solver.solvers.recaptcha_v2.RecaptchaV2Solver."""

from unittest.mock import MagicMock

import pytest

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType, SolverInput
from captcha_solver.solvers.recaptcha_v2 import RecaptchaV2Solver


class TestRecaptchaV2Solver:
    def test_captcha_type(self):
        solver = RecaptchaV2Solver()
        assert solver.captcha_type == CaptchaType.RECAPTCHA_V2

    def test_name(self):
        solver = RecaptchaV2Solver()
        assert solver.name == "RecaptchaV2Solver"

    def test_can_solve_with_image(self, sample_square_image: bytes):
        solver = RecaptchaV2Solver()
        inp = SolverInput(image=sample_square_image)
        assert solver.can_solve(inp) is True

    def test_can_solve_without_image(self):
        solver = RecaptchaV2Solver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_solve_with_mock_backend(self, sample_square_image: bytes):
        mock_backend = MagicMock()
        mock_backend.solve_grid_captcha.return_value = [1, 4, 7]

        solver = RecaptchaV2Solver(backend=mock_backend)
        inp = SolverInput(
            image=sample_square_image,
            metadata={"challenge_prompt": "Select all traffic lights"},
        )
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == "1,4,7"
        assert result.captcha_type == "recaptcha_v2"
        assert result.confidence == 0.80
        assert result.solver_name == "RecaptchaV2Solver"
        assert result.elapsed_ms > 0
        assert result.raw["positions"] == [1, 4, 7]
        assert result.raw["grid_size"] == [3, 3]
        mock_backend.solve_grid_captcha.assert_called_once()

    def test_solve_requires_image(self):
        mock_backend = MagicMock()
        solver = RecaptchaV2Solver(backend=mock_backend)
        inp = SolverInput()

        with pytest.raises(ValueError, match="requires an image"):
            solver.solve(inp)

    def test_solve_with_custom_grid_size(self, sample_square_image: bytes):
        mock_backend = MagicMock()
        mock_backend.solve_grid_captcha.return_value = [2, 8, 15]

        solver = RecaptchaV2Solver(backend=mock_backend)
        inp = SolverInput(
            image=sample_square_image,
            metadata={
                "challenge_prompt": "Select crosswalks",
                "grid_size": (4, 4),
            },
        )
        result = solver.solve(inp)

        assert result.solution == "2,8,15"
        assert result.raw["grid_size"] == [4, 4]
        mock_backend.solve_grid_captcha.assert_called_once_with(
            sample_square_image, "Select crosswalks", (4, 4)
        )

    def test_solve_empty_positions(self, sample_square_image: bytes):
        mock_backend = MagicMock()
        mock_backend.solve_grid_captcha.return_value = []

        solver = RecaptchaV2Solver(backend=mock_backend)
        inp = SolverInput(image=sample_square_image)
        result = solver.solve(inp)

        assert result.solution == ""
        assert result.raw["positions"] == []

    def test_solve_uses_default_prompt(self, sample_square_image: bytes):
        mock_backend = MagicMock()
        mock_backend.solve_grid_captcha.return_value = [5]

        solver = RecaptchaV2Solver(backend=mock_backend)
        inp = SolverInput(image=sample_square_image)
        solver.solve(inp)

        call_args = mock_backend.solve_grid_captcha.call_args
        assert "Select all squares" in call_args[0][1]
