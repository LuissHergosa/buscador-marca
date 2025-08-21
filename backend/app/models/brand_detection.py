"""
Brand detection models for the Document Brand Detection System.
"""

from typing import List
from pydantic import BaseModel, Field


class BrandDetectionBase(BaseModel):
    """Base brand detection model."""
    page_number: int = Field(..., description="Page number in the document")
    brands_detected: List[str] = Field(..., description="List of detected brand names")


class BrandDetectionCreate(BrandDetectionBase):
    """Model for creating a new brand detection result."""
    pass


class BrandDetection(BrandDetectionBase):
    """Complete brand detection model."""
    processing_time: float = Field(..., description="Time taken to process this page (seconds)")
    status: str = Field(..., description="Processing status: pending, processing, completed, failed")
    
    class Config:
        from_attributes = True
