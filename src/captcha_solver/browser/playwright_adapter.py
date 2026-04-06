"""Playwright Page adapter (sync API)."""
from __future__ import annotations

from typing import Any, Optional

from captcha_solver.browser.base import BrowserAdapter


class PlaywrightAdapter(BrowserAdapter):
    """Adapter wrapping a Playwright sync Page instance."""

    def __init__(self, page: Any) -> None:
        self._page = page
        self._page_stack: list[Any] = []

    def screenshot(self, element: Any = None) -> bytes:
        if element is not None:
            return element.screenshot()  # type: ignore[no-any-return]
        return self._page.screenshot()  # type: ignore[no-any-return]

    def full_page_screenshot(self) -> bytes:
        return self._page.screenshot(full_page=True)  # type: ignore[no-any-return]

    def find_element(self, selector: str) -> Any:
        return self._page.query_selector(selector)

    def find_elements(self, selector: str) -> list[Any]:
        return self._page.query_selector_all(selector)  # type: ignore[no-any-return]

    def execute_js(self, script: str, *args: Any) -> Any:
        return self._page.evaluate(script, *args)

    def click(self, x: int, y: int) -> None:
        self._page.mouse.click(x, y)

    def click_element(self, element: Any) -> None:
        element.click()

    def type_text(self, element: Any, text: str) -> None:
        element.fill(text)

    def get_page_url(self) -> str:
        return self._page.url  # type: ignore[no-any-return]

    def get_page_source(self) -> str:
        return self._page.content()  # type: ignore[no-any-return]

    def switch_to_iframe(self, iframe: Any) -> None:
        frame = iframe.content_frame()
        self._page_stack.append(self._page)
        self._page = frame

    def switch_to_default(self) -> None:
        if self._page_stack:
            self._page = self._page_stack[0]
            self._page_stack.clear()

    def wait_for_selector(self, selector: str, timeout: float = 10.0) -> Any:
        return self._page.wait_for_selector(selector, timeout=timeout * 1000)

    def get_element_attribute(self, element: Any, attr: str) -> Optional[str]:
        return element.get_attribute(attr)  # type: ignore[no-any-return]
