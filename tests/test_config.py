"""Tests for captcha_solver.config.Settings."""

from captcha_solver.config import Settings


class TestSettings:
    def test_default_values(self):
        settings = Settings()
        assert settings.model_backend == "local"
        assert settings.gpu_enabled is False
        assert settings.min_confidence == 0.7
        assert settings.max_retries == 2
        assert settings.timeout_seconds == 30.0
        assert settings.server_host == "127.0.0.1"
        assert settings.server_port == 8000
        assert settings.log_level == "INFO"
        assert settings.cloud_provider == "openai"
        assert settings.openai_api_key is None
        assert settings.anthropic_api_key is None

    def test_instantiation(self):
        s = Settings()
        assert isinstance(s, Settings)

    def test_env_var_override(self, monkeypatch):
        monkeypatch.setenv("CAPTCHA_SOLVER_GPU_ENABLED", "true")
        monkeypatch.setenv("CAPTCHA_SOLVER_MIN_CONFIDENCE", "0.9")
        monkeypatch.setenv("CAPTCHA_SOLVER_LOG_LEVEL", "DEBUG")
        settings = Settings()
        assert settings.gpu_enabled is True
        assert settings.min_confidence == 0.9
        assert settings.log_level == "DEBUG"

    def test_model_dir_default(self):
        settings = Settings()
        assert "captcha-solver" in settings.model_dir

    def test_custom_settings_kwargs(self):
        settings = Settings(model_backend="cloud", server_port=9000)
        assert settings.model_backend == "cloud"
        assert settings.server_port == 9000
