"""Image preprocessing for captcha solving."""
from __future__ import annotations

import io

import numpy as np
from PIL import Image


def load_image(image_bytes: bytes) -> Image.Image:
    """Load image from bytes."""
    return Image.open(io.BytesIO(image_bytes))


def to_grayscale(image_bytes: bytes) -> bytes:
    """Convert image to grayscale."""
    img = load_image(image_bytes)
    gray = img.convert("L")
    buf = io.BytesIO()
    gray.save(buf, format="PNG")
    return buf.getvalue()


def threshold(image_bytes: bytes, value: int = 128) -> bytes:
    """Apply binary threshold to image."""
    img = load_image(image_bytes).convert("L")
    arr = np.array(img)
    arr = ((arr > value) * 255).astype(np.uint8)
    result = Image.fromarray(arr)
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()


def denoise(image_bytes: bytes, radius: int = 1) -> bytes:
    """Simple denoise via median filter."""
    from PIL import ImageFilter

    img = load_image(image_bytes)
    filtered = img.filter(ImageFilter.MedianFilter(size=radius * 2 + 1))
    buf = io.BytesIO()
    filtered.save(buf, format="PNG")
    return buf.getvalue()


def resize(image_bytes: bytes, width: int, height: int) -> bytes:
    """Resize image to given dimensions."""
    img = load_image(image_bytes)
    resized = img.resize((width, height), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    resized.save(buf, format="PNG")
    return buf.getvalue()


def normalize_for_model(
    image_bytes: bytes, target_size: tuple[int, int] = (128, 64)
) -> np.ndarray:
    """Convert image to normalized float array for model input.

    Returns shape: (1, 1, height, width) -- batch, channel, H, W.
    """
    img = load_image(image_bytes).convert("L")
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return arr.reshape(1, 1, target_size[1], target_size[0])
