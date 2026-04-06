"""Captcha type detection using image analysis and heuristics."""
from __future__ import annotations

import io
import logging

import numpy as np
from PIL import Image

from captcha_solver.solvers.base import CaptchaType, SolverInput

logger = logging.getLogger(__name__)


class CaptchaDetector:
    """Detect captcha type from image characteristics and metadata."""

    def detect(self, solver_input: SolverInput) -> CaptchaType:
        """Return the most likely captcha type."""
        captcha_type, _ = self.detect_with_confidence(solver_input)
        return captcha_type

    def detect_with_confidence(self, solver_input: SolverInput) -> tuple[CaptchaType, float]:
        """Return captcha type and confidence score."""
        # Priority 1: Explicit metadata hints
        if solver_input.site_key:
            # If page_url hints at hcaptcha, use that
            page_url = solver_input.page_url or ""
            if "hcaptcha" in page_url.lower():
                return CaptchaType.HCAPTCHA, 0.95
            return CaptchaType.RECAPTCHA_V2, 0.90

        if solver_input.audio is not None:
            return CaptchaType.AUDIO, 0.95

        if solver_input.metadata.get("browser") is not None:
            # Browser-based detection — check for known types
            browser_type = solver_input.metadata.get("detected_type")
            if browser_type:
                try:
                    return CaptchaType(browser_type), 0.90
                except ValueError:
                    pass

        if solver_input.image is None:
            # Text-only challenge (no image)
            if solver_input.metadata.get("question"):
                return CaptchaType.TEXT, 0.80
            return CaptchaType.TEXT, 0.1

        # Priority 2: Image-based analysis
        return self._analyze_image(solver_input.image)

    def _analyze_image(self, image_bytes: bytes) -> tuple[CaptchaType, float]:
        """Analyze image properties to determine captcha type."""
        img = Image.open(io.BytesIO(image_bytes))
        width, height = img.size
        aspect_ratio = width / max(height, 1)

        # Convert to numpy for analysis
        arr = np.array(img)

        # Feature extraction
        if len(arr.shape) == 3:
            gray = np.mean(arr[:, :, :3], axis=2)
        else:
            gray = arr.astype(float)

        # Color diversity (low = likely text/math, high = likely photo/grid)
        std_dev = float(np.std(gray))

        # Edge density (high = complex image)
        if gray.shape[0] > 1 and gray.shape[1] > 1:
            edges_h = np.abs(np.diff(gray, axis=1))
            edges_v = np.abs(np.diff(gray, axis=0))
            edge_density = (float(np.mean(edges_h)) + float(np.mean(edges_v))) / 2
        else:
            edge_density = 0.0

        # Unique color count (sampled)
        if len(arr.shape) == 3 and arr.shape[2] >= 3:
            sample = arr[::4, ::4, :3].reshape(-1, 3)
            unique_colors = len(set(map(tuple, sample)))
        else:
            unique_colors = len(np.unique(gray[::4, ::4]))

        logger.debug(
            "Image analysis: %dx%d, ratio=%.2f, std=%.1f, edges=%.1f, colors=%d",
            width,
            height,
            aspect_ratio,
            std_dev,
            edge_density,
            unique_colors,
        )

        # Decision tree

        # Slider: very wide aspect ratio
        if aspect_ratio > 3.0:
            return CaptchaType.SLIDER, 0.90

        # Grid captcha: square-ish, large, many colors (photo content)
        if 0.7 < aspect_ratio < 1.3 and width > 200 and unique_colors > 100:
            return CaptchaType.RECAPTCHA_V2, 0.70

        # GeeTest: medium aspect ratio, high edge density, colorful
        if 1.3 < aspect_ratio < 2.5 and width > 250 and unique_colors > 80:
            return CaptchaType.GEETEST, 0.55

        # Text/Math captcha: low color diversity, small image
        if unique_colors < 50 and width < 400:
            # Wider images are more likely text captchas
            if aspect_ratio > 1.5:
                return CaptchaType.TEXT, 0.75
            # Square-ish, very simple images are more likely math
            if std_dev < 80 and edge_density < 20:
                return CaptchaType.MATH, 0.60
            return CaptchaType.TEXT, 0.70

        # Medium text captcha
        if 1.5 < aspect_ratio < 4.0 and width < 500:
            return CaptchaType.TEXT, 0.65

        # Default fallback
        return CaptchaType.TEXT, 0.50
