"""Solver registry with priority-based lookup."""
from __future__ import annotations

from captcha_solver.solvers.base import BaseSolver, CaptchaType


class SolverRegistry:
    def __init__(self) -> None:
        self._solvers: dict[CaptchaType, list[tuple[int, BaseSolver]]] = {}

    def register(self, solver: BaseSolver, priority: int = 0) -> None:
        ct = solver.captcha_type
        if ct not in self._solvers:
            self._solvers[ct] = []
        self._solvers[ct].append((priority, solver))
        self._solvers[ct].sort(key=lambda x: x[0], reverse=True)

    def get_solver(self, captcha_type: CaptchaType) -> BaseSolver:
        solvers = self._solvers.get(captcha_type)
        if not solvers:
            raise ValueError(f"No solver registered for {captcha_type}")
        return solvers[0][1]

    def get_all_solvers(self, captcha_type: CaptchaType) -> list[BaseSolver]:
        return [s for _, s in self._solvers.get(captcha_type, [])]

    def list_types(self) -> list[CaptchaType]:
        return list(self._solvers.keys())

    def discover_plugins(self) -> None:
        pass
