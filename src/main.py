"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.analyzer_routes import router as analyzer_router
from src.api.dependencies import get_feedback_analyzer
from src.api.routes import router
from src.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Resume Analysis API",
    description="공기업 자기소개서 AI 분석 API",
    version=settings.app_version,
    docs_url="/docs" if settings.debug or settings.app_env == "development" else None,
    redoc_url="/redoc" if settings.debug or settings.app_env == "development" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)
app.include_router(analyzer_router)


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint.

    Returns:
        Health status and version
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


# Re-export for dependency injection in tests
__all__ = ["app", "get_feedback_analyzer"]
