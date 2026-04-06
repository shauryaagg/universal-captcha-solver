"""Browser stealth and anti-detection utilities."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from captcha_solver.browser.base import BrowserAdapter


# JavaScript to patch common bot detection vectors
STEALTH_SCRIPTS = [
    # Remove webdriver flag
    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
    # Chrome runtime
    "window.chrome = {runtime: {}, loadTimes: function(){}, csi: function(){}}",
    # Permissions
    """
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({state: Notification.permission}) :
            originalQuery(parameters)
    );
    """,
    # Plugins (make it look like a real browser)
    """
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    """,
    # Languages
    """
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en'],
    });
    """,
]


def apply_stealth(adapter: BrowserAdapter) -> None:
    """Apply stealth patches to avoid bot detection."""
    for script in STEALTH_SCRIPTS:
        try:
            adapter.execute_js(script)
        except Exception:
            pass  # Some scripts may fail in certain contexts


def patch_webdriver(adapter: BrowserAdapter) -> None:
    """Remove navigator.webdriver flag."""
    try:
        adapter.execute_js(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
    except Exception:
        pass
