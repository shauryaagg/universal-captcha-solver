"""Tests for captcha_solver.solvers.recaptcha_v3.RecaptchaV3Solver."""

from unittest.mock import MagicMock

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType, SolverInput
from captcha_solver.solvers.recaptcha_v3 import RecaptchaV3Solver


class TestRecaptchaV3Solver:
    def test_captcha_type(self):
        solver = RecaptchaV3Solver()
        assert solver.captcha_type == CaptchaType.RECAPTCHA_V3

    def test_name(self):
        solver = RecaptchaV3Solver()
        assert solver.name == "RecaptchaV3Solver"

    def test_can_solve_with_site_key(self):
        solver = RecaptchaV3Solver()
        inp = SolverInput(site_key="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")
        assert solver.can_solve(inp) is True

    def test_can_solve_without_site_key_or_browser(self):
        solver = RecaptchaV3Solver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_can_solve_with_browser_in_metadata(self):
        solver = RecaptchaV3Solver()
        mock_browser = MagicMock()
        inp = SolverInput(metadata={"browser": mock_browser})
        assert solver.can_solve(inp) is True

    def test_solve_without_browser_returns_empty(self):
        solver = RecaptchaV3Solver()
        inp = SolverInput(site_key="test-key")
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == ""
        assert result.captcha_type == "recaptcha_v3"
        assert result.confidence == 0.0
        assert result.solver_name == "RecaptchaV3Solver"
        assert result.elapsed_ms >= 0
        assert result.raw["error"] == "Browser adapter required for reCAPTCHA v3"

    def test_solve_with_mock_browser_returns_token(self):
        mock_browser = MagicMock()
        fake_token = "03AGdBq24PBCbwiDRaS_MJ7Z..."
        mock_browser.execute_js.return_value = fake_token

        solver = RecaptchaV3Solver(simulation_duration=0.0)
        inp = SolverInput(
            site_key="test-site-key",
            metadata={"browser": mock_browser, "action": "login"},
        )
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == fake_token
        assert result.captcha_type == "recaptcha_v3"
        assert result.confidence == 0.7
        assert result.solver_name == "RecaptchaV3Solver"
        assert result.elapsed_ms > 0
        assert result.raw["site_key"] == "test-site-key"
        assert result.raw["action"] == "login"

    def test_solve_with_browser_exception_returns_empty(self):
        mock_browser = MagicMock()
        # Only the grecaptcha.execute call (which uses a Promise) should fail.
        # Behavior simulation calls use simpler JS; we make execute_js raise
        # only when the script contains "grecaptcha".
        original_return = None

        def _selective_error(script, *args):
            if "grecaptcha" in script:
                raise RuntimeError("grecaptcha not loaded")
            return original_return

        mock_browser.execute_js.side_effect = _selective_error

        solver = RecaptchaV3Solver(simulation_duration=0.0)
        inp = SolverInput(
            site_key="test-site-key",
            metadata={"browser": mock_browser},
        )
        result = solver.solve(inp)

        assert result.solution == ""
        assert result.confidence == 0.0

    def test_solve_default_action_is_submit(self):
        mock_browser = MagicMock()
        mock_browser.execute_js.return_value = "token123"

        solver = RecaptchaV3Solver(simulation_duration=0.0)
        inp = SolverInput(
            site_key="test-key",
            metadata={"browser": mock_browser},
        )
        result = solver.solve(inp)

        assert result.raw["action"] == "submit"
