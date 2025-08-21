"""
Document management API endpoints.
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
import io

from ..models.document import Document, DocumentCreate, DocumentUpdate
from ..models.processing_status import ProcessingStatus
from ..services.processing_service import processing_service
from ..services.firebase_service import firebase_service
from ..config import settings

router = APIRouter(prefix="/api/documents", tags=["documents"])


def validate_file_size(file_size: int) -> None:
    """Validate file size."""
    if file_size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size // (1024*1024)}MB"
        )


def validate_file_extension(filename: str) -> None:
    """Validate file extension."""
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.allowed_extensions)}"
        )


@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...)
) -> Document:
    """
    Upload a PDF document for brand detection analysis.
    
    Args:
        file: PDF file to upload
        
    Returns:
        Document object with processing status
    """
    try:
        # Validate file
        validate_file_extension(file.filename)
        
        # Read file content
        file_content = await file.read()
        validate_file_size(len(file_content))
        
        # Process document
        document = await processing_service.process_document(
            file_content, file.filename
        )
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=List[Document])
async def get_documents() -> List[Document]:
    """
    Get all documents.
    
    Returns:
        List of all documents
    """
    try:
        documents = await firebase_service.get_all_documents()
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get documents: {str(e)}")


@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str) -> Document:
    """
    Get a specific document by ID.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document object
    """
    try:
        document = await firebase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> dict:
    """
    Delete a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Success message
    """
    try:
        success = await firebase_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/{document_id}/status", response_model=ProcessingStatus)
async def get_document_status(document_id: str) -> ProcessingStatus:
    """
    Get processing status for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Processing status object
    """
    try:
        status = await processing_service.get_processing_status(document_id)
        if not status:
            raise HTTPException(status_code=404, detail="Document not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/{document_id}/cancel")
async def cancel_processing(document_id: str) -> dict:
    """
    Cancel processing for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Success message
    """
    try:
        success = await processing_service.cancel_processing(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"message": "Processing cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel processing: {str(e)}")


@router.get("/{document_id}/results")
async def get_document_results(document_id: str) -> dict:
    """
    Get brand detection results for a document.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document with results
    """
    try:
        document = await firebase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {
            "document_id": document.id,
            "filename": document.filename,
            "status": document.status,
            "total_pages": document.total_pages,
            "results": document.results or []
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.get("/active/processes")
async def get_active_processes() -> dict:
    """
    Get information about currently active processing tasks.
    
    Returns:
        Dictionary with active process information
    """
    try:
        active_processes = await processing_service.get_active_processes()
        return {
            "active_processes": active_processes,
            "count": len(active_processes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active processes: {str(e)}")
