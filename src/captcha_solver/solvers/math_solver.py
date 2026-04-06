"""Math captcha solver: OCR + safe expression evaluation."""
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput

if TYPE_CHECKING:
    from captcha_solver.models.backend import ModelBackend


# Safe math operations
_OPERATORS: dict[str, object] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "\u00d7": lambda a, b: a * b,
    "x": lambda a, b: a * b,
    "/": lambda a, b: a / b if b != 0 else 0,
    "\u00f7": lambda a, b: a / b if b != 0 else 0,
}


def parse_math_expression(text: str) -> str | None:
    """Parse and evaluate a math expression safely. Returns result as string or None."""
    # Clean the text
    text = text.strip().lower()
    text = text.replace("what is", "").replace("?", "").replace("=", "").strip()

    # Try to find pattern: number operator number
    pattern = r"(\d+)\s*([+\-*/\u00d7\u00f7x])\s*(\d+)"
    match = re.search(pattern, text)
    if not match:
        return None

    a = float(match.group(1))
    op = match.group(2)
    b = float(match.group(3))

    func = _OPERATORS.get(op)
    if func is None:
        return None

    result = func(a, b)  # type: ignore[operator]
    # Return as int if whole number
    if result == int(result):
        return str(int(result))
    return str(result)


class MathSolver(BaseSolver):
    def __init__(self, backend: ModelBackend | None = None):
        self._backend = backend

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.MATH

    @property
    def name(self) -> str:
        return "MathSolver"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return solver_input.image is not None

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        if solver_input.image is None:
            raise ValueError("MathSolver requires an image input")

        start = time.perf_counter()

        # OCR the math expression
        backend = self._get_backend()
        text = backend.ocr(solver_input.image)

        # Parse and evaluate
        answer = parse_math_expression(text)
        elapsed = (time.perf_counter() - start) * 1000

        if answer is None:
            return CaptchaResult(
                solution="",
                captcha_type=CaptchaType.MATH.value,
                confidence=0.0,
                solver_name=self.name,
                elapsed_ms=elapsed,
                raw={"ocr_text": text, "error": "Could not parse math expression"},
            )

        return CaptchaResult(
            solution=answer,
            captcha_type=CaptchaType.MATH.value,
            confidence=0.95,
            solver_name=self.name,
            elapsed_ms=elapsed,
            raw={"ocr_text": text},
        )

    def _get_backend(self) -> ModelBackend:
        if self._backend is not None:
            return self._backend
        from captcha_solver.models.onnx_backend import OnnxBackend

        self._backend = OnnxBackend()
        return self._backend
