"""FastAPI application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from captcha_solver.server.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize pipeline on startup."""
    from captcha_solver.core.pipeline import get_default_pipeline

    get_default_pipeline()  # Warm up the pipeline
    yield


app = FastAPI(
    title="Universal Captcha Solver",
    description="Solve any captcha type via REST API.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
