"""
Processing service that orchestrates the document processing workflow.
"""

import asyncio
import time
from typing import List, Optional
from datetime import datetime

from ..models.document import Document, DocumentCreate
from ..models.brand_detection import BrandDetectionCreate
from ..models.processing_status import ProcessingStatus
from .firebase_service import firebase_service
from .pdf_service import pdf_service
from .brand_detection_service import brand_detection_service


class ProcessingService:
    """Service for orchestrating document processing workflow."""
    
    def __init__(self):
        """Initialize processing service."""
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
            # Step 1: Process PDF and extract images
            print(f"Processing PDF: {filename}")
            pdf_path, image_paths, total_pages = await pdf_service.process_pdf(
                file_content, filename
            )
            
            # Step 2: Create document record in Firebase
            document_data = DocumentCreate(
                filename=filename,
                total_pages=total_pages
            )
            document = await firebase_service.create_document(document_data)
            
            # Step 3: Start async processing
            asyncio.create_task(
                self._process_document_async(document.id, image_paths, total_pages)
            )
            
            # Cleanup temporary files
            await pdf_service.cleanup_temp_files([pdf_path] + image_paths)
            
            return document
            
        except Exception as e:
            # Cleanup on error
            if 'pdf_path' in locals():
                await pdf_service.cleanup_temp_files([pdf_path])
            if 'image_paths' in locals():
                await pdf_service.cleanup_temp_files(image_paths)
            raise e
    
    async def _process_document_async(
        self, 
        document_id: str, 
        image_paths: List[str], 
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
            print(f"Starting async processing for document: {document_id}")
            
            # Track processing start
            self.active_processes[document_id] = {
                "start_time": time.time(),
                "total_pages": total_pages,
                "processed_pages": 0,
                "failed_pages": 0
            }
            
            # Process each page
            for i, image_path in enumerate(image_paths):
                page_number = i + 1
                
                try:
                    # Update page status to processing
                    await firebase_service.update_page_status(
                        document_id, page_number, "processing"
                    )
                    
                    # Detect brands in image
                    result = await brand_detection_service.detect_brands_in_image(
                        image_path, page_number
                    )
                    
                    # Calculate processing time
                    processing_time = time.time() - self.active_processes[document_id]["start_time"]
                    
                    # Save result to Firebase
                    await firebase_service.save_brand_detection_result(
                        document_id, page_number, result, processing_time
                    )
                    
                    # Update tracking
                    self.active_processes[document_id]["processed_pages"] += 1
                    
                    print(f"Completed page {page_number}/{total_pages} for document {document_id}")
                    
                except Exception as e:
                    print(f"Error processing page {page_number} for document {document_id}: {str(e)}")
                    
                    # Update page status to failed
                    await firebase_service.update_page_status(
                        document_id, page_number, "failed", str(e)
                    )
                    
                    # Update tracking
                    self.active_processes[document_id]["failed_pages"] += 1
            
            # Update document status
            final_status = "completed"
            if self.active_processes[document_id]["failed_pages"] > 0:
                if self.active_processes[document_id]["failed_pages"] == total_pages:
                    final_status = "failed"
                else:
                    final_status = "completed_with_errors"
            
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(status=final_status)
            )
            
            # Cleanup tracking
            if document_id in self.active_processes:
                del self.active_processes[document_id]
            
            print(f"Completed processing document: {document_id}")
            
        except Exception as e:
            print(f"Error in async processing for document {document_id}: {str(e)}")
            
            # Update document status to failed
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(status="failed")
            )
            
            # Cleanup tracking
            if document_id in self.active_processes:
                del self.active_processes[document_id]
    
    async def get_processing_status(self, document_id: str) -> Optional[ProcessingStatus]:
        """
        Get processing status for a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            ProcessingStatus object or None if document not found
        """
        return await firebase_service.get_processing_status(document_id)
    
    async def get_active_processes(self) -> dict:
        """
        Get information about currently active processing tasks.
        
        Returns:
            Dictionary with active process information
        """
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
            # Update document status to cancelled
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(status="cancelled")
            )
            
            # Remove from active processes
            if document_id in self.active_processes:
                del self.active_processes[document_id]
            
            return True
        except Exception as e:
            print(f"Error cancelling processing for document {document_id}: {str(e)}")
            return False


# Global processing service instance
processing_service = ProcessingService()
