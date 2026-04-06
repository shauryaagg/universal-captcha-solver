"""Tests for captcha_solver.solvers.geetest.GeeTestSolver."""

from unittest.mock import MagicMock

import pytest

from captcha_solver.core.result import CaptchaResult
from captcha_solver.models.backend import BoundingBox
from captcha_solver.solvers.base import CaptchaType, SolverInput
from captcha_solver.solvers.geetest import GeeTestSolver


class TestGeeTestSolver:
    def test_captcha_type(self):
        solver = GeeTestSolver()
        assert solver.captcha_type == CaptchaType.GEETEST

    def test_name(self):
        solver = GeeTestSolver()
        assert solver.name == "GeeTestSolver"

    def test_can_solve_with_image(self, sample_slider_image: bytes):
        solver = GeeTestSolver()
        inp = SolverInput(image=sample_slider_image)
        assert solver.can_solve(inp) is True

    def test_can_solve_without_image(self):
        solver = GeeTestSolver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_solve_requires_image(self):
        solver = GeeTestSolver()
        inp = SolverInput()
        with pytest.raises(ValueError, match="requires an image"):
            solver.solve(inp)

    def test_solve_slide_default(self, sample_slider_image: bytes):
        """Default challenge type is slide; uses SliderSolver internally."""
        solver = GeeTestSolver()
        inp = SolverInput(image=sample_slider_image)
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.captcha_type == "geetest"
        assert result.solver_name == "GeeTestSolver"
        # Solution should be a parseable integer offset
        offset = int(result.solution)
        assert offset >= 0
        assert result.raw["challenge_type"] == "slide"

    def test_solve_slide_explicit(self, sample_slider_image: bytes):
        """Explicitly set geetest_type to slide."""
        solver = GeeTestSolver()
        inp = SolverInput(
            image=sample_slider_image,
            metadata={"geetest_type": "slide"},
        )
        result = solver.solve(inp)

        assert result.captcha_type == "geetest"
        assert result.raw["challenge_type"] == "slide"

    def test_solve_click_with_objects(self, sample_slider_image: bytes):
        """Click challenge with mock backend returning bounding boxes."""
        mock_backend = MagicMock()
        mock_backend.detect_objects.return_value = [
            BoundingBox(x=10, y=20, width=30, height=40, label="star", confidence=0.9),
            BoundingBox(x=100, y=50, width=20, height=20, label="circle", confidence=0.85),
        ]

        solver = GeeTestSolver(backend=mock_backend)
        inp = SolverInput(
            image=sample_slider_image,
            metadata={"geetest_type": "click"},
        )
        result = solver.solve(inp)

        assert result.captcha_type == "geetest"
        assert result.solver_name == "GeeTestSolver"
        assert result.confidence == 0.70
        assert result.raw["challenge_type"] == "click"
        assert result.raw["objects"] == 2
        # Verify coordinates: center of first box = (10+15, 20+20) = (25, 40)
        # Center of second box = (100+10, 50+10) = (110, 60)
        assert result.solution == "25,40|110,60"

    def test_solve_click_no_objects_fallback(self, sample_slider_image: bytes):
        """Click challenge falls back to classify when no objects detected."""
        mock_backend = MagicMock()
        mock_backend.detect_objects.return_value = []
        mock_backend.classify_image.return_value = "a button"

        solver = GeeTestSolver(backend=mock_backend)
        inp = SolverInput(
            image=sample_slider_image,
            metadata={"geetest_type": "click"},
        )
        result = solver.solve(inp)

        assert result.captcha_type == "geetest"
        assert result.confidence == 0.5
        assert result.solution == "a button"
        assert result.raw["challenge_type"] == "click"
        mock_backend.classify_image.assert_called_once()

    def test_solve_icon(self, sample_slider_image: bytes):
        """Icon matching challenge with mock backend."""
        mock_backend = MagicMock()
        mock_backend.classify_image.return_value = "cat"

        solver = GeeTestSolver(backend=mock_backend)
        inp = SolverInput(
            image=sample_slider_image,
            metadata={"geetest_type": "icon", "icon_labels": ["cat", "dog", "fish"]},
        )
        result = solver.solve(inp)

        assert result.captcha_type == "geetest"
        assert result.confidence == 0.65
        assert result.solution == "cat"
        assert result.raw["challenge_type"] == "icon"
        mock_backend.classify_image.assert_called_once_with(
            sample_slider_image,
            labels=["cat", "dog", "fish"],
        )

    def test_metadata_geetest_type_routing(self, sample_slider_image: bytes):
        """Verify that geetest_type metadata routes to the correct handler."""
        mock_backend = MagicMock()
        mock_backend.detect_objects.return_value = []
        mock_backend.classify_image.return_value = "test"

        solver = GeeTestSolver(backend=mock_backend)

        # click type
        inp_click = SolverInput(
            image=sample_slider_image,
            metadata={"geetest_type": "click"},
        )
        result_click = solver.solve(inp_click)
        assert result_click.raw["challenge_type"] == "click"

        # icon type
        inp_icon = SolverInput(
            image=sample_slider_image,
            metadata={"geetest_type": "icon"},
        )
        result_icon = solver.solve(inp_icon)
        assert result_icon.raw["challenge_type"] == "icon"

    def test_unknown_geetest_type_defaults_to_slide(self, sample_slider_image: bytes):
        """Unknown geetest_type should default to slide."""
        solver = GeeTestSolver()
        inp = SolverInput(
            image=sample_slider_image,
            metadata={"geetest_type": "unknown_type"},
        )
        result = solver.solve(inp)
        assert result.raw["challenge_type"] == "slide"
