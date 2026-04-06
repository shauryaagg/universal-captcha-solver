"""Integration test: Slider-like captchas."""
from __future__ import annotations

import io

from tests.integration.conftest import requires_playwright


@requires_playwright
class TestSliderCaptcha:
    """Test slider captcha detection and solving."""

    def test_solve_slider_from_screenshot(self, page):
        """Take a screenshot of a slider-like captcha and try to find the gap."""
        from PIL import Image, ImageDraw

        from captcha_solver.solvers.base import SolverInput
        from captcha_solver.solvers.slider import SliderSolver

        # Create a synthetic slider image for testing
        # (2captcha doesn't have a simple slider demo)
        img = Image.new("RGB", (400, 100), color=(200, 200, 200))
        draw = ImageDraw.Draw(img)
        draw.rectangle([250, 10, 290, 90], fill=(50, 50, 50), outline=(0, 0, 0), width=3)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        solver = SliderSolver()
        result = solver.solve(SolverInput(image=image_bytes))

        print(f"Slider offset: {result.solution}px, confidence: {result.confidence}")
        offset = int(result.solution)
        assert 200 < offset < 320, f"Expected offset near 270, got {offset}"
