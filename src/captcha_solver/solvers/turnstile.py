"""Cloudflare Turnstile solver."""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput

if TYPE_CHECKING:
    from captcha_solver.browser.base import BrowserAdapter


class TurnstileSolver(BaseSolver):
    """Solve Cloudflare Turnstile by interacting with the challenge widget."""

    def __init__(self, stealth: bool = True, timeout: float = 15.0):
        self.stealth = stealth
        self.timeout = timeout

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.TURNSTILE

    @property
    def name(self) -> str:
        return "TurnstileSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.metadata.get("browser") is not None

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        start = time.perf_counter()

        browser: BrowserAdapter | None = solver_input.metadata.get("browser")

        if browser is None:
            return CaptchaResult(
                solution="",
                captcha_type=CaptchaType.TURNSTILE.value,
                confidence=0.0,
                solver_name=self.name,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                raw={"error": "Browser adapter required for Turnstile"},
            )

        # Step 1: Apply stealth patches
        if self.stealth:
            from captcha_solver.browser.stealth import apply_stealth

            apply_stealth(browser)

        # Step 2: Find and interact with Turnstile widget
        token = self._solve_turnstile(browser)
        elapsed = (time.perf_counter() - start) * 1000

        confidence = 0.85 if token else 0.0

        return CaptchaResult(
            solution=token or "",
            captcha_type=CaptchaType.TURNSTILE.value,
            confidence=confidence,
            solver_name=self.name,
            elapsed_ms=elapsed,
        )

    def _solve_turnstile(self, browser: BrowserAdapter) -> str | None:
        """Attempt to solve Turnstile challenge."""
        import time as _time

        # Try to find the Turnstile iframe
        try:
            iframe = browser.find_element("iframe[src*='challenges.cloudflare.com']")
            if iframe is None:
                # Try alternate selector
                iframe = browser.find_element("div.cf-turnstile iframe")

            if iframe:
                browser.switch_to_iframe(iframe)

                # Look for the checkbox/challenge element and click it
                try:
                    checkbox = browser.wait_for_selector(
                        "input[type='checkbox'], .ctp-checkbox-label, #challenge-stage",
                        timeout=5.0,
                    )
                    if checkbox:
                        _time.sleep(0.5)  # Brief human-like delay
                        browser.click_element(checkbox)
                except Exception:
                    pass

                browser.switch_to_default()
        except Exception:
            pass

        # Wait for token to appear
        deadline = _time.time() + self.timeout
        while _time.time() < deadline:
            try:
                # Check for cf-turnstile-response
                token = browser.execute_js(
                    """
                    var el = document.querySelector('[name="cf-turnstile-response"]');
                    if (el && el.value) return el.value;
                    var el2 = document.querySelector('input[name="cf-turnstile-response"]');
                    if (el2 && el2.value) return el2.value;
                    return '';
                    """
                )
                if token:
                    return token
            except Exception:
                pass
            _time.sleep(0.5)

        return None
