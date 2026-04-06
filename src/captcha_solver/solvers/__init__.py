"""Captcha solver implementations."""
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput
from captcha_solver.solvers.math_solver import MathSolver
from captcha_solver.solvers.slider import SliderSolver
from captcha_solver.solvers.text import TextSolver

__all__ = [
    "BaseSolver",
    "CaptchaType",
    "MathSolver",
    "SliderSolver",
    "SolverInput",
    "TextSolver",
]


def get_default_solvers() -> list[BaseSolver]:
    """Return instances of all built-in solvers."""
    return [TextSolver(), MathSolver(), SliderSolver()]
