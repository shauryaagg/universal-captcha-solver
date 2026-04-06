"""Human behavior simulation for score-based captchas."""
from __future__ import annotations

import random
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from captcha_solver.browser.base import BrowserAdapter


def bezier_curve(
    start: tuple[float, float],
    end: tuple[float, float],
    num_points: int = 20,
) -> list[tuple[int, int]]:
    """Generate points along a cubic Bezier curve for natural mouse movement."""
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy

    cp1 = (
        sx + dx * random.uniform(0.2, 0.4) + random.uniform(-50, 50),
        sy + dy * random.uniform(0.2, 0.4) + random.uniform(-50, 50),
    )
    cp2 = (
        sx + dx * random.uniform(0.6, 0.8) + random.uniform(-50, 50),
        sy + dy * random.uniform(0.6, 0.8) + random.uniform(-50, 50),
    )

    points: list[tuple[int, int]] = []
    for i in range(num_points + 1):
        t = i / num_points
        t2 = t * t
        t3 = t2 * t
        mt = 1 - t
        mt2 = mt * mt
        mt3 = mt2 * mt

        x = mt3 * sx + 3 * mt2 * t * cp1[0] + 3 * mt * t2 * cp2[0] + t3 * ex
        y = mt3 * sy + 3 * mt2 * t * cp1[1] + 3 * mt * t2 * cp2[1] + t3 * ey
        points.append((int(x), int(y)))

    return points


def simulate_mouse_movement(
    adapter: BrowserAdapter,
    start: tuple[int, int],
    end: tuple[int, int],
) -> None:
    """Move mouse along a natural Bezier curve path."""
    points = bezier_curve(start, end, num_points=random.randint(15, 30))
    for x, y in points:
        adapter.execute_js(
            "document.dispatchEvent(new MouseEvent('mousemove', "
            "{clientX: arguments[0], clientY: arguments[1]}))",
            x,
            y,
        )
        time.sleep(random.uniform(0.005, 0.02))


def simulate_scroll(adapter: BrowserAdapter, amount: int = 300) -> None:
    """Simulate natural scrolling behavior."""
    scrolled = 0
    while scrolled < amount:
        chunk = random.randint(30, 80)
        adapter.execute_js(f"window.scrollBy(0, {chunk})")
        scrolled += chunk
        time.sleep(random.uniform(0.05, 0.15))


def simulate_human_delay(min_ms: int = 100, max_ms: int = 500) -> None:
    """Random delay simulating human reaction time."""
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))


def simulate_reading(adapter: BrowserAdapter, duration: float = 2.0) -> None:
    """Simulate reading behavior: small mouse movements + occasional scrolls."""
    end_time = time.time() + duration
    while time.time() < end_time:
        # Small random mouse movements
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        adapter.execute_js(
            "document.dispatchEvent(new MouseEvent('mousemove', "
            "{clientX: arguments[0], clientY: arguments[1]}))",
            x,
            y,
        )
        time.sleep(random.uniform(0.1, 0.4))

        # Occasional scroll
        if random.random() < 0.3:
            simulate_scroll(adapter, random.randint(50, 150))


def simulate_typing(adapter: BrowserAdapter, element: Any, text: str) -> None:
    """Type text with realistic keystroke timing."""
    for char in text:
        adapter.type_text(element, char)
        time.sleep(random.uniform(0.05, 0.2))
