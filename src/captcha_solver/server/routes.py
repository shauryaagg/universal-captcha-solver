"""API route handlers."""
from __future__ import annotations

import base64
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from captcha_solver.server.schemas import (
    DetectResponse,
    ErrorResponse,
    HealthResponse,
    SolverInfo,
    SolveResponse,
    SolversResponse,
)

router = APIRouter()


@router.post(
    "/solve",
    response_model=SolveResponse,
    responses={400: {"model": ErrorResponse}},
)
async def solve_captcha(
    image: UploadFile = File(..., description="Captcha image file"),
    captcha_type: Optional[str] = Form(None, description="Captcha type (auto-detect if omitted)"),
) -> SolveResponse:
    """Solve a captcha from an uploaded image."""
    from captcha_solver.core.pipeline import get_default_pipeline

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    try:
        pipeline = get_default_pipeline()
        result = await pipeline.asolve(image=image_bytes, captcha_type=captcha_type)
        return SolveResponse(
            solution=result.solution,
            captcha_type=result.captcha_type,
            confidence=result.confidence,
            elapsed_ms=result.elapsed_ms,
            solver_name=result.solver_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/solve/base64",
    response_model=SolveResponse,
    responses={400: {"model": ErrorResponse}},
)
async def solve_captcha_base64(
    image_base64: str = Form(..., description="Base64-encoded captcha image"),
    captcha_type: Optional[str] = Form(None, description="Captcha type"),
) -> SolveResponse:
    """Solve a captcha from a base64-encoded image."""
    from captcha_solver.core.pipeline import get_default_pipeline

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 encoding") from e

    try:
        pipeline = get_default_pipeline()
        result = await pipeline.asolve(image=image_bytes, captcha_type=captcha_type)
        return SolveResponse(
            solution=result.solution,
            captcha_type=result.captcha_type,
            confidence=result.confidence,
            elapsed_ms=result.elapsed_ms,
            solver_name=result.solver_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/detect",
    response_model=DetectResponse,
    responses={400: {"model": ErrorResponse}},
)
async def detect_captcha(
    image: UploadFile = File(..., description="Captcha image file"),
) -> DetectResponse:
    """Detect captcha type from an uploaded image."""
    from captcha_solver.core.pipeline import get_default_pipeline

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image file")

    try:
        pipeline = get_default_pipeline()
        captcha_type, confidence = pipeline.detect(image_bytes)
        return DetectResponse(captcha_type=captcha_type.value, confidence=confidence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    import captcha_solver
    from captcha_solver.core.pipeline import get_default_pipeline

    pipeline = get_default_pipeline()
    solver_types = [t.value for t in pipeline.registry.list_types()]

    gpu_available = False
    try:
        import onnxruntime as ort

        gpu_available = "CUDAExecutionProvider" in ort.get_available_providers()
    except ImportError:
        pass

    return HealthResponse(
        status="ok",
        version=captcha_solver.__version__,
        gpu_available=gpu_available,
        solvers=solver_types,
    )


@router.get("/solvers", response_model=SolversResponse)
async def list_solvers() -> SolversResponse:
    """List all registered solvers."""
    from captcha_solver.core.pipeline import get_default_pipeline

    pipeline = get_default_pipeline()
    solvers = []
    for ct in pipeline.registry.list_types():
        for solver in pipeline.registry.get_all_solvers(ct):
            solvers.append(SolverInfo(name=solver.name, captcha_type=ct.value))
    return SolversResponse(solvers=solvers)
