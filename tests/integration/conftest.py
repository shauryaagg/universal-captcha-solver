"""Integration test configuration for 2captcha.com demo tests."""
from __future__ import annotations

import os

import pytest

# Skip all integration tests if no API key is set
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get(
    "CAPTCHA_SOLVER_ANTHROPIC_API_KEY"
)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get(
    "CAPTCHA_SOLVER_OPENAI_API_KEY"
)
HAS_API_KEY = bool(ANTHROPIC_API_KEY or OPENAI_API_KEY)

requires_api_key = pytest.mark.skipif(
    not HAS_API_KEY,
    reason="No API key set. Set ANTHROPIC_API_KEY or OPENAI_API_KEY to run integration tests.",
)

# Check if Playwright is available
try:
    from playwright.sync_api import sync_playwright  # noqa: F401

    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

requires_playwright = pytest.mark.skipif(
    not HAS_PLAYWRIGHT,
    reason="Playwright not installed. Run: pip install playwright && playwright install chromium",
)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply 'integration' marker to all tests in this directory."""
    for item in items:
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(scope="session")
def cloud_provider() -> str:
    if ANTHROPIC_API_KEY:
        return "anthropic"
    return "openai"


@pytest.fixture(scope="session")
def api_key() -> str:
    return ANTHROPIC_API_KEY or OPENAI_API_KEY or ""


@pytest.fixture(scope="session")
def browser_context():
    """Shared Playwright browser for all integration tests."""
    if not HAS_PLAYWRIGHT:
        pytest.skip("Playwright not available")

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    )
    yield context
    context.close()
    browser.close()
    pw.stop()


@pytest.fixture
def page(browser_context):
    """Fresh page for each test."""
    page = browser_context.new_page()
    yield page
    page.close()
