"""Tests for captcha_solver.solvers.turnstile.TurnstileSolver."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType, SolverInput
from captcha_solver.solvers.turnstile import TurnstileSolver


class TestTurnstileSolverProperties:
    def test_captcha_type(self) -> None:
        solver = TurnstileSolver()
        assert solver.captcha_type == CaptchaType.TURNSTILE

    def test_name(self) -> None:
        solver = TurnstileSolver()
        assert solver.name == "TurnstileSolver"

    def test_default_stealth_enabled(self) -> None:
        solver = TurnstileSolver()
        assert solver.stealth is True

    def test_stealth_can_be_disabled(self) -> None:
        solver = TurnstileSolver(stealth=False)
        assert solver.stealth is False

    def test_default_timeout(self) -> None:
        solver = TurnstileSolver()
        assert solver.timeout == 15.0

    def test_custom_timeout(self) -> None:
        solver = TurnstileSolver(timeout=30.0)
        assert solver.timeout == 30.0


class TestTurnstileCanSolve:
    def test_can_solve_with_browser(self) -> None:
        solver = TurnstileSolver()
        browser = MagicMock()
        inp = SolverInput(metadata={"browser": browser})
        assert solver.can_solve(inp) is True

    def test_cannot_solve_without_browser(self) -> None:
        solver = TurnstileSolver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_cannot_solve_with_none_browser(self) -> None:
        solver = TurnstileSolver()
        inp = SolverInput(metadata={"browser": None})
        assert solver.can_solve(inp) is False


class TestTurnstileSolve:
    def test_solve_without_browser_returns_empty(self) -> None:
        solver = TurnstileSolver()
        inp = SolverInput()
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == ""
        assert result.captcha_type == "turnstile"
        assert result.confidence == 0.0
        assert result.solver_name == "TurnstileSolver"
        assert result.elapsed_ms >= 0
        assert result.raw == {"error": "Browser adapter required for Turnstile"}

    def test_solve_with_browser_returns_token(self) -> None:
        browser = MagicMock()
        # find_element returns an iframe
        browser.find_element.return_value = MagicMock()
        browser.wait_for_selector.return_value = MagicMock()
        # execute_js returns the token on first call (from stealth) then token
        browser.execute_js.return_value = "cf-token-abc123"

        solver = TurnstileSolver(stealth=False, timeout=1.0)
        inp = SolverInput(metadata={"browser": browser})
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == "cf-token-abc123"
        assert result.captcha_type == "turnstile"
        assert result.confidence == 0.85
        assert result.solver_name == "TurnstileSolver"
        assert result.elapsed_ms > 0

    def test_solve_no_token_returns_empty(self) -> None:
        browser = MagicMock()
        browser.find_element.return_value = None
        browser.execute_js.return_value = ""

        solver = TurnstileSolver(stealth=False, timeout=0.5)
        inp = SolverInput(metadata={"browser": browser})
        result = solver.solve(inp)

        assert result.solution == ""
        assert result.confidence == 0.0

    def test_solve_applies_stealth_when_enabled(self) -> None:
        browser = MagicMock()
        browser.find_element.return_value = None
        browser.execute_js.return_value = "token-xyz"

        with patch("captcha_solver.browser.stealth.apply_stealth") as mock_stealth:
            solver = TurnstileSolver(stealth=True, timeout=1.0)
            inp = SolverInput(metadata={"browser": browser})
            solver.solve(inp)

            mock_stealth.assert_called_once_with(browser)

    def test_solve_skips_stealth_when_disabled(self) -> None:
        browser = MagicMock()
        browser.find_element.return_value = None
        browser.execute_js.return_value = "token-xyz"

        with patch("captcha_solver.browser.stealth.apply_stealth") as mock_stealth:
            solver = TurnstileSolver(stealth=False, timeout=1.0)
            inp = SolverInput(metadata={"browser": browser})
            solver.solve(inp)

            mock_stealth.assert_not_called()

    def test_solve_clicks_checkbox_in_iframe(self) -> None:
        browser = MagicMock()
        mock_iframe = MagicMock()
        mock_checkbox = MagicMock()

        browser.find_element.return_value = mock_iframe
        browser.wait_for_selector.return_value = mock_checkbox
        # Return token on first execute_js call in the token-polling loop
        browser.execute_js.return_value = "solved-token"

        solver = TurnstileSolver(stealth=False, timeout=1.0)
        inp = SolverInput(metadata={"browser": browser})
        result = solver.solve(inp)

        browser.switch_to_iframe.assert_called_once_with(mock_iframe)
        browser.click_element.assert_called_once_with(mock_checkbox)
        browser.switch_to_default.assert_called_once()
        assert result.solution == "solved-token"

    def test_solve_handles_iframe_exception(self) -> None:
        browser = MagicMock()
        browser.find_element.side_effect = Exception("no iframe")
        browser.execute_js.return_value = ""

        solver = TurnstileSolver(stealth=False, timeout=0.5)
        inp = SolverInput(metadata={"browser": browser})
        result = solver.solve(inp)

        # Should not raise, just return empty
        assert result.solution == ""
        assert result.confidence == 0.0
