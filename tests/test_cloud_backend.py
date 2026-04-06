"""Tests for captcha_solver.models.cloud_backend.CloudBackend."""

import base64
from unittest.mock import MagicMock, patch

import pytest

from captcha_solver.models.backend import BoundingBox
from captcha_solver.models.cloud_backend import CloudBackend


# --- PNG header bytes for test images ---
PNG_HEADER = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
JPEG_HEADER = b"\xff\xd8\xff\xe0" + b"\x00" * 100
GIF_HEADER = b"GIF89a" + b"\x00" * 100
WEBP_HEADER = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100


class TestEncodeImage:
    def test_encode_roundtrip(self):
        backend = CloudBackend()
        data = b"hello world"
        encoded = backend._encode_image(data)
        assert base64.b64decode(encoded) == data

    def test_encode_empty(self):
        backend = CloudBackend()
        encoded = backend._encode_image(b"")
        assert encoded == ""

    def test_encode_binary(self):
        backend = CloudBackend()
        data = bytes(range(256))
        encoded = backend._encode_image(data)
        assert base64.b64decode(encoded) == data


class TestDetectMediaType:
    def test_png(self):
        backend = CloudBackend()
        assert backend._detect_media_type(PNG_HEADER) == "image/png"

    def test_jpeg(self):
        backend = CloudBackend()
        assert backend._detect_media_type(JPEG_HEADER) == "image/jpeg"

    def test_gif(self):
        backend = CloudBackend()
        assert backend._detect_media_type(GIF_HEADER) == "image/gif"

    def test_webp(self):
        backend = CloudBackend()
        assert backend._detect_media_type(WEBP_HEADER) == "image/webp"

    def test_unknown_defaults_to_png(self):
        backend = CloudBackend()
        assert backend._detect_media_type(b"\x00\x00\x00\x00") == "image/png"


class TestDefaultModel:
    def test_anthropic_default(self):
        backend = CloudBackend(provider="anthropic")
        assert backend.model == "claude-sonnet-4-20250514"

    def test_openai_default(self):
        backend = CloudBackend(provider="openai")
        assert backend.model == "gpt-4o"

    def test_custom_model(self):
        backend = CloudBackend(provider="anthropic", model="claude-opus-4-20250514")
        assert backend.model == "claude-opus-4-20250514"

    def test_unknown_provider_defaults_to_claude(self):
        backend = CloudBackend(provider="other")
        assert backend.model == "claude-sonnet-4-20250514"


class TestOcrWithMockedAnthropic:
    @patch("captcha_solver.models.cloud_backend.anthropic", create=True)
    def test_ocr_anthropic(self, mock_anthropic_module):
        """Test OCR via mocked Anthropic client."""
        # Set up mock
        mock_client = MagicMock()
        mock_message = MagicMock()
        mock_content_block = MagicMock()
        mock_content_block.text = "  abc123  "
        mock_message.content = [mock_content_block]
        mock_client.messages.create.return_value = mock_message

        with patch.dict("sys.modules", {"anthropic": MagicMock()}):
            backend = CloudBackend(provider="anthropic", api_key="test-key")
            # Directly patch the internal method to avoid import issues
            with patch.object(backend, "_call_anthropic", return_value="abc123") as mock_call:
                result = backend.ocr(PNG_HEADER)
                assert result == "abc123"
                mock_call.assert_called_once()

    @patch("captcha_solver.models.cloud_backend.openai", create=True)
    def test_ocr_openai(self, mock_openai_module):
        """Test OCR via mocked OpenAI client."""
        backend = CloudBackend(provider="openai", api_key="test-key")
        with patch.object(backend, "_call_openai", return_value="xyz789") as mock_call:
            result = backend.ocr(PNG_HEADER)
            assert result == "xyz789"
            mock_call.assert_called_once()


class TestClassifyImage:
    def test_classify_with_labels(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="cat") as mock_call:
            result = backend.classify_image(PNG_HEADER, labels=["cat", "dog", "bird"])
            assert result == "cat"
            call_args = mock_call.call_args
            assert "cat, dog, bird" in call_args[0][1]

    def test_classify_without_labels(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="red car") as mock_call:
            result = backend.classify_image(PNG_HEADER)
            assert result == "red car"
            mock_call.assert_called_once()


class TestDetectObjects:
    def test_detect_objects_valid_json(self):
        backend = CloudBackend(provider="anthropic")
        json_response = (
            '[{"x": 10, "y": 20, "width": 50, "height": 60, "label": "car"},'
            ' {"x": 100, "y": 110, "width": 30, "height": 40, "label": "tree"}]'
        )
        with patch.object(backend, "_call_vision", return_value=json_response):
            result = backend.detect_objects(PNG_HEADER)
            assert len(result) == 2
            assert isinstance(result[0], BoundingBox)
            assert result[0].label == "car"
            assert result[0].x == 10.0
            assert result[1].label == "tree"

    def test_detect_objects_json_with_extra_text(self):
        backend = CloudBackend(provider="anthropic")
        response = 'Here are the objects: [{"x": 5, "y": 5, "width": 10, "height": 10, "label": "box"}] found'
        with patch.object(backend, "_call_vision", return_value=response):
            result = backend.detect_objects(PNG_HEADER)
            assert len(result) == 1
            assert result[0].label == "box"

    def test_detect_objects_invalid_json(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="no objects found"):
            result = backend.detect_objects(PNG_HEADER)
            assert result == []

    def test_detect_objects_empty_array(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="[]"):
            result = backend.detect_objects(PNG_HEADER)
            assert result == []


class TestSolveGridCaptcha:
    def test_parse_comma_separated(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="1,4,7"):
            result = backend.solve_grid_captcha(PNG_HEADER, "Select traffic lights")
            assert result == [1, 4, 7]

    def test_parse_with_spaces(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="2, 5, 8"):
            result = backend.solve_grid_captcha(PNG_HEADER, "Select bicycles")
            assert result == [2, 5, 8]

    def test_filters_out_of_range(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="0,1,10,3"):
            result = backend.solve_grid_captcha(PNG_HEADER, "Select cars")
            assert result == [1, 3]  # 0 and 10 are out of range for 3x3

    def test_handles_non_numeric(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="1,abc,3"):
            result = backend.solve_grid_captcha(PNG_HEADER, "Select buses")
            assert result == [1, 3]

    def test_custom_grid_size(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value="1,8,16"):
            result = backend.solve_grid_captcha(
                PNG_HEADER, "Select crosswalks", grid_size=(4, 4)
            )
            assert result == [1, 8, 16]

    def test_empty_response(self):
        backend = CloudBackend(provider="anthropic")
        with patch.object(backend, "_call_vision", return_value=""):
            result = backend.solve_grid_captcha(PNG_HEADER, "Select fire hydrants")
            assert result == []


class TestAnswerTextChallenge:
    def test_anthropic_text_challenge(self):
        backend = CloudBackend(provider="anthropic", api_key="test-key")
        with patch.object(backend, "answer_text_challenge", return_value="blue"):
            result = backend.answer_text_challenge("What color is the sky?")
            assert result == "blue"

    def test_openai_text_challenge(self):
        backend = CloudBackend(provider="openai", api_key="test-key")
        with patch.object(backend, "answer_text_challenge", return_value="4"):
            result = backend.answer_text_challenge("What is 2+2?")
            assert result == "4"

    def test_unknown_provider_raises(self):
        backend = CloudBackend(provider="unknown", api_key="test-key")
        with pytest.raises(ValueError, match="Unknown provider"):
            backend.answer_text_challenge("test question")


class TestCallVision:
    def test_unknown_provider_raises(self):
        backend = CloudBackend(provider="unknown")
        with pytest.raises(ValueError, match="Unknown provider"):
            backend._call_vision(PNG_HEADER, "test prompt")


class TestTranscribeAudio:
    def test_anthropic_raises_not_implemented(self):
        backend = CloudBackend(provider="anthropic")
        with pytest.raises(NotImplementedError, match="not supported"):
            backend.transcribe_audio(b"audio data")
