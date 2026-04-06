"""Browser automation integration for captcha solving."""
from __future__ import annotations

from typing import Any

from captcha_solver.browser.base import BrowserAdapter, CaptchaElementInfo
from captcha_solver.core.result import CaptchaResult


def solve_captcha(driver_or_page: Any, **kwargs: Any) -> CaptchaResult:
    """Auto-detect browser type and solve captcha on page.

    Args:
        driver_or_page: Selenium WebDriver or Playwright Page
        **kwargs: Additional options (captcha_type, etc.)
    """
    adapter = _wrap(driver_or_page)
    from captcha_solver.browser.detection import detect_captcha_in_page
    from captcha_solver.core.pipeline import get_default_pipeline

    # Detect captcha in page
    captcha_info = detect_captcha_in_page(adapter)

    pipeline = get_default_pipeline()

    if captcha_info and captcha_info.element:
        # Screenshot the captcha element
        screenshot = adapter.screenshot(captcha_info.element)
        captcha_type = kwargs.get("captcha_type", captcha_info.captcha_type)
        return pipeline.solve(
            image=screenshot,
            captcha_type=captcha_type,
            page_url=captcha_info.page_url,
            site_key=captcha_info.site_key,
            **{k: v for k, v in kwargs.items() if k != "captcha_type"},
        )
    else:
        # Fall back to full page screenshot
        screenshot = adapter.full_page_screenshot()
        return pipeline.solve(image=screenshot, **kwargs)


async def asolve_captcha(page: Any, **kwargs: Any) -> CaptchaResult:
    """Async version for Playwright async pages."""
    import asyncio

    return await asyncio.get_event_loop().run_in_executor(
        None, lambda: solve_captcha(page, **kwargs)
    )


def get_adapter(driver_or_page: Any) -> BrowserAdapter:
    """Get a BrowserAdapter for the given driver or page."""
    return _wrap(driver_or_page)


def _wrap(obj: Any) -> BrowserAdapter:
    """Duck-type detection: Selenium vs Playwright."""
    # Check for Selenium WebDriver
    if hasattr(obj, "find_element") and hasattr(obj, "execute_script"):
        from captcha_solver.browser.selenium_adapter import SeleniumAdapter

        return SeleniumAdapter(obj)
    # Check for Playwright Page
    if hasattr(obj, "query_selector") and hasattr(obj, "evaluate"):
        from captcha_solver.browser.playwright_adapter import PlaywrightAdapter

        return PlaywrightAdapter(obj)
    raise TypeError(
        f"Unsupported browser type: {type(obj)}. "
        "Expected Selenium WebDriver or Playwright Page."
    )


__all__ = [
    "BrowserAdapter",
    "CaptchaElementInfo",
    "asolve_captcha",
    "get_adapter",
    "solve_captcha",
]
