"""Integration test: Full end-to-end flow using solve_captcha()."""
from __future__ import annotations

import os

from tests.integration.conftest import requires_api_key, requires_playwright


@requires_api_key
@requires_playwright
class TestFullFlow:
    """Test the complete solve_captcha() flow on live pages."""

    def test_solve_captcha_on_normal_demo(self, page, cloud_provider, api_key):
        """Use solve_captcha(page) on the normal captcha demo."""
        os.environ["CAPTCHA_SOLVER_MODEL_BACKEND"] = "cloud"
        os.environ["CAPTCHA_SOLVER_CLOUD_PROVIDER"] = cloud_provider
        if cloud_provider == "anthropic":
            os.environ["CAPTCHA_SOLVER_ANTHROPIC_API_KEY"] = api_key
        else:
            os.environ["CAPTCHA_SOLVER_OPENAI_API_KEY"] = api_key

        import captcha_solver.core.pipeline as pipeline_mod

        try:
            # Reset the default pipeline so it picks up new settings
            pipeline_mod._default_pipeline = None

            page.goto("https://2captcha.com/demo/normal", wait_until="networkidle")
            page.wait_for_timeout(2000)

            from captcha_solver.browser import solve_captcha

            result = solve_captcha(page, captcha_type="text")

            print(
                f"Full flow result: solution='{result.solution}', "
                f"type={result.captcha_type}, confidence={result.confidence:.2f}"
            )
            assert result.solution, "Expected a solution"
            assert result.captcha_type == "text"
        finally:
            pipeline_mod._default_pipeline = None
            for key in [
                "CAPTCHA_SOLVER_MODEL_BACKEND",
                "CAPTCHA_SOLVER_CLOUD_PROVIDER",
                "CAPTCHA_SOLVER_ANTHROPIC_API_KEY",
                "CAPTCHA_SOLVER_OPENAI_API_KEY",
            ]:
                os.environ.pop(key, None)
