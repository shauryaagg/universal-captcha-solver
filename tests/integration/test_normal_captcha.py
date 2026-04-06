"""Integration test: Normal text captcha on 2captcha.com/demo/normal."""
from __future__ import annotations

from tests.integration.conftest import requires_api_key, requires_playwright


@requires_api_key
@requires_playwright
class TestNormalCaptcha:
    """Test solving normal text captchas from 2captcha demo page."""

    def test_solve_normal_captcha_from_screenshot(self, page, cloud_provider, api_key):
        """Screenshot the captcha image and solve it with cloud OCR."""
        from captcha_solver.models.cloud_backend import CloudBackend

        page.goto("https://2captcha.com/demo/normal", wait_until="networkidle")
        page.wait_for_timeout(2000)

        # Find the captcha image
        captcha_img = (
            page.query_selector("img[src*='captcha']")
            or page.query_selector(".captcha-image img")
            or page.query_selector("img.captcha")
        )

        # If no direct img found, look for any img in the captcha area
        if not captcha_img:
            captcha_img = page.query_selector("div.captcha img") or page.query_selector("main img")

        if not captcha_img:
            # Take full page screenshot and try to solve
            screenshot = page.screenshot()
        else:
            screenshot = captcha_img.screenshot()

        # Solve using cloud backend directly
        backend = CloudBackend(provider=cloud_provider, api_key=api_key)
        solution = backend.ocr(screenshot)

        print(f"Normal captcha solution: '{solution}'")
        assert solution, "Expected non-empty solution"
        assert len(solution) > 0

    def test_solve_normal_captcha_via_pipeline(self, page, cloud_provider, api_key):
        """Solve using the full pipeline with cloud backend."""
        import os

        os.environ["CAPTCHA_SOLVER_MODEL_BACKEND"] = "cloud"
        os.environ["CAPTCHA_SOLVER_CLOUD_PROVIDER"] = cloud_provider
        if cloud_provider == "anthropic":
            os.environ["CAPTCHA_SOLVER_ANTHROPIC_API_KEY"] = api_key
        else:
            os.environ["CAPTCHA_SOLVER_OPENAI_API_KEY"] = api_key

        try:
            from captcha_solver.config import Settings
            from captcha_solver.core.pipeline import SolverPipeline

            page.goto("https://2captcha.com/demo/normal", wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Screenshot the captcha area
            captcha_img = page.query_selector("img[src*='captcha']") or page.query_selector(
                "main img"
            )
            if captcha_img:
                screenshot = captcha_img.screenshot()
            else:
                screenshot = page.screenshot()

            settings = Settings()
            pipeline = SolverPipeline(settings=settings)
            result = pipeline.solve(image=screenshot, captcha_type="text")

            print(f"Pipeline result: solution='{result.solution}', confidence={result.confidence}")
            assert result.solution, "Expected non-empty solution"
        finally:
            for key in [
                "CAPTCHA_SOLVER_MODEL_BACKEND",
                "CAPTCHA_SOLVER_CLOUD_PROVIDER",
                "CAPTCHA_SOLVER_ANTHROPIC_API_KEY",
                "CAPTCHA_SOLVER_OPENAI_API_KEY",
            ]:
                os.environ.pop(key, None)
