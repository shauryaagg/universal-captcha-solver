"""Tests for captcha_solver.core.detector.CaptchaDetector."""

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
        """Square 300x300 image should detect as reCAPTCHA v2 (grid)."""
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
        assert confidence == 0.9

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
