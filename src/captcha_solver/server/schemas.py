"""Pydantic request/response models for the REST API."""
from __future__ import annotations

from pydantic import BaseModel


class SolveResponse(BaseModel):
    solution: str
    captcha_type: str
    confidence: float
    elapsed_ms: float
    solver_name: str = ""


class DetectResponse(BaseModel):
    captcha_type: str
    confidence: float


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    gpu_available: bool
    solvers: list[str]


class SolverInfo(BaseModel):
    name: str
    captcha_type: str


class SolversResponse(BaseModel):
    solvers: list[SolverInfo]


class ErrorResponse(BaseModel):
    error: str
    detail: str = ""
