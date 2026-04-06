"""Model lifecycle management."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelInfo:
    name: str
    filename: str
    url: str
    size_bytes: int
    sha256: str
    description: str = ""


# Phase 1: hardcoded manifest. Models will be hosted on GitHub Releases later.
MODEL_MANIFEST: dict[str, ModelInfo] = {
    "text-ocr-v1": ModelInfo(
        name="text-ocr-v1",
        filename="text_ocr_v1.onnx",
        url="",  # To be populated when models are hosted
        size_bytes=12_000_000,
        sha256="",
        description="Text captcha OCR model",
    ),
    "classifier-v1": ModelInfo(
        name="classifier-v1",
        filename="classifier_v1.onnx",
        url="",
        size_bytes=8_000_000,
        sha256="",
        description="Captcha type classifier",
    ),
}


class ModelManager:
    def __init__(self, model_dir: str = "~/.cache/captcha-solver/models"):
        self.model_dir = Path(model_dir).expanduser()
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def get_model_path(self, name: str) -> Path:
        """Return local path for model, downloading if needed."""
        info = MODEL_MANIFEST.get(name)
        if info is None:
            raise ValueError(
                f"Unknown model: {name}. Available: {list(MODEL_MANIFEST.keys())}"
            )

        path = self.model_dir / info.filename
        if not path.exists():
            if not info.url:
                raise FileNotFoundError(
                    f"Model '{name}' not found at {path} and no download URL configured. "
                    f"Place the model file manually or wait for model hosting setup."
                )
            self.download_model(name)
        return path

    def download_model(self, name: str) -> Path:
        """Download model from URL."""
        info = MODEL_MANIFEST.get(name)
        if info is None:
            raise ValueError(f"Unknown model: {name}")
        if not info.url:
            raise ValueError(
                f"No download URL for model '{name}'. Model hosting not yet configured."
            )

        import httpx

        path = self.model_dir / info.filename
        print(f"Downloading {name} ({info.size_bytes / 1_000_000:.1f}MB)...")

        with httpx.stream("GET", info.url, follow_redirects=True) as response:
            response.raise_for_status()
            with open(path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)

        if info.sha256:
            self.verify_checksum(path, info.sha256)

        print(f"Downloaded {name} to {path}")
        return path

    def verify_checksum(self, path: Path, expected_sha256: str) -> bool:
        """Verify SHA-256 checksum of a downloaded model file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        actual = sha256.hexdigest()
        if actual != expected_sha256:
            path.unlink()  # Remove corrupted download
            raise ValueError(
                f"Checksum mismatch for {path.name}: "
                f"expected {expected_sha256}, got {actual}"
            )
        return True

    def list_available(self) -> list[ModelInfo]:
        """List all models in the manifest."""
        return list(MODEL_MANIFEST.values())

    def list_downloaded(self) -> list[ModelInfo]:
        """List models that have been downloaded locally."""
        return [
            info
            for info in MODEL_MANIFEST.values()
            if (self.model_dir / info.filename).exists()
        ]
