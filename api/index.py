"""Vercel Serverless Function entry point for FastAPI."""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create a simple FastAPI app for Vercel
app = FastAPI(title="Resume Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "environment": "vercel"}


@app.get("/api/test")
async def test_endpoint():
    """Test endpoint."""
    return {"message": "API is working"}


# Import and mount the main routes
try:
    from src.api.routes import router
    from src.api.analyzer_routes import router as analyzer_router

    app.include_router(router)
    app.include_router(analyzer_router)
except Exception as e:
    @app.get("/api/error")
    async def error_info():
        return {"error": str(e)}
