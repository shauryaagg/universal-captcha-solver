"""Selenium WebDriver adapter."""
from __future__ import annotations

from typing import Any, Optional

from captcha_solver.browser.base import BrowserAdapter


class SeleniumAdapter(BrowserAdapter):
    """Adapter wrapping a Selenium WebDriver instance."""

    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def screenshot(self, element: Any = None) -> bytes:
        if element is not None:
            return element.screenshot_as_png  # type: ignore[no-any-return]
        return self._driver.get_screenshot_as_png()  # type: ignore[no-any-return]

    def full_page_screenshot(self) -> bytes:
        return self._driver.get_screenshot_as_png()  # type: ignore[no-any-return]

    def find_element(self, selector: str) -> Any:
        from selenium.webdriver.common.by import By

        return self._driver.find_element(By.CSS_SELECTOR, selector)

    def find_elements(self, selector: str) -> list[Any]:
        from selenium.webdriver.common.by import By

        return self._driver.find_elements(By.CSS_SELECTOR, selector)  # type: ignore[no-any-return]

    def execute_js(self, script: str, *args: Any) -> Any:
        return self._driver.execute_script(script, *args)

    def click(self, x: int, y: int) -> None:
        from selenium.webdriver.common.action_chains import ActionChains

        actions = ActionChains(self._driver)
        actions.move_by_offset(x, y).click().perform()

    def click_element(self, element: Any) -> None:
        element.click()

    def type_text(self, element: Any, text: str) -> None:
        element.clear()
        element.send_keys(text)

    def get_page_url(self) -> str:
        return self._driver.current_url  # type: ignore[no-any-return]

    def get_page_source(self) -> str:
        return self._driver.page_source  # type: ignore[no-any-return]

    def switch_to_iframe(self, iframe: Any) -> None:
        self._driver.switch_to.frame(iframe)

    def switch_to_default(self) -> None:
        self._driver.switch_to.default_content()

    def wait_for_selector(self, selector: str, timeout: float = 10.0) -> Any:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        wait = WebDriverWait(self._driver, timeout)
        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

    def get_element_attribute(self, element: Any, attr: str) -> Optional[str]:
        return element.get_attribute(attr)  # type: ignore[no-any-return]
