"""Tests for captcha_solver.cli.app."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from captcha_solver.cli.app import app
from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType

runner = CliRunner()


class TestCLIVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "captcha-solver" in result.output
        assert "0.1.0" in result.output

    def test_short_version_flag(self):
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCLIHelp:
    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Universal Captcha Solver" in result.output

    def test_solve_help(self):
        result = runner.invoke(app, ["solve", "--help"])
        assert result.exit_code == 0
        assert "image" in result.output.lower()

    def test_detect_help(self):
        result = runner.invoke(app, ["detect", "--help"])
        assert result.exit_code == 0


class TestCLIModels:
    def test_models_list(self):
        result = runner.invoke(app, ["models", "list"])
        assert result.exit_code == 0
        assert "text-ocr-v1" in result.output


class TestCLISolve:
    def test_solve_file_not_found(self):
        result = runner.invoke(app, ["solve", "/nonexistent/image.png"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_solve_with_fixture(self, tmp_image_file):
        mock_result = CaptchaResult(
            solution="abc123",
            captcha_type="text",
            confidence=0.9,
            solver_name="MockSolver",
            elapsed_ms=5.0,
        )
        with patch("captcha_solver.core.pipeline.SolverPipeline") as MockPipeline:
            MockPipeline.return_value.solve.return_value = mock_result
            result = runner.invoke(app, ["solve", str(tmp_image_file)])
            assert result.exit_code == 0
            assert "abc123" in result.output

    def test_solve_json_output(self, tmp_image_file):
        mock_result = CaptchaResult(
            solution="abc123",
            captcha_type="text",
            confidence=0.9,
            solver_name="MockSolver",
            elapsed_ms=5.0,
        )
        with patch("captcha_solver.core.pipeline.SolverPipeline") as MockPipeline:
            MockPipeline.return_value.solve.return_value = mock_result
            result = runner.invoke(app, ["solve", str(tmp_image_file), "--output", "json"])
            assert result.exit_code == 0
            assert '"solution"' in result.output


class TestCLIDetect:
    def test_detect_file_not_found(self):
        result = runner.invoke(app, ["detect", "/nonexistent/image.png"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_detect_with_fixture(self, tmp_image_file):
        with patch("captcha_solver.core.pipeline.get_default_pipeline") as mock_get:
            mock_pipeline = MagicMock()
            mock_pipeline.detect.return_value = (CaptchaType.TEXT, 0.75)
            mock_get.return_value = mock_pipeline
            result = runner.invoke(app, ["detect", str(tmp_image_file)])
            assert result.exit_code == 0
            assert "text" in result.output.lower()
