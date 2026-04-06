"""Universal Captcha Solver - solve any captcha with one line of code."""
from __future__ import annotations

from pathlib import Path
from typing import Any

__version__ = "0.1.0"


def solve(
    image: bytes | str | Path | None = None,
    captcha_type: str | None = None,
    **kwargs: Any,
) -> "CaptchaResult":  # noqa: F821
    """Solve a captcha in one line.

    Args:
        image: File path (str/Path) or raw image bytes.
        captcha_type: Optional type hint ("text", "slider", "math", etc.)

    Returns:
        CaptchaResult with solution, confidence, timing.

    Example:
        >>> from captcha_solver import solve
        >>> result = solve("captcha.png")
        >>> print(result.solution)
    """
    from captcha_solver.core.pipeline import get_default_pipeline

    pipeline = get_default_pipeline()
    return pipeline.solve(image=image, captcha_type=captcha_type, **kwargs)


def detect(image: bytes | str | Path) -> tuple:
    """Detect captcha type from image.

    Returns:
        Tuple of (CaptchaType, confidence).
    """
    from captcha_solver.core.pipeline import get_default_pipeline

    pipeline = get_default_pipeline()
    return pipeline.detect(image)
