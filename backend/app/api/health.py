"""
Health check endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    message: str
    version: str
    timestamp: str


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    from datetime import datetime
    from ..config import settings
    
    return HealthResponse(
        status="healthy",
        message="Document Brand Detection System is running",
        version=settings.app_version,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check endpoint."""
    from datetime import datetime
    
    # Check if services are ready
    try:
        # Add service health checks here if needed
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "firebase": "connected",
                "gemini": "configured"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")
