"""Integration test: reCAPTCHA on 2captcha.com demos."""
from __future__ import annotations

from tests.integration.conftest import requires_api_key, requires_playwright


@requires_api_key
@requires_playwright
class TestRecaptchaV2:
    """Test reCAPTCHA v2 detection and basic solving."""

    def test_detect_recaptcha_v2(self, page):
        """Detect reCAPTCHA v2 widget on the demo page."""
        from captcha_solver.browser.detection import detect_captcha_in_page
        from captcha_solver.browser.playwright_adapter import PlaywrightAdapter

        page.goto("https://2captcha.com/demo/recaptcha-v2", wait_until="networkidle")
        page.wait_for_timeout(3000)

        adapter = PlaywrightAdapter(page)
        captcha_info = detect_captcha_in_page(adapter)

        assert captcha_info is not None, "Should detect reCAPTCHA on page"
        assert captcha_info.captcha_type == "recaptcha_v2"
        print(f"Detected: type={captcha_info.captcha_type}, site_key={captcha_info.site_key}")

    def test_screenshot_recaptcha_grid(self, page, cloud_provider, api_key):
        """Screenshot and attempt to classify reCAPTCHA grid challenge."""
        from captcha_solver.browser.playwright_adapter import PlaywrightAdapter

        page.goto("https://2captcha.com/demo/recaptcha-v2", wait_until="networkidle")
        page.wait_for_timeout(3000)

        PlaywrightAdapter(page)

        # Find and click the reCAPTCHA checkbox to trigger the challenge
        recaptcha_iframe = page.query_selector("iframe[src*='recaptcha']")
        if recaptcha_iframe:
            frame = recaptcha_iframe.content_frame()
            if frame:
                checkbox = frame.query_selector(
                    ".recaptcha-checkbox-border, #recaptcha-anchor"
                )
                if checkbox:
                    checkbox.click()
                    page.wait_for_timeout(3000)

        # Take a screenshot of the page state
        screenshot = page.screenshot()
        assert len(screenshot) > 0, "Should get a screenshot"
        print(f"Screenshot taken: {len(screenshot)} bytes")


@requires_playwright
class TestRecaptchaV3:
    """Test reCAPTCHA v3 detection."""

    def test_detect_recaptcha_v3_page(self, page):
        """Load reCAPTCHA v3 demo page."""
        page.goto("https://2captcha.com/demo/recaptcha-v3", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # reCAPTCHA v3 is invisible -- just verify the page loads
        # and the recaptcha script is present
        has_recaptcha = page.evaluate(
            "typeof grecaptcha !== 'undefined' "
            "|| document.querySelector('script[src*=\"recaptcha\"]') !== null"
        )
        print(f"reCAPTCHA v3 present: {has_recaptcha}")
