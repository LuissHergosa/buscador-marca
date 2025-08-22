"""
Brand detection models for the Document Brand Detection System.
"""

from typing import List, Dict
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
    brands_review_status: Dict[str, bool] = Field(
        default_factory=dict, 
        description="Review status for each detected brand (brand_name: is_reviewed)"
    )
    
    class Config:
        from_attributes = True


class BrandReviewUpdate(BaseModel):
    """Model for updating brand review status."""
    document_id: str = Field(..., description="Document ID")
    page_number: int = Field(..., description="Page number")
    brand_name: str = Field(..., description="Brand name to update")
    is_reviewed: bool = Field(..., description="Whether the brand has been reviewed")
