"""
Document management API endpoints.
"""

import logging
import os
from typing import List
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
import asyncio

from ..models.document import Document, DocumentCreate, DocumentUpdate
from ..models.processing_status import ProcessingStatus
from ..models.brand_detection import BrandReviewUpdate
from ..services.processing_service import processing_service
from ..services.firebase_service import firebase_service
from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


def validate_file_size(file_size: int) -> None:
    """Validate file size."""
    logger.info(f"Validating file size: {file_size} bytes")
    # Skip validation if max_file_size is 0 (no limit)
    if settings.max_file_size > 0 and file_size > settings.max_file_size:
        logger.error(
            f"File too large: {file_size} bytes > {settings.max_file_size} bytes"
        )
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size // (1024 * 1024)}MB",
        )
    logger.info("File size validation passed")


def validate_file_extension(filename: str) -> None:
    """Validate file extension."""
    logger.info(f"Validating file extension: {filename}")
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in settings.allowed_extensions:
        logger.error(f"Invalid file extension: {file_ext}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.allowed_extensions)}",
        )
    logger.info(f"File extension validation passed: {file_ext}")


async def _process_document_safely(document_id: str, file_content: bytes, filename: str):
    """
    Safely process document with proper error handling to prevent application exit.
    
    Args:
        document_id: Document ID
        file_content: PDF file content
        filename: Original filename
    """
    try:
        logger.info(f"Starting safe async document processing: {document_id}")
        await processing_service.process_document_async(
            document_id, file_content, filename
        )
        logger.info(f"Safe async document processing completed successfully: {document_id}")
    except Exception as e:
        logger.error(f"Safe async document processing failed for {document_id}: {str(e)}")
        # Update document status to failed
        try:
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(status="failed")
            )
            logger.info(f"Document {document_id} status updated to 'failed'")
        except Exception as update_error:
            logger.error(f"Failed to update document {document_id} status: {str(update_error)}")


@router.post("/upload", response_model=Document)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
) -> Document:
    """
    Upload a PDF document for brand detection analysis.
    Returns immediately after starting processing.

    Args:
        file: PDF file to upload
        background_tasks: FastAPI background tasks

    Returns:
        Document object with processing status
    """
    try:
        logger.info(f"Starting file upload: {file.filename}")
        logger.info(f"File size: {file.size} bytes")
        logger.info(f"Content type: {file.content_type}")

        # Validate file
        logger.info("Validating file extension")
        validate_file_extension(file.filename)

        # Read file content
        logger.info("Reading file content")
        file_content = await file.read()
        logger.info(f"File content read: {len(file_content)} bytes")

        # Validate file size
        logger.info("Validating file size")
        validate_file_size(len(file_content))

        # Create document record immediately
        logger.info("Creating document record in Firebase")
        document_data = DocumentCreate(
            filename=file.filename,
            total_pages=0  # Will be updated during processing
        )
        document = await firebase_service.create_document(document_data)
        logger.info(f"Document created in Firebase: {document.id}")

        # Use FastAPI background tasks for safer async processing
        if background_tasks:
            logger.info("Starting async document processing with FastAPI background tasks")
            background_tasks.add_task(
                _process_document_safely, document.id, file_content, file.filename
            )
        else:
            # Fallback to manual task creation with proper error handling
            logger.info("Starting async document processing with manual task creation")
            task = asyncio.create_task(
                _process_document_safely(document.id, file_content, file.filename)
            )
            
            # Add simple error callback to prevent task exceptions from crashing the app
            def task_done_callback(task):
                if task.exception():
                    logger.error(f"Background task failed but won't crash the app: {task.exception()}")
            
            task.add_done_callback(task_done_callback)

        logger.info(f"Document upload initiated successfully: {document.id}")
        return document

    except HTTPException:
        logger.error("HTTP exception during upload")
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=List[Document])
async def get_documents() -> List[Document]:
    """
    Get all documents with improved error handling.

    Returns:
        List of all documents
    """
    try:
        logger.info("API: Getting all documents")
        documents = await firebase_service.get_all_documents()
        logger.info(f"API: Retrieved {len(documents)} documents successfully")
        return documents
    except Exception as e:
        logger.error(f"API: Failed to get documents: {str(e)}")
        # Return empty list instead of 500 error to prevent frontend issues
        logger.warning("API: Returning empty list due to error")
        return []


@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str) -> Document:
    """
    Get a specific document by ID with improved error handling.

    Args:
        document_id: Document ID

    Returns:
        Document object
    """
    try:
        logger.info(f"API: Getting document {document_id}")
        document = await firebase_service.get_document(document_id)
        if not document:
            logger.warning(f"API: Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        logger.info(f"API: Retrieved document {document_id} successfully")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Failed to get document {document_id}: {str(e)}")
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
        raise HTTPException(
            status_code=500, detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/{document_id}/results", response_model=Document)
async def get_document_results(document_id: str) -> Document:
    """
    Get document with full processing results for frontend display.

    Args:
        document_id: Document ID

    Returns:
        Document object with complete results
    """
    try:
        logger.info(f"API: Getting document results for {document_id}")
        document = await firebase_service.get_document(document_id)
        if not document:
            logger.warning(f"API: Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        logger.info(f"API: Retrieved document results for {document_id}: {len(document.results)} results")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Failed to get document results {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document results: {str(e)}")


@router.get("/{document_id}/summary")
async def get_document_summary(document_id: str) -> dict:
    """
    Get document processing summary with statistics.

    Args:
        document_id: Document ID

    Returns:
        Document summary with brand statistics
    """
    try:
        logger.info(f"API: Getting document summary for {document_id}")
        document = await firebase_service.get_document(document_id)
        if not document:
            logger.warning(f"API: Document not found: {document_id}")
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Return summary if available, otherwise generate basic summary from results
        if document.summary:
            logger.info(f"API: Retrieved saved summary for {document_id}")
            return {
                "document_id": document_id,
                "summary": document.summary,
                "status": document.status
            }
        else:
            # Generate basic summary from results
            all_brands = set()
            for result in document.results or []:
                all_brands.update(result.brands_detected)
            
            basic_summary = {
                "total_pages": document.total_pages,
                "total_unique_brands": len(all_brands),
                "all_detected_brands": sorted(list(all_brands)),
                "status": document.status
            }
            
            logger.info(f"API: Generated basic summary for {document_id}")
            return {
                "document_id": document_id,
                "summary": basic_summary,
                "status": document.status
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Failed to get document summary {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document summary: {str(e)}")


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
        raise HTTPException(
            status_code=500, detail=f"Failed to cancel processing: {str(e)}"
        )



@router.post("/{document_id}/brands/review")
async def update_brand_review_status(
    document_id: str, review_update: BrandReviewUpdate
) -> dict:
    """
    Update the review status of a detected brand.

    Args:
        document_id: Document ID
        review_update: Brand review update data

    Returns:
        Success message
    """
    try:
        # Validate that the document exists
        document = await firebase_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Update the brand review status
        success = await firebase_service.update_brand_review_status(
            document_id=document_id,
            page_number=review_update.page_number,
            brand_name=review_update.brand_name,
            is_reviewed=review_update.is_reviewed,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Brand not found in document")

        return {
            "message": f"Brand '{review_update.brand_name}' review status updated successfully",
            "is_reviewed": review_update.is_reviewed,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to update brand review status: {str(e)}"
        )


@router.get("/active/processes")
async def get_active_processes() -> dict:
    """
    Get information about currently active processing tasks.

    Returns:
        Dictionary with active process information
    """
    try:
        active_processes = await processing_service.get_active_processes()
        return {"active_processes": active_processes, "count": len(active_processes)}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get active processes: {str(e)}"
        )
