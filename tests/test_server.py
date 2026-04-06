"""Tests for captcha_solver.server REST API."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from captcha_solver.core.result import CaptchaResult
from captcha_solver.solvers.base import CaptchaType


@pytest.fixture
def client():
    """Create a test client with mocked pipeline."""
    # Reset the singleton pipeline before each test
    import captcha_solver.core.pipeline as pipeline_mod

    pipeline_mod._default_pipeline = None

    # Build a mock pipeline
    mock_pipeline = MagicMock()
    mock_pipeline.registry = MagicMock()
    mock_pipeline.registry.list_types.return_value = [CaptchaType.TEXT, CaptchaType.SLIDER]
    mock_pipeline.registry.get_all_solvers.return_value = []

    mock_result = CaptchaResult(
        solution="mocked",
        captcha_type="text",
        confidence=0.9,
        solver_name="MockSolver",
        elapsed_ms=5.0,
    )

    mock_pipeline.asolve = AsyncMock(return_value=mock_result)
    mock_pipeline.detect.return_value = (CaptchaType.TEXT, 0.75)

    with patch("captcha_solver.core.pipeline.get_default_pipeline", return_value=mock_pipeline):
        from captcha_solver.server.app import app

        yield TestClient(app, raise_server_exceptions=False)

    # Cleanup singleton
    pipeline_mod._default_pipeline = None


class TestSolveEndpoint:
    def test_solve_with_file(self, client, sample_text_image: bytes):
        response = client.post(
            "/solve",
            files={"image": ("captcha.png", io.BytesIO(sample_text_image), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["solution"] == "mocked"
        assert data["captcha_type"] == "text"
        assert "confidence" in data
        assert "elapsed_ms" in data

    def test_solve_with_captcha_type(self, client, sample_text_image: bytes):
        response = client.post(
            "/solve",
            files={"image": ("captcha.png", io.BytesIO(sample_text_image), "image/png")},
            data={"captcha_type": "text"},
        )
        assert response.status_code == 200

    def test_solve_empty_file(self, client):
        response = client.post(
            "/solve",
            files={"image": ("empty.png", io.BytesIO(b""), "image/png")},
        )
        assert response.status_code == 400


class TestDetectEndpoint:
    def test_detect_with_file(self, client, sample_text_image: bytes):
        response = client.post(
            "/detect",
            files={"image": ("captcha.png", io.BytesIO(sample_text_image), "image/png")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["captcha_type"] == "text"
        assert "confidence" in data

    def test_detect_empty_file(self, client):
        response = client.post(
            "/detect",
            files={"image": ("empty.png", io.BytesIO(b""), "image/png")},
        )
        assert response.status_code == 400


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "solvers" in data


class TestSolversEndpoint:
    def test_solvers(self, client):
        response = client.get("/solvers")
        assert response.status_code == 200
        data = response.json()
        assert "solvers" in data
        assert isinstance(data["solvers"], list)
