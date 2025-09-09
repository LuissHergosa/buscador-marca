"""
Main FastAPI application for the Document Brand Detection System.
"""

import asyncio
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config import settings
from .api import documents_router, health_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    # Include routers with no request body limits for unlimited file uploads
    app.include_router(health_router)
    app.include_router(
        documents_router,
        # No request body limits for unlimited file uploads
        dependencies=[]
    )
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        logger.error(f"Global exception handler caught: {str(exc)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal server error: {str(exc)}"}
        )
    
    # Startup event to configure asyncio
    @app.on_event("startup")
    async def startup_event():
        logger.info("Application starting up...")
        # Configure asyncio to handle unhandled exceptions gracefully
        loop = asyncio.get_event_loop()
        
        def handle_exception(loop, context):
            logger.error(f"Unhandled exception in event loop: {context}")
            # Don't let unhandled exceptions crash the application
            logger.error("Exception handled gracefully, application will continue running")
        
        loop.set_exception_handler(handle_exception)
        logger.info("Application startup completed")
    
    # Shutdown event for cleanup
    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Application shutting down...")
        # Don't try to cancel tasks manually - let uvicorn handle it
        # This prevents recursion errors during shutdown
        logger.info("Application shutdown completed")
    
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
        # No limits for unlimited processing
        limit_concurrency=0,  # No concurrency limit
        limit_max_requests=0,  # No request limit
        timeout_keep_alive=0,  # No keep-alive timeout
        timeout_graceful_shutdown=0  # No graceful shutdown timeout
    )
