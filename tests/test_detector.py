"""Tests for captcha_solver.core.detector.CaptchaDetector."""

import io

import numpy as np
from PIL import Image

from captcha_solver.core.detector import CaptchaDetector
from captcha_solver.solvers.base import CaptchaType, SolverInput


class TestCaptchaDetector:
    def setup_method(self):
        self.detector = CaptchaDetector()

    def test_slider_detection(self, sample_slider_image: bytes):
        """Wide aspect-ratio image (400x100) should detect as slider."""
        inp = SolverInput(image=sample_slider_image)
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.SLIDER
        assert confidence > 0.5

    def test_square_image_detects_grid(self, sample_square_image: bytes):
        """Square 300x300 image with many colours should detect as reCAPTCHA v2 (grid)."""
        inp = SolverInput(image=sample_square_image)
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.RECAPTCHA_V2
        assert confidence > 0.5

    def test_text_shaped_image(self, sample_text_image: bytes):
        """200x80 image (aspect ~2.5) should detect as text."""
        inp = SolverInput(image=sample_text_image)
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.TEXT
        assert confidence > 0.5

    def test_site_key_metadata(self):
        """Input with site_key should detect as reCAPTCHA v2."""
        inp = SolverInput(site_key="6LeIxAcTAAAA...")
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.RECAPTCHA_V2
        assert confidence == 0.90

    def test_audio_input(self):
        """Input with audio data should detect as audio captcha."""
        inp = SolverInput(audio=b"fake-audio-data")
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.AUDIO
        assert confidence == 0.95

    def test_fallback_no_image(self):
        """No image and no metadata: low-confidence text fallback."""
        inp = SolverInput()
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.TEXT
        assert confidence < 0.5

    def test_detect_returns_type_only(self, sample_text_image: bytes):
        """detect() (without confidence) should return just the CaptchaType."""
        inp = SolverInput(image=sample_text_image)
        ctype = self.detector.detect(inp)
        assert isinstance(ctype, CaptchaType)

    # --- New tests for improved detection ---

    def test_many_colors_grid_detection(self):
        """Large square image with high colour diversity -> grid (reCAPTCHA v2)."""
        rng = np.random.default_rng(7)
        arr = rng.integers(0, 256, size=(350, 350, 3), dtype=np.uint8)
        img = Image.fromarray(arr, "RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        inp = SolverInput(image=buf.getvalue())
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.RECAPTCHA_V2
        assert confidence >= 0.70

    def test_narrow_low_color_text(self):
        """Narrow image with few colours -> text captcha."""
        img = Image.new("RGB", (250, 100), color=(240, 240, 240))
        from PIL import ImageDraw

        draw = ImageDraw.Draw(img)
        draw.text((10, 30), "HELLO", fill=(30, 30, 30))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        inp = SolverInput(image=buf.getvalue())
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.TEXT
        assert confidence > 0.5

    def test_wide_image_slider(self):
        """Very wide image (aspect > 3) -> slider."""
        img = Image.new("RGB", (600, 100), color=(150, 150, 150))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        inp = SolverInput(image=buf.getvalue())
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.SLIDER
        assert confidence >= 0.90

    def test_geetest_like_image(self, sample_geetest_image: bytes):
        """Medium-ratio colourful image -> GeeTest."""
        inp = SolverInput(image=sample_geetest_image)
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.GEETEST
        assert confidence > 0.5

    def test_browser_metadata_detected_type(self):
        """Browser metadata with detected_type should be honoured."""
        inp = SolverInput(
            metadata={"browser": "chromium", "detected_type": "turnstile"},
        )
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.TURNSTILE
        assert confidence == 0.90

    def test_browser_metadata_invalid_type_falls_through(self):
        """Invalid detected_type should fall through to other heuristics."""
        inp = SolverInput(
            metadata={"browser": "chromium", "detected_type": "unknown_xyz"},
        )
        # No image, no question -> low-confidence TEXT fallback
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.TEXT
        assert confidence < 0.5

    def test_question_metadata_text(self):
        """Input with a question in metadata (no image) -> TEXT with decent confidence."""
        inp = SolverInput(metadata={"question": "What colour is the sky?"})
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.TEXT
        assert confidence == 0.80

    def test_site_key_hcaptcha_url(self):
        """site_key + hcaptcha in page_url -> HCAPTCHA."""
        inp = SolverInput(
            site_key="abc123",
            page_url="https://example.com/hcaptcha/verify",
        )
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.HCAPTCHA
        assert confidence == 0.95

    def test_site_key_no_hcaptcha_url(self):
        """site_key without hcaptcha URL -> reCAPTCHA v2."""
        inp = SolverInput(
            site_key="abc123",
            page_url="https://example.com/login",
        )
        ctype, confidence = self.detector.detect_with_confidence(inp)
        assert ctype == CaptchaType.RECAPTCHA_V2
        assert confidence == 0.90
