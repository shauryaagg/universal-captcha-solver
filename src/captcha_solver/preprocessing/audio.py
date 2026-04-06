"""Audio preprocessing for audio captcha solving. Full implementation in Phase 3."""
from __future__ import annotations


def normalize_audio(audio_bytes: bytes) -> bytes:
    """Normalize audio volume. Requires [audio] extra."""
    raise NotImplementedError(
        "Audio preprocessing requires: pip install universal-captcha-solver[audio]"
    )


def reduce_noise(audio_bytes: bytes) -> bytes:
    """Reduce background noise. Requires [audio] extra."""
    raise NotImplementedError(
        "Audio preprocessing requires: pip install universal-captcha-solver[audio]"
    )
