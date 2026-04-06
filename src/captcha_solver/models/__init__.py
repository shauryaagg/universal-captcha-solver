"""Model management and inference backends."""
from captcha_solver.models.backend import BoundingBox, ModelBackend
from captcha_solver.models.manager import ModelInfo, ModelManager

__all__ = ["BoundingBox", "ModelBackend", "ModelInfo", "ModelManager"]
