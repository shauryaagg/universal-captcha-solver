"""Tests for captcha_solver.core.result.CaptchaResult."""

from captcha_solver.core.result import CaptchaResult


class TestCaptchaResult:
    def test_construction(self):
        result = CaptchaResult(
            solution="abc123",
            captcha_type="text",
            confidence=0.95,
            solver_name="TextSolver",
            elapsed_ms=42.5,
        )
        assert result.solution == "abc123"
        assert result.captcha_type == "text"
        assert result.confidence == 0.95
        assert result.solver_name == "TextSolver"
        assert result.elapsed_ms == 42.5
        assert result.raw is None

    def test_construction_with_raw(self):
        result = CaptchaResult(
            solution="10",
            captcha_type="math",
            confidence=0.9,
            solver_name="MathSolver",
            elapsed_ms=10.0,
            raw={"ocr_text": "3 + 7"},
        )
        assert result.raw == {"ocr_text": "3 + 7"}

    def test_to_dict(self):
        result = CaptchaResult(
            solution="abc",
            captcha_type="text",
            confidence=0.85,
            solver_name="TextSolver",
            elapsed_ms=20.0,
        )
        d = result.to_dict()
        assert d == {
            "solution": "abc",
            "captcha_type": "text",
            "confidence": 0.85,
            "solver_name": "TextSolver",
            "elapsed_ms": 20.0,
        }

    def test_to_dict_excludes_raw(self):
        result = CaptchaResult(
            solution="x",
            captcha_type="text",
            confidence=0.5,
            solver_name="TestSolver",
            elapsed_ms=1.0,
            raw={"extra": "data"},
        )
        d = result.to_dict()
        assert "raw" not in d
