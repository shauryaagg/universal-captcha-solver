"""Tests for SeleniumAdapter and PlaywrightAdapter."""
from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

# ---------------------------------------------------------------------------
# Provide a fake selenium package so SeleniumAdapter methods can import it.
# ---------------------------------------------------------------------------
_fake_selenium = types.ModuleType("selenium")
_fake_webdriver = types.ModuleType("selenium.webdriver")
_fake_common = types.ModuleType("selenium.webdriver.common")
_fake_by = types.ModuleType("selenium.webdriver.common.by")
_fake_action_chains = types.ModuleType("selenium.webdriver.common.action_chains")
_fake_support = types.ModuleType("selenium.webdriver.support")
_fake_ui = types.ModuleType("selenium.webdriver.support.ui")
_fake_ec = types.ModuleType("selenium.webdriver.support.expected_conditions")

# Create a simple By class with CSS_SELECTOR
_ByMock = type("By", (), {"CSS_SELECTOR": "css selector"})
_fake_by.By = _ByMock  # type: ignore[attr-defined]

# ActionChains mock
_fake_action_chains.ActionChains = MagicMock  # type: ignore[attr-defined]

# WebDriverWait and EC mocks
_fake_ui.WebDriverWait = MagicMock  # type: ignore[attr-defined]
_fake_ec.presence_of_element_located = MagicMock(return_value="locator")  # type: ignore[attr-defined]

# Wire up submodules
_fake_selenium.webdriver = _fake_webdriver  # type: ignore[attr-defined]
_fake_webdriver.common = _fake_common  # type: ignore[attr-defined]
_fake_common.by = _fake_by  # type: ignore[attr-defined]
_fake_common.action_chains = _fake_action_chains  # type: ignore[attr-defined]
_fake_webdriver.support = _fake_support  # type: ignore[attr-defined]
_fake_support.ui = _fake_ui  # type: ignore[attr-defined]
_fake_support.expected_conditions = _fake_ec  # type: ignore[attr-defined]

sys.modules.setdefault("selenium", _fake_selenium)
sys.modules.setdefault("selenium.webdriver", _fake_webdriver)
sys.modules.setdefault("selenium.webdriver.common", _fake_common)
sys.modules.setdefault("selenium.webdriver.common.by", _fake_by)
sys.modules.setdefault("selenium.webdriver.common.action_chains", _fake_action_chains)
sys.modules.setdefault("selenium.webdriver.support", _fake_support)
sys.modules.setdefault("selenium.webdriver.support.ui", _fake_ui)
sys.modules.setdefault("selenium.webdriver.support.expected_conditions", _fake_ec)

from captcha_solver.browser.selenium_adapter import SeleniumAdapter  # noqa: E402
from captcha_solver.browser.playwright_adapter import PlaywrightAdapter  # noqa: E402


# ---------------------------------------------------------------------------
# SeleniumAdapter tests
# ---------------------------------------------------------------------------


class TestSeleniumAdapter:
    def _make_adapter(self) -> tuple[SeleniumAdapter, MagicMock]:
        driver = MagicMock()
        return SeleniumAdapter(driver), driver

    def test_instantiation(self) -> None:
        adapter, driver = self._make_adapter()
        assert adapter._driver is driver

    def test_screenshot_full_page(self) -> None:
        adapter, driver = self._make_adapter()
        driver.get_screenshot_as_png.return_value = b"\x89PNG"
        result = adapter.screenshot()
        assert result == b"\x89PNG"
        driver.get_screenshot_as_png.assert_called_once()

    def test_screenshot_element(self) -> None:
        adapter, _driver = self._make_adapter()
        el = MagicMock()
        el.screenshot_as_png = b"\x89PNG-element"
        result = adapter.screenshot(el)
        assert result == b"\x89PNG-element"

    def test_full_page_screenshot(self) -> None:
        adapter, driver = self._make_adapter()
        driver.get_screenshot_as_png.return_value = b"full"
        assert adapter.full_page_screenshot() == b"full"

    def test_find_element(self) -> None:
        adapter, driver = self._make_adapter()
        mock_el = MagicMock()
        driver.find_element.return_value = mock_el

        result = adapter.find_element("div.test")
        assert result is mock_el
        driver.find_element.assert_called_once_with("css selector", "div.test")

    def test_find_elements(self) -> None:
        adapter, driver = self._make_adapter()
        mock_els = [MagicMock(), MagicMock()]
        driver.find_elements.return_value = mock_els

        result = adapter.find_elements("div.test")
        assert result == mock_els
        driver.find_elements.assert_called_once_with("css selector", "div.test")

    def test_execute_js(self) -> None:
        adapter, driver = self._make_adapter()
        driver.execute_script.return_value = 42
        result = adapter.execute_js("return 1+1")
        assert result == 42

    def test_click_element(self) -> None:
        adapter, _driver = self._make_adapter()
        el = MagicMock()
        adapter.click_element(el)
        el.click.assert_called_once()

    def test_type_text(self) -> None:
        adapter, _driver = self._make_adapter()
        el = MagicMock()
        adapter.type_text(el, "hello")
        el.clear.assert_called_once()
        el.send_keys.assert_called_once_with("hello")

    def test_get_page_url(self) -> None:
        adapter, driver = self._make_adapter()
        type(driver).current_url = PropertyMock(return_value="https://example.com")
        assert adapter.get_page_url() == "https://example.com"

    def test_get_page_source(self) -> None:
        adapter, driver = self._make_adapter()
        type(driver).page_source = PropertyMock(return_value="<html></html>")
        assert adapter.get_page_source() == "<html></html>"

    def test_switch_to_iframe(self) -> None:
        adapter, driver = self._make_adapter()
        iframe = MagicMock()
        adapter.switch_to_iframe(iframe)
        driver.switch_to.frame.assert_called_once_with(iframe)

    def test_switch_to_default(self) -> None:
        adapter, driver = self._make_adapter()
        adapter.switch_to_default()
        driver.switch_to.default_content.assert_called_once()

    def test_get_element_attribute(self) -> None:
        adapter, _driver = self._make_adapter()
        el = MagicMock()
        el.get_attribute.return_value = "my-value"
        assert adapter.get_element_attribute(el, "data-key") == "my-value"
        el.get_attribute.assert_called_once_with("data-key")


# ---------------------------------------------------------------------------
# PlaywrightAdapter tests
# ---------------------------------------------------------------------------


class TestPlaywrightAdapter:
    def _make_adapter(self) -> tuple[PlaywrightAdapter, MagicMock]:
        page = MagicMock()
        return PlaywrightAdapter(page), page

    def test_instantiation(self) -> None:
        adapter, page = self._make_adapter()
        assert adapter._page is page
        assert adapter._page_stack == []

    def test_screenshot_full_page_default(self) -> None:
        adapter, page = self._make_adapter()
        page.screenshot.return_value = b"\x89PNG"
        result = adapter.screenshot()
        assert result == b"\x89PNG"
        page.screenshot.assert_called_once()

    def test_screenshot_element(self) -> None:
        adapter, _page = self._make_adapter()
        el = MagicMock()
        el.screenshot.return_value = b"\x89PNG-el"
        result = adapter.screenshot(el)
        assert result == b"\x89PNG-el"
        el.screenshot.assert_called_once()

    def test_full_page_screenshot(self) -> None:
        adapter, page = self._make_adapter()
        page.screenshot.return_value = b"full"
        result = adapter.full_page_screenshot()
        assert result == b"full"
        page.screenshot.assert_called_once_with(full_page=True)

    def test_find_element(self) -> None:
        adapter, page = self._make_adapter()
        mock_el = MagicMock()
        page.query_selector.return_value = mock_el
        result = adapter.find_element("div.test")
        assert result is mock_el
        page.query_selector.assert_called_once_with("div.test")

    def test_find_elements(self) -> None:
        adapter, page = self._make_adapter()
        mock_els = [MagicMock()]
        page.query_selector_all.return_value = mock_els
        result = adapter.find_elements("div.test")
        assert result == mock_els

    def test_execute_js(self) -> None:
        adapter, page = self._make_adapter()
        page.evaluate.return_value = 42
        result = adapter.execute_js("1 + 1")
        assert result == 42

    def test_click(self) -> None:
        adapter, page = self._make_adapter()
        adapter.click(100, 200)
        page.mouse.click.assert_called_once_with(100, 200)

    def test_click_element(self) -> None:
        adapter, _page = self._make_adapter()
        el = MagicMock()
        adapter.click_element(el)
        el.click.assert_called_once()

    def test_type_text(self) -> None:
        adapter, _page = self._make_adapter()
        el = MagicMock()
        adapter.type_text(el, "hello")
        el.fill.assert_called_once_with("hello")

    def test_get_page_url(self) -> None:
        adapter, page = self._make_adapter()
        type(page).url = PropertyMock(return_value="https://example.com")
        assert adapter.get_page_url() == "https://example.com"

    def test_get_page_source(self) -> None:
        adapter, page = self._make_adapter()
        page.content.return_value = "<html></html>"
        assert adapter.get_page_source() == "<html></html>"

    def test_switch_to_iframe(self) -> None:
        adapter, page = self._make_adapter()
        iframe = MagicMock()
        frame = MagicMock()
        iframe.content_frame.return_value = frame

        adapter.switch_to_iframe(iframe)

        assert adapter._page is frame
        assert adapter._page_stack == [page]

    def test_switch_to_default(self) -> None:
        adapter, page = self._make_adapter()
        iframe = MagicMock()
        frame = MagicMock()
        iframe.content_frame.return_value = frame

        adapter.switch_to_iframe(iframe)
        adapter.switch_to_default()

        assert adapter._page is page
        assert adapter._page_stack == []

    def test_switch_to_default_no_stack(self) -> None:
        """switch_to_default when no iframes have been entered is a no-op."""
        adapter, page = self._make_adapter()
        adapter.switch_to_default()
        assert adapter._page is page

    def test_wait_for_selector(self) -> None:
        adapter, page = self._make_adapter()
        mock_el = MagicMock()
        page.wait_for_selector.return_value = mock_el
        result = adapter.wait_for_selector("div.loaded", timeout=5.0)
        assert result is mock_el
        page.wait_for_selector.assert_called_once_with("div.loaded", timeout=5000.0)

    def test_get_element_attribute(self) -> None:
        adapter, _page = self._make_adapter()
        el = MagicMock()
        el.get_attribute.return_value = "value"
        assert adapter.get_element_attribute(el, "data-key") == "value"


# ---------------------------------------------------------------------------
# Import error tests
# ---------------------------------------------------------------------------


class TestImportErrors:
    """Verify that adapters give clear errors when deps are missing."""

    def test_selenium_adapter_find_element_needs_selenium(self) -> None:
        """SeleniumAdapter.find_element lazily imports selenium.webdriver.common.by.

        When selenium is truly absent, importing By raises ImportError.
        We simulate this by temporarily blocking the module in sys.modules.
        """
        adapter, _driver = TestSeleniumAdapter()._make_adapter()
        blocked = {
            "selenium": None,
            "selenium.webdriver": None,
            "selenium.webdriver.common": None,
            "selenium.webdriver.common.by": None,
        }
        with patch.dict("sys.modules", blocked):
            with pytest.raises((ImportError, ModuleNotFoundError)):
                adapter.find_element("div")

    def test_playwright_adapter_instantiates_without_playwright(self) -> None:
        """PlaywrightAdapter does not import playwright at module level."""
        page = MagicMock()
        # Should not raise - no top-level import of playwright
        adapter = PlaywrightAdapter(page)
        assert adapter._page is page
