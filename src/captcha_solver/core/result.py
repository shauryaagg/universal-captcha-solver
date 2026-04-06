"""Captcha solving result types."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CaptchaResult:
    """Result from solving a captcha."""

    solution: str
    captcha_type: str
    confidence: float
    solver_name: str
    elapsed_ms: float
    raw: Optional[Any] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "solution": self.solution,
            "captcha_type": self.captcha_type,
            "confidence": self.confidence,
            "solver_name": self.solver_name,
            "elapsed_ms": self.elapsed_ms,
        }
