"""
Processing service that orchestrates the document processing workflow.
"""

import asyncio
import logging
import time
from typing import List, Optional
from datetime import datetime

from ..models.document import Document, DocumentCreate, DocumentUpdate
from ..models.brand_detection import BrandDetectionCreate
from ..models.processing_status import ProcessingStatus
from .firebase_service import firebase_service
from .pdf_service import pdf_service
from .brand_detection_service import brand_detection_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for orchestrating document processing workflow."""
    
    def __init__(self):
        """Initialize processing service."""
        logger.info("ProcessingService initialized")
        self.active_processes = {}  # Track active processing tasks
    
    async def process_document(
        self, 
        file_content: bytes, 
        filename: str
    ) -> Document:
        """
        Process a complete document: upload, extract pages, detect brands.
        
        Args:
            file_content: PDF file content
            filename: Original filename
            
        Returns:
            Document object with processing results
        """
        try:
            logger.info(f"Starting document processing: {filename}")
            logger.info(f"File size: {len(file_content)} bytes")
            
            # Step 1: Process PDF and extract images in memory
            logger.info(f"Processing PDF: {filename}")
            images, total_pages = await pdf_service.process_pdf(
                file_content, filename
            )
            
            logger.info(f"PDF processing completed: {total_pages} pages, {len(images)} images")
            
            # Step 2: Create document record in Firebase
            logger.info("Creating document record in Firebase")
            document_data = DocumentCreate(
                filename=filename,
                total_pages=total_pages
            )
            document = await firebase_service.create_document(document_data)
            logger.info(f"Document created in Firebase: {document.id}")
            
            # Step 3: Start async processing
            logger.info("Starting async brand detection processing")
            asyncio.create_task(
                self._process_document_async(document.id, images, total_pages)
            )
            
            logger.info(f"Document processing initiated successfully: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise e
    
    async def _process_document_async(
        self, 
        document_id: str, 
        images: List, 
        total_pages: int
    ):
        """
        Process document asynchronously.
        
        Args:
            document_id: Document ID
            image_paths: List of image paths
            total_pages: Total number of pages
        """
        try:
            logger.info(f"Starting async processing for document: {document_id}")
            logger.info(f"Total pages to process: {total_pages}")
            
            # Track processing start
            self.active_processes[document_id] = {
                "start_time": time.time(),
                "total_pages": total_pages,
                "processed_pages": 0,
                "failed_pages": 0
            }
            
            logger.info(f"Processing tracking initialized for document: {document_id}")
            
            # Process each page
            for i, image in enumerate(images):
                page_number = i + 1
                logger.info(f"Processing page {page_number}/{total_pages} for document {document_id}")
                
                try:
                    # Update page status to processing
                    logger.info(f"Updating page {page_number} status to 'processing'")
                    await firebase_service.update_page_status(
                        document_id, page_number, "processing"
                    )
                    
                    # Detect brands in image
                    logger.info(f"Starting brand detection for page {page_number}")
                    result = await brand_detection_service.detect_brands_in_image(
                        image, page_number
                    )
                    
                    # Calculate processing time
                    processing_time = time.time() - self.active_processes[document_id]["start_time"]
                    logger.info(f"Page {page_number} processing time: {processing_time:.2f} seconds")
                    
                    # Save result to Firebase
                    logger.info(f"Saving brand detection result for page {page_number}")
                    await firebase_service.save_brand_detection_result(
                        document_id, page_number, result, processing_time
                    )
                    
                    # Update tracking
                    self.active_processes[document_id]["processed_pages"] += 1
                    logger.info(f"Page {page_number} completed successfully. Progress: {self.active_processes[document_id]['processed_pages']}/{total_pages}")
                    
                except Exception as e:
                    logger.error(f"Error processing page {page_number} for document {document_id}: {str(e)}")
                    
                    # Update page status to failed
                    logger.info(f"Updating page {page_number} status to 'failed'")
                    await firebase_service.update_page_status(
                        document_id, page_number, "failed", str(e)
                    )
                    
                    # Update tracking
                    self.active_processes[document_id]["failed_pages"] += 1
                    logger.error(f"Page {page_number} failed. Failed pages: {self.active_processes[document_id]['failed_pages']}")
            
            # Update document status
            final_status = "completed"
            if self.active_processes[document_id]["failed_pages"] > 0:
                if self.active_processes[document_id]["failed_pages"] == total_pages:
                    final_status = "failed"
                    logger.error(f"All pages failed for document {document_id}")
                else:
                    final_status = "completed_with_errors"
                    logger.warning(f"Document {document_id} completed with {self.active_processes[document_id]['failed_pages']} failed pages")
            
            logger.info(f"Updating document {document_id} status to: {final_status}")
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(status=final_status)
            )
            
            # Cleanup tracking
            if document_id in self.active_processes:
                del self.active_processes[document_id]
                logger.info(f"Processing tracking cleaned up for document {document_id}")
            
            total_processing_time = time.time() - self.active_processes.get(document_id, {}).get("start_time", time.time())
            logger.info(f"Completed processing document: {document_id} in {total_processing_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error in async processing for document {document_id}: {str(e)}")
            
            # Update document status to failed
            logger.info(f"Updating document {document_id} status to 'failed' due to processing error")
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(status="failed")
            )
            
            # Cleanup tracking
            if document_id in self.active_processes:
                del self.active_processes[document_id]
                logger.info(f"Processing tracking cleaned up for failed document {document_id}")
    
    async def get_processing_status(self, document_id: str) -> Optional[ProcessingStatus]:
        """
        Get processing status for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            ProcessingStatus object or None if document not found
        """
        logger.info(f"Getting processing status for document: {document_id}")
        status = await firebase_service.get_processing_status(document_id)
        if status:
            logger.info(f"Processing status for document {document_id}: {status.status}")
        else:
            logger.warning(f"No processing status found for document: {document_id}")
        return status
    
    async def get_active_processes(self) -> dict:
        """
        Get information about currently active processing tasks.
        
        Returns:
            Dictionary with active process information
        """
        logger.info(f"Getting active processes. Count: {len(self.active_processes)}")
        return self.active_processes.copy()
    
    async def cancel_processing(self, document_id: str) -> bool:
        """
        Cancel processing for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            logger.info(f"Cancelling processing for document: {document_id}")
            
            # Update document status to cancelled
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(status="cancelled")
            )
            
            # Remove from active processes
            if document_id in self.active_processes:
                del self.active_processes[document_id]
                logger.info(f"Document {document_id} removed from active processes")
            
            logger.info(f"Processing cancelled successfully for document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling processing for document {document_id}: {str(e)}")
            return False


# Global processing service instance
processing_service = ProcessingService()
