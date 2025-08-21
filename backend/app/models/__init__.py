"""
Data models for the Document Brand Detection System.
"""

from .document import Document, DocumentCreate, DocumentUpdate
from .brand_detection import BrandDetection, BrandDetectionCreate
from .processing_status import ProcessingStatus

__all__ = [
    "Document",
    "DocumentCreate", 
    "DocumentUpdate",
    "BrandDetection",
    "BrandDetectionCreate",
    "ProcessingStatus"
]
