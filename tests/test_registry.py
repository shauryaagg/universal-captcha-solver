"""Tests for captcha_solver.core.registry.SolverRegistry."""

import pytest

from captcha_solver.core.registry import SolverRegistry
from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput


class _DummySolver(BaseSolver):
    """Concrete solver for testing the registry."""

    def __init__(self, ctype: CaptchaType = CaptchaType.TEXT, solver_name: str = "DummySolver"):
        self._ctype = ctype
        self._name = solver_name

    @property
    def captcha_type(self) -> CaptchaType:
        return self._ctype

    @property
    def name(self) -> str:
        return self._name

    def can_solve(self, solver_input: SolverInput) -> bool:
        return True

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        return CaptchaResult(
            solution="dummy",
            captcha_type=self._ctype.value,
            confidence=1.0,
            solver_name=self._name,
            elapsed_ms=0.0,
        )


class TestSolverRegistry:
    def test_register_and_get_solver(self):
        registry = SolverRegistry()
        solver = _DummySolver()
        registry.register(solver)
        retrieved = registry.get_solver(CaptchaType.TEXT)
        assert retrieved is solver

    def test_priority_ordering(self):
        registry = SolverRegistry()
        low = _DummySolver(solver_name="LowPriority")
        high = _DummySolver(solver_name="HighPriority")

        registry.register(low, priority=1)
        registry.register(high, priority=10)

        retrieved = registry.get_solver(CaptchaType.TEXT)
        assert retrieved.name == "HighPriority"

    def test_get_all_solvers(self):
        registry = SolverRegistry()
        s1 = _DummySolver(solver_name="S1")
        s2 = _DummySolver(solver_name="S2")

        registry.register(s1, priority=5)
        registry.register(s2, priority=10)

        all_solvers = registry.get_all_solvers(CaptchaType.TEXT)
        assert len(all_solvers) == 2
        # Higher priority first
        assert all_solvers[0].name == "S2"
        assert all_solvers[1].name == "S1"

    def test_list_types(self):
        registry = SolverRegistry()
        registry.register(_DummySolver(CaptchaType.TEXT))
        registry.register(_DummySolver(CaptchaType.SLIDER))

        types = registry.list_types()
        assert CaptchaType.TEXT in types
        assert CaptchaType.SLIDER in types

    def test_get_solver_raises_for_unknown_type(self):
        registry = SolverRegistry()
        with pytest.raises(ValueError, match="No solver registered"):
            registry.get_solver(CaptchaType.AUDIO)

    def test_get_all_solvers_returns_empty_for_unknown(self):
        registry = SolverRegistry()
        assert registry.get_all_solvers(CaptchaType.HCAPTCHA) == []

    def test_multiple_types(self):
        registry = SolverRegistry()
        text_solver = _DummySolver(CaptchaType.TEXT, "TextDummy")
        math_solver = _DummySolver(CaptchaType.MATH, "MathDummy")

        registry.register(text_solver)
        registry.register(math_solver)

        assert registry.get_solver(CaptchaType.TEXT).name == "TextDummy"
        assert registry.get_solver(CaptchaType.MATH).name == "MathDummy"
