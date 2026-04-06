"""Tests for captcha_solver.preprocessing.image."""

import io

import numpy as np
from PIL import Image

from captcha_solver.preprocessing.image import (
    denoise,
    load_image,
    normalize_for_model,
    resize,
    threshold,
    to_grayscale,
)


class TestLoadImage:
    def test_load_image(self, sample_text_image: bytes):
        img = load_image(sample_text_image)
        assert isinstance(img, Image.Image)
        assert img.size == (200, 80)

    def test_load_image_mode(self, sample_text_image: bytes):
        img = load_image(sample_text_image)
        assert img.mode == "RGB"


class TestToGrayscale:
    def test_output_is_grayscale(self, sample_text_image: bytes):
        result = to_grayscale(sample_text_image)
        img = Image.open(io.BytesIO(result))
        assert img.mode == "L"

    def test_output_is_bytes(self, sample_text_image: bytes):
        result = to_grayscale(sample_text_image)
        assert isinstance(result, bytes)

    def test_dimensions_preserved(self, sample_text_image: bytes):
        result = to_grayscale(sample_text_image)
        img = Image.open(io.BytesIO(result))
        assert img.size == (200, 80)


class TestThreshold:
    def test_output_is_binary(self, sample_text_image: bytes):
        result = threshold(sample_text_image, value=128)
        img = Image.open(io.BytesIO(result))
        arr = np.array(img)
        unique_values = set(np.unique(arr))
        assert unique_values <= {0, 255}

    def test_output_is_bytes(self, sample_text_image: bytes):
        result = threshold(sample_text_image)
        assert isinstance(result, bytes)


class TestDenoise:
    def test_output_is_valid_image(self, sample_text_image: bytes):
        result = denoise(sample_text_image)
        img = Image.open(io.BytesIO(result))
        assert img.size == (200, 80)

    def test_output_is_bytes(self, sample_text_image: bytes):
        result = denoise(sample_text_image)
        assert isinstance(result, bytes)


class TestResize:
    def test_output_dimensions(self, sample_text_image: bytes):
        result = resize(sample_text_image, width=100, height=40)
        img = Image.open(io.BytesIO(result))
        assert img.size == (100, 40)

    def test_output_is_bytes(self, sample_text_image: bytes):
        result = resize(sample_text_image, width=50, height=25)
        assert isinstance(result, bytes)


class TestNormalizeForModel:
    def test_output_shape(self, sample_text_image: bytes):
        arr = normalize_for_model(sample_text_image, target_size=(128, 64))
        # Expected shape: (1, 1, height, width) = (1, 1, 64, 128)
        assert arr.shape == (1, 1, 64, 128)

    def test_output_dtype(self, sample_text_image: bytes):
        arr = normalize_for_model(sample_text_image)
        assert arr.dtype == np.float32

    def test_output_range(self, sample_text_image: bytes):
        arr = normalize_for_model(sample_text_image)
        assert arr.min() >= 0.0
        assert arr.max() <= 1.0

    def test_custom_target_size(self, sample_text_image: bytes):
        arr = normalize_for_model(sample_text_image, target_size=(64, 32))
        assert arr.shape == (1, 1, 32, 64)
