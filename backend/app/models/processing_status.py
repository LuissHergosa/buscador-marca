"""
Processing status models for the Document Brand Detection System.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ProcessingStatus(BaseModel):
    """Model for tracking document processing status."""
    document_id: str = Field(..., description="Document identifier")
    status: str = Field(..., description="Overall status: processing, completed, failed")
    total_pages: int = Field(..., description="Total number of pages to process")
    processed_pages: int = Field(..., description="Number of pages already processed")
    failed_pages: int = Field(..., description="Number of pages that failed processing")
    progress_percentage: float = Field(..., description="Processing progress as percentage")
    page_status: Dict[int, str] = Field(..., description="Status of each page")
    estimated_time_remaining: Optional[float] = Field(default=None, description="Estimated time remaining in seconds")
    
    class Config:
        from_attributes = True


class PageStatus(BaseModel):
    """Model for individual page processing status."""
    page_number: int = Field(..., description="Page number")
    status: str = Field(..., description="Page status: pending, processing, completed, failed")
    processing_time: Optional[float] = Field(default=None, description="Time taken to process this page")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")
