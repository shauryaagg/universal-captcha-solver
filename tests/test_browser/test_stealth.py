"""Tests for captcha_solver.browser.stealth module."""
from __future__ import annotations

from unittest.mock import MagicMock

from captcha_solver.browser.stealth import (
    STEALTH_SCRIPTS,
    apply_stealth,
    patch_webdriver,
)


class TestApplyStealth:
    def test_calls_execute_js_for_each_script(self) -> None:
        adapter = MagicMock()
        apply_stealth(adapter)

        assert adapter.execute_js.call_count == len(STEALTH_SCRIPTS)
        for script in STEALTH_SCRIPTS:
            adapter.execute_js.assert_any_call(script)

    def test_continues_on_execute_js_failure(self) -> None:
        adapter = MagicMock()
        adapter.execute_js.side_effect = Exception("script error")

        # Should not raise
        apply_stealth(adapter)

        # Should still try all scripts
        assert adapter.execute_js.call_count == len(STEALTH_SCRIPTS)

    def test_partial_failure(self) -> None:
        """Some scripts fail, others succeed."""
        adapter = MagicMock()
        call_count = 0

        def side_effect(script: str) -> None:
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:
                raise RuntimeError("even call fails")

        adapter.execute_js.side_effect = side_effect
        apply_stealth(adapter)

        assert adapter.execute_js.call_count == len(STEALTH_SCRIPTS)


class TestPatchWebdriver:
    def test_calls_execute_js(self) -> None:
        adapter = MagicMock()
        patch_webdriver(adapter)

        adapter.execute_js.assert_called_once_with(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

    def test_does_not_crash_on_failure(self) -> None:
        adapter = MagicMock()
        adapter.execute_js.side_effect = Exception("boom")

        # Should not raise
        patch_webdriver(adapter)


class TestStealthScripts:
    def test_scripts_list_not_empty(self) -> None:
        assert len(STEALTH_SCRIPTS) > 0

    def test_all_scripts_are_strings(self) -> None:
        for script in STEALTH_SCRIPTS:
            assert isinstance(script, str)

    def test_webdriver_script_present(self) -> None:
        assert any("webdriver" in s for s in STEALTH_SCRIPTS)

    def test_chrome_runtime_script_present(self) -> None:
        assert any("chrome" in s for s in STEALTH_SCRIPTS)

    def test_plugins_script_present(self) -> None:
        assert any("plugins" in s for s in STEALTH_SCRIPTS)

    def test_languages_script_present(self) -> None:
        assert any("languages" in s for s in STEALTH_SCRIPTS)
