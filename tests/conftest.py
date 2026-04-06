"""Shared pytest fixtures for captcha_solver tests."""

import io

import numpy as np
import pytest
from PIL import Image, ImageDraw


@pytest.fixture
def sample_text_image() -> bytes:
    """Generate a simple text captcha image."""
    img = Image.new("RGB", (200, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 20), "abc123", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_math_image() -> bytes:
    """Generate a math captcha image: 3 + 7"""
    img = Image.new("RGB", (200, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((30, 20), "3 + 7", fill=(0, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_slider_image() -> bytes:
    """Generate a slider captcha image (wide with a gap)."""
    img = Image.new("RGB", (400, 100), color=(200, 200, 200))
    draw = ImageDraw.Draw(img)
    # Draw a dark region as the "gap"
    draw.rectangle([250, 10, 290, 90], fill=(50, 50, 50), outline=(0, 0, 0), width=3)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_square_image() -> bytes:
    """Generate a square image with many colours (simulates grid/photo captcha)."""
    rng = np.random.default_rng(42)
    arr = rng.integers(0, 256, size=(300, 300, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_geetest_image() -> bytes:
    """Generate a GeeTest-like image: wide, colourful, high edge density."""
    rng = np.random.default_rng(99)
    arr = rng.integers(0, 256, size=(200, 300, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def tmp_image_file(sample_text_image: bytes, tmp_path):
    """Write sample image to a temp file and return path."""
    path = tmp_path / "test_captcha.png"
    path.write_bytes(sample_text_image)
    return path
