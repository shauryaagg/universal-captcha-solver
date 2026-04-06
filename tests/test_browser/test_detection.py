"""Tests for browser detection and _wrap() duck typing."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from captcha_solver.browser import _wrap, get_adapter
from captcha_solver.browser.base import CaptchaElementInfo
from captcha_solver.browser.detection import detect_captcha_in_page


# ---------------------------------------------------------------------------
# _wrap() duck-typing tests
# ---------------------------------------------------------------------------


class TestWrap:
    """Test that _wrap() correctly identifies Selenium vs Playwright objects."""

    def test_selenium_driver_detected(self) -> None:
        driver = MagicMock()
        driver.find_element = MagicMock()
        driver.execute_script = MagicMock()
        # Remove playwright attributes so it doesn't match playwright branch
        del driver.query_selector
        del driver.evaluate

        adapter = _wrap(driver)
        assert type(adapter).__name__ == "SeleniumAdapter"

    def test_playwright_page_detected(self) -> None:
        page = MagicMock()
        page.query_selector = MagicMock()
        page.evaluate = MagicMock()
        # Remove selenium attributes so it doesn't match selenium branch
        del page.find_element
        del page.execute_script

        adapter = _wrap(page)
        assert type(adapter).__name__ == "PlaywrightAdapter"

    def test_unknown_type_raises(self) -> None:
        obj = object()
        with pytest.raises(TypeError, match="Unsupported browser type"):
            _wrap(obj)

    def test_get_adapter_returns_browser_adapter(self) -> None:
        page = MagicMock()
        page.query_selector = MagicMock()
        page.evaluate = MagicMock()
        del page.find_element
        del page.execute_script

        adapter = get_adapter(page)
        assert type(adapter).__name__ == "PlaywrightAdapter"


# ---------------------------------------------------------------------------
# detect_captcha_in_page() tests
# ---------------------------------------------------------------------------


class MockAdapter:
    """A minimal mock adapter for testing detection logic."""

    def __init__(self, elements_map: dict[str, list], attributes_map: dict[str, str] | None = None):
        self._elements_map = elements_map
        self._attributes_map = attributes_map or {}

    def find_elements(self, selector: str) -> list:
        return self._elements_map.get(selector, [])

    def find_element(self, selector: str):
        elements = self._elements_map.get(selector, [])
        if elements:
            return elements[0]
        raise Exception(f"No element found for {selector}")

    def get_element_attribute(self, element, attr: str) -> str | None:
        return self._attributes_map.get(attr)

    def get_page_url(self) -> str:
        return "https://example.com/login"


class TestDetectCaptchaInPage:
    def test_detects_recaptcha(self) -> None:
        mock_element = MagicMock()
        adapter = MockAdapter(
            elements_map={
                "div.g-recaptcha": [mock_element],
            },
            attributes_map={"data-sitekey": "6LcXyz123"},
        )

        result = detect_captcha_in_page(adapter)  # type: ignore[arg-type]

        assert result is not None
        assert result.captcha_type == "recaptcha_v2"
        assert result.site_key == "6LcXyz123"
        assert result.page_url == "https://example.com/login"
        assert result.element is mock_element

    def test_detects_hcaptcha(self) -> None:
        mock_element = MagicMock()
        adapter = MockAdapter(
            elements_map={
                "div.h-captcha": [mock_element],
            },
            attributes_map={"data-sitekey": "hcap-key-123"},
        )

        result = detect_captcha_in_page(adapter)  # type: ignore[arg-type]

        assert result is not None
        assert result.captcha_type == "hcaptcha"
        assert result.site_key == "hcap-key-123"

    def test_detects_turnstile(self) -> None:
        mock_element = MagicMock()
        adapter = MockAdapter(
            elements_map={
                "div.cf-turnstile": [mock_element],
            },
            attributes_map={"data-sitekey": "cf-key-456"},
        )

        result = detect_captcha_in_page(adapter)  # type: ignore[arg-type]

        assert result is not None
        assert result.captcha_type == "turnstile"
        assert result.site_key == "cf-key-456"

    def test_detects_text_captcha(self) -> None:
        mock_element = MagicMock()
        adapter = MockAdapter(
            elements_map={
                "img[src*='captcha']": [mock_element],
            },
        )

        result = detect_captcha_in_page(adapter)  # type: ignore[arg-type]

        assert result is not None
        assert result.captcha_type == "text"
        assert result.needs_interaction is False

    def test_detects_geetest(self) -> None:
        mock_element = MagicMock()
        adapter = MockAdapter(
            elements_map={
                "div.geetest_holder": [mock_element],
            },
        )

        result = detect_captcha_in_page(adapter)  # type: ignore[arg-type]

        assert result is not None
        assert result.captcha_type == "geetest"
        assert result.needs_interaction is True

    def test_returns_none_when_no_captcha(self) -> None:
        adapter = MockAdapter(elements_map={})

        result = detect_captcha_in_page(adapter)  # type: ignore[arg-type]

        assert result is None

    def test_handles_exceptions_gracefully(self) -> None:
        """If find_elements raises, detection continues to next signature."""

        class FailingAdapter(MockAdapter):
            def find_elements(self, selector: str) -> list:
                if "recaptcha" in selector:
                    raise RuntimeError("boom")
                return super().find_elements(selector)

        mock_element = MagicMock()
        adapter = FailingAdapter(
            elements_map={
                "img.captcha": [mock_element],
            },
        )

        result = detect_captcha_in_page(adapter)  # type: ignore[arg-type]

        assert result is not None
        assert result.captcha_type == "text"

    def test_captcha_element_info_defaults(self) -> None:
        info = CaptchaElementInfo(captcha_type="text")
        assert info.element is None
        assert info.site_key == ""
        assert info.page_url == ""
        assert info.iframe_src == ""
        assert info.needs_interaction is True
        assert info.metadata == {}
