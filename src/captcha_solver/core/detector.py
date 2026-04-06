"""Rule-based captcha type detection."""
from __future__ import annotations

import io

from PIL import Image

from captcha_solver.solvers.base import CaptchaType, SolverInput


class CaptchaDetector:
    """Detect captcha type from image characteristics and metadata."""

    def detect(self, solver_input: SolverInput) -> CaptchaType:
        """Return the most likely captcha type."""
        captcha_type, _ = self.detect_with_confidence(solver_input)
        return captcha_type

    def detect_with_confidence(self, solver_input: SolverInput) -> tuple[CaptchaType, float]:
        """Return captcha type and confidence score."""
        # Check metadata hints first
        if solver_input.site_key:
            return CaptchaType.RECAPTCHA_V2, 0.9

        if solver_input.audio is not None:
            return CaptchaType.AUDIO, 0.95

        if solver_input.image is None:
            return CaptchaType.TEXT, 0.1  # Low confidence fallback

        img = Image.open(io.BytesIO(solver_input.image))
        width, height = img.size
        aspect_ratio = width / max(height, 1)

        # Slider: very wide aspect ratio (>3:1)
        if aspect_ratio > 3.0:
            return CaptchaType.SLIDER, 0.85

        # Grid captchas (reCAPTCHA v2): roughly square, large
        if 0.8 < aspect_ratio < 1.2 and width > 200:
            return CaptchaType.RECAPTCHA_V2, 0.6

        # Text captchas: moderate aspect ratio (1.5:1 to 3:1), small to medium
        if 1.5 < aspect_ratio <= 3.0 and width < 400:
            return CaptchaType.TEXT, 0.75

        # Default fallback
        return CaptchaType.TEXT, 0.5
