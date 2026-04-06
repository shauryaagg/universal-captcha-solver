"""Tests for captcha_solver.solvers.slider.SliderSolver."""

import pytest

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType, SolverInput
from captcha_solver.solvers.slider import SliderSolver


class TestSliderSolver:
    def test_captcha_type(self):
        solver = SliderSolver()
        assert solver.captcha_type == CaptchaType.SLIDER

    def test_name(self):
        solver = SliderSolver()
        assert solver.name == "SliderSolver"

    def test_can_solve_with_image(self, sample_slider_image: bytes):
        solver = SliderSolver()
        inp = SolverInput(image=sample_slider_image)
        assert solver.can_solve(inp) is True

    def test_can_solve_without_image(self):
        solver = SliderSolver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_solve_returns_integer_offset(self, sample_slider_image: bytes):
        solver = SliderSolver()
        inp = SolverInput(image=sample_slider_image)
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.captcha_type == "slider"
        assert result.solver_name == "SliderSolver"
        # Solution should be parseable as an integer
        offset = int(result.solution)
        assert isinstance(offset, int)
        assert offset >= 0

    def test_find_gap_offset_reasonable(self, sample_slider_image: bytes):
        """Gap drawn at x=250-290 should produce offset in a reasonable range."""
        solver = SliderSolver()
        offset = solver._find_gap_offset(sample_slider_image)
        assert isinstance(offset, int)
        # The gap was drawn at x=[250,290], so offset should be near that area
        assert 200 <= offset <= 350

    def test_solve_requires_image(self):
        solver = SliderSolver()
        inp = SolverInput()
        with pytest.raises(ValueError, match="requires an image"):
            solver.solve(inp)

    def test_solve_confidence(self, sample_slider_image: bytes):
        solver = SliderSolver()
        inp = SolverInput(image=sample_slider_image)
        result = solver.solve(inp)
        assert result.confidence == 0.80
