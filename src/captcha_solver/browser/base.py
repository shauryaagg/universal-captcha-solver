"""Browser adapter abstraction."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CaptchaElementInfo:
    """Information about a detected captcha element on a page."""

    captcha_type: str
    element: Any = None
    site_key: str = ""
    page_url: str = ""
    iframe_src: str = ""
    needs_interaction: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class BrowserAdapter(ABC):
    """Unified interface over Selenium and Playwright."""

    @abstractmethod
    def screenshot(self, element: Any = None) -> bytes: ...

    @abstractmethod
    def full_page_screenshot(self) -> bytes: ...

    @abstractmethod
    def find_element(self, selector: str) -> Any: ...

    @abstractmethod
    def find_elements(self, selector: str) -> list[Any]: ...

    @abstractmethod
    def execute_js(self, script: str, *args: Any) -> Any: ...

    @abstractmethod
    def click(self, x: int, y: int) -> None: ...

    @abstractmethod
    def click_element(self, element: Any) -> None: ...

    @abstractmethod
    def type_text(self, element: Any, text: str) -> None: ...

    @abstractmethod
    def get_page_url(self) -> str: ...

    @abstractmethod
    def get_page_source(self) -> str: ...

    @abstractmethod
    def switch_to_iframe(self, iframe: Any) -> None: ...

    @abstractmethod
    def switch_to_default(self) -> None: ...

    @abstractmethod
    def wait_for_selector(self, selector: str, timeout: float = 10.0) -> Any: ...

    @abstractmethod
    def get_element_attribute(self, element: Any, attr: str) -> Optional[str]: ...
