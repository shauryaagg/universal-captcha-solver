"""Base solver types and abstractions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from captcha_solver.core.result import CaptchaResult


class CaptchaType(str, Enum):
    TEXT = "text"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    SLIDER = "slider"
    MATH = "math"
    AUDIO = "audio"
    GEETEST = "geetest"


@dataclass
class SolverInput:
    image: Optional[bytes] = None
    audio: Optional[bytes] = None
    page_url: Optional[str] = None
    site_key: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseSolver(ABC):
    @property
    @abstractmethod
    def captcha_type(self) -> CaptchaType: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def can_solve(self, solver_input: SolverInput) -> bool: ...

    @abstractmethod
    def solve(self, solver_input: SolverInput) -> CaptchaResult: ...

    def preprocess(self, solver_input: SolverInput) -> SolverInput:
        return solver_input

    async def asolve(self, solver_input: SolverInput) -> CaptchaResult:
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.solve, solver_input)
