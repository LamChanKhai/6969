"""FastAPI app factory and middleware setup."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import init_db, close_db
from app.api.v1.endpoints import router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    await init_db()
    yield
    await close_db()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CSCV2025 Secure Platform API",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix="/api/v1")
    return app


app = create_app()
