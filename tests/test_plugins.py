"""Tests for plugin discovery via entry_points."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from captcha_solver.core.registry import SolverRegistry
from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import BaseSolver, CaptchaType, SolverInput


class _ValidPluginSolver(BaseSolver):
    """A valid solver that could be loaded as a plugin."""

    @property
    def captcha_type(self) -> CaptchaType:
        return CaptchaType.AUDIO

    @property
    def name(self) -> str:
        return "ValidPlugin"

    def can_solve(self, solver_input: SolverInput) -> bool:
        return True

    def solve(self, solver_input: SolverInput) -> CaptchaResult:
        return CaptchaResult(
            solution="plugin_result",
            captcha_type=self.captcha_type.value,
            confidence=0.95,
            solver_name=self.name,
            elapsed_ms=1.0,
        )


class _NotASolver:
    """Something that is NOT a BaseSolver subclass."""

    pass


class TestDiscoverPlugins:
    def test_valid_plugin_is_registered(self):
        """A properly implemented solver plugin gets registered."""
        mock_ep = MagicMock()
        mock_ep.name = "valid_plugin"
        mock_ep.load.return_value = _ValidPluginSolver

        with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
            registry = SolverRegistry()
            registry.discover_plugins()

        solver = registry.get_solver(CaptchaType.AUDIO)
        assert solver.name == "ValidPlugin"

    def test_non_solver_plugin_is_skipped(self):
        """A plugin that doesn't subclass BaseSolver is silently skipped."""
        mock_ep = MagicMock()
        mock_ep.name = "bad_class"
        mock_ep.load.return_value = _NotASolver

        with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
            registry = SolverRegistry()
            registry.discover_plugins()

        assert registry.list_types() == []

    def test_failing_plugin_does_not_crash(self):
        """If ep.load() raises, the registry logs a warning and continues."""
        mock_ep = MagicMock()
        mock_ep.name = "broken_plugin"
        mock_ep.load.side_effect = ImportError("missing dep")

        with patch("importlib.metadata.entry_points", return_value=[mock_ep]):
            registry = SolverRegistry()
            # Should not raise
            registry.discover_plugins()

        assert registry.list_types() == []

    def test_multiple_plugins_mixed(self):
        """Mix of good and bad plugins: good ones register, bad ones don't crash."""
        good_ep = MagicMock()
        good_ep.name = "good"
        good_ep.load.return_value = _ValidPluginSolver

        bad_ep = MagicMock()
        bad_ep.name = "bad"
        bad_ep.load.side_effect = RuntimeError("boom")

        with patch("importlib.metadata.entry_points", return_value=[good_ep, bad_ep]):
            registry = SolverRegistry()
            registry.discover_plugins()

        assert CaptchaType.AUDIO in registry.list_types()
        assert len(registry.get_all_solvers(CaptchaType.AUDIO)) == 1

    def test_no_plugins_available(self):
        """When no entry_points exist, discover_plugins is a no-op."""
        with patch("importlib.metadata.entry_points", return_value=[]):
            registry = SolverRegistry()
            registry.discover_plugins()

        assert registry.list_types() == []

    def test_python39_compat_fallback(self):
        """Handles TypeError from entry_points(group=...) for Python 3.9 compat."""
        mock_ep = MagicMock()
        mock_ep.name = "compat_plugin"
        mock_ep.load.return_value = _ValidPluginSolver

        def fake_entry_points(**kwargs):
            if kwargs:
                raise TypeError("unexpected keyword argument 'group'")
            return {"captcha_solver.solvers": [mock_ep]}

        with patch("importlib.metadata.entry_points", side_effect=fake_entry_points):
            registry = SolverRegistry()
            registry.discover_plugins()

        assert CaptchaType.AUDIO in registry.list_types()
