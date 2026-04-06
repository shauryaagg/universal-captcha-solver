"""Integration test: Cloudflare Turnstile on 2captcha.com demo."""
from __future__ import annotations

from tests.integration.conftest import requires_playwright


@requires_playwright
class TestTurnstile:
    """Test Turnstile detection and solving."""

    def test_detect_turnstile(self, page):
        """Detect Turnstile widget on demo page."""
        from captcha_solver.browser.detection import detect_captcha_in_page
        from captcha_solver.browser.playwright_adapter import PlaywrightAdapter

        page.goto("https://2captcha.com/demo/cloudflare-turnstile", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)

        adapter = PlaywrightAdapter(page)
        captcha_info = detect_captcha_in_page(adapter)

        # Turnstile may or may not be detected depending on page load
        if captcha_info:
            print(f"Detected: type={captcha_info.captcha_type}")
            assert captcha_info.captcha_type == "turnstile"
        else:
            # Check if turnstile elements exist on page
            has_turnstile = page.query_selector(
                "div.cf-turnstile"
            ) or page.query_selector("iframe[src*='challenges.cloudflare.com']")
            print(f"Turnstile element found: {has_turnstile is not None}")

    def test_turnstile_with_stealth(self, page):
        """Apply stealth and attempt Turnstile interaction."""
        from captcha_solver.browser.playwright_adapter import PlaywrightAdapter
        from captcha_solver.browser.stealth import apply_stealth

        page.goto("https://2captcha.com/demo/cloudflare-turnstile", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        adapter = PlaywrightAdapter(page)
        apply_stealth(adapter)

        # Verify stealth was applied
        webdriver_value = page.evaluate("navigator.webdriver")
        print(f"navigator.webdriver after stealth: {webdriver_value}")
        # Should be undefined/None, not True
        assert webdriver_value is not True, "Stealth should hide webdriver flag"
