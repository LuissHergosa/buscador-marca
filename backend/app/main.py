"""
Main FastAPI application for the Document Brand Detection System.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings
from .api import documents_router, health_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Document Brand Detection System - API for analyzing PDF documents to detect brand names using AI",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers with increased request body limits for heavy files
    app.include_router(health_router)
    app.include_router(
        documents_router,
        # Increase request body limit for heavy PDF files
        dependencies=[]
    )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )
    
    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Document Brand Detection System API",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health"
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info",
        # Increase limits for heavy file processing
        limit_concurrency=1000,
        limit_max_requests=10000,
        timeout_keep_alive=300,
        timeout_graceful_shutdown=300
    )
