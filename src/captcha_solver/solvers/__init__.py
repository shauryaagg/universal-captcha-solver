"""Captcha solver implementations."""
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput
from captcha_solver.solvers.hcaptcha import HCaptchaSolver
from captcha_solver.solvers.math_solver import MathSolver
from captcha_solver.solvers.recaptcha_v2 import RecaptchaV2Solver
from captcha_solver.solvers.slider import SliderSolver
from captcha_solver.solvers.text import TextSolver
from captcha_solver.solvers.turnstile import TurnstileSolver

__all__ = [
    "BaseSolver",
    "CaptchaType",
    "HCaptchaSolver",
    "MathSolver",
    "RecaptchaV2Solver",
    "SliderSolver",
    "SolverInput",
    "TextSolver",
    "TurnstileSolver",
]


def get_default_solvers() -> list[BaseSolver]:
    """Return instances of all built-in solvers."""
    return [
        TextSolver(),
        MathSolver(),
        SliderSolver(),
        RecaptchaV2Solver(),
        HCaptchaSolver(),
        TurnstileSolver(),
    ]
