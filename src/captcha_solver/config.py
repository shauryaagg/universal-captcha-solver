"""Configuration via pydantic-settings."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CAPTCHA_SOLVER_",
        env_file=".env",
    )

    model_backend: Literal["local", "cloud"] = "local"
    model_dir: str = "~/.cache/captcha-solver/models"
    gpu_enabled: bool = False

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    cloud_provider: Literal["openai", "anthropic"] = "openai"

    min_confidence: float = 0.7
    max_retries: int = 2
    timeout_seconds: float = 30.0

    server_host: str = "127.0.0.1"
    server_port: int = 8000

    log_level: str = "INFO"
