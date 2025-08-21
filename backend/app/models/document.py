"""
Document models for the Document Brand Detection System.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document model."""
    filename: str = Field(..., description="Name of the uploaded file")
    total_pages: int = Field(..., description="Total number of pages in the document")


class DocumentCreate(DocumentBase):
    """Model for creating a new document."""
    pass


class DocumentUpdate(BaseModel):
    """Model for updating a document."""
    filename: Optional[str] = None
    status: Optional[str] = None


class Document(DocumentBase):
    """Complete document model."""
    id: str = Field(..., description="Unique document identifier")
    upload_date: datetime = Field(..., description="Date when document was uploaded")
    status: str = Field(..., description="Processing status: processing, completed, failed")
    results: Optional[List["BrandDetection"]] = Field(default=None, description="Brand detection results")
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Import here to avoid circular imports
from .brand_detection import BrandDetection

# Update forward references
Document.model_rebuild()
