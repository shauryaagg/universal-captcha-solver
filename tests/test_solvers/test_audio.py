"""Tests for captcha_solver.solvers.audio.AudioSolver."""

from unittest.mock import MagicMock

import pytest

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.audio import AudioSolver
from captcha_solver.solvers.base import CaptchaType, SolverInput


class TestAudioSolver:
    def test_captcha_type(self):
        solver = AudioSolver()
        assert solver.captcha_type == CaptchaType.AUDIO

    def test_name(self):
        solver = AudioSolver()
        assert solver.name == "AudioSolver"

    def test_can_solve_with_audio(self):
        solver = AudioSolver()
        inp = SolverInput(audio=b"fake-audio-data")
        assert solver.can_solve(inp) is True

    def test_can_solve_without_audio(self):
        solver = AudioSolver()
        inp = SolverInput()
        assert solver.can_solve(inp) is False

    def test_can_solve_with_image_only(self):
        solver = AudioSolver()
        inp = SolverInput(image=b"fake-image-data")
        assert solver.can_solve(inp) is False

    def test_solve_with_mock_backend(self):
        mock_backend = MagicMock()
        mock_backend.transcribe_audio.return_value = "12345"

        solver = AudioSolver(backend=mock_backend)
        inp = SolverInput(audio=b"fake-audio-data")
        result = solver.solve(inp)

        assert isinstance(result, CaptchaResult)
        assert result.solution == "12345"
        assert result.captcha_type == "audio"
        assert result.confidence == 0.80
        assert result.solver_name == "AudioSolver"
        assert result.elapsed_ms > 0
        mock_backend.transcribe_audio.assert_called_once_with(b"fake-audio-data")

    def test_solve_cleans_transcription(self):
        mock_backend = MagicMock()
        mock_backend.transcribe_audio.return_value = "  Hello, World.  "

        solver = AudioSolver(backend=mock_backend)
        inp = SolverInput(audio=b"fake-audio-data")
        result = solver.solve(inp)

        assert result.solution == "hello world"

    def test_solve_strips_punctuation(self):
        mock_backend = MagicMock()
        mock_backend.transcribe_audio.return_value = "1, 2, 3."

        solver = AudioSolver(backend=mock_backend)
        inp = SolverInput(audio=b"fake-audio-data")
        result = solver.solve(inp)

        assert result.solution == "1 2 3"

    def test_solve_requires_audio(self):
        mock_backend = MagicMock()
        solver = AudioSolver(backend=mock_backend)
        inp = SolverInput()

        with pytest.raises(ValueError, match="requires audio input"):
            solver.solve(inp)
