"""reCAPTCHA v3 solver via browser behavior simulation."""
from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput

if TYPE_CHECKING:
    from captcha_solver.browser.base import BrowserAdapter


class RecaptchaV3Solver(BaseSolver):
    """Solve reCAPTCHA v3 by simulating natural browser behavior to achieve a passing score."""

    def __init__(self, simulation_duration: float = 3.0):
        self.simulation_duration = simulation_duration

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.RECAPTCHA_V3

    @property
    def name(self) -> str:
        return "RecaptchaV3Solver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return (
            solver_input.site_key is not None
            or solver_input.metadata.get("browser") is not None
        )

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        start = time.perf_counter()

        browser: BrowserAdapter | None = solver_input.metadata.get("browser")
        site_key = solver_input.site_key or ""
        action = solver_input.metadata.get("action", "submit")

        if browser is None:
            return CaptchaResult(
                solution="",
                captcha_type=CaptchaType.RECAPTCHA_V3.value,
                confidence=0.0,
                solver_name=self.name,
                elapsed_ms=(time.perf_counter() - start) * 1000,
                raw={"error": "Browser adapter required for reCAPTCHA v3"},
            )

        # Step 1: Simulate human behavior
        from captcha_solver.browser.behavior import (
            simulate_human_delay,
            simulate_reading,
            simulate_scroll,
        )

        simulate_reading(browser, duration=self.simulation_duration)
        simulate_human_delay(200, 600)
        simulate_scroll(browser, amount=random.randint(100, 400))
        simulate_human_delay(100, 300)

        # Step 2: Execute reCAPTCHA v3 and get token
        token = ""
        try:
            token = browser.execute_js(
                """
                return new Promise((resolve, reject) => {
                    if (typeof grecaptcha === 'undefined') {
                        reject('grecaptcha not loaded');
                        return;
                    }
                    grecaptcha.ready(() => {
                        grecaptcha.execute(arguments[0], {action: arguments[1]})
                            .then(token => resolve(token))
                            .catch(err => reject(err.toString()));
                    });
                });
                """,
                site_key,
                action,
            )
        except Exception:
            token = ""

        elapsed = (time.perf_counter() - start) * 1000

        confidence = 0.7 if token else 0.0

        return CaptchaResult(
            solution=token or "",
            captcha_type=CaptchaType.RECAPTCHA_V3.value,
            confidence=confidence,
            solver_name=self.name,
            elapsed_ms=elapsed,
            raw={"site_key": site_key, "action": action},
        )
