"""
Processing service that orchestrates the document processing workflow.
Optimized for performance with batch processing and parallel execution.
"""

import asyncio
import logging
import time
from typing import List, Optional

from ..models.document import Document, DocumentCreate, DocumentUpdate
from ..models.processing_status import ProcessingStatus
from .firebase_service import firebase_service
from .pdf_service import pdf_service
from .brand_detection_service import brand_detection_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProcessingService:
    """Service for orchestrating document processing workflow with performance optimizations."""
    
    def __init__(self):
        """Initialize processing service with performance optimizations."""
        logger.info("ProcessingService initialized with performance optimizations")
        self.active_processes = {}  # Track active processing tasks
        
        # Performance settings
        self.batch_size = 5  # Process pages in batches
        self.max_concurrent_batches = 3  # Maximum concurrent batches
    
    async def process_document(
        self, 
        file_content: bytes, 
        filename: str
    ) -> Document:
        """
        Process a complete document: upload, extract pages, detect brands.
        Optimized for performance with parallel processing.
        
        Args:
            file_content: PDF file content
            filename: Original filename
            
        Returns:
            Document object with processing results
        """
        try:
            logger.info(f"Starting optimized document processing: {filename}")
            logger.info(f"File size: {len(file_content)} bytes")
            
            # Step 1: Process PDF and extract images in memory with parallel processing
            logger.info(f"Processing PDF with parallel optimization: {filename}")
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
            
            # Step 3: Start async processing with batch optimization
            logger.info("Starting async brand detection processing with batch optimization")
            asyncio.create_task(
                self._process_document_async_optimized(document.id, images, total_pages)
            )
            
            logger.info(f"Document processing initiated successfully: {document.id}")
            return document
            
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise e
    
    async def process_document_async(
        self, 
        document_id: str,
        file_content: bytes, 
        filename: str
    ) -> None:
        """
        Process a document asynchronously without waiting for completion.
        This method is called by the upload endpoint to start processing in background.
        
        Args:
            document_id: Document ID
            file_content: PDF file content
            filename: Original filename
        """
        try:
            logger.info(f"Starting async document processing: {filename}")
            logger.info(f"File size: {len(file_content)} bytes")
            
            # Step 1: Process PDF and extract images in memory with parallel processing
            logger.info(f"Processing PDF with parallel optimization: {filename}")
            images, total_pages = await pdf_service.process_pdf(
                file_content, filename
            )
            
            logger.info(f"PDF processing completed: {total_pages} pages, {len(images)} images")
            
            # Update document with total pages
            await firebase_service.update_document(
                document_id, 
                DocumentUpdate(total_pages=total_pages)
            )
            
            # Step 2: Start async processing with batch optimization
            logger.info("Starting async brand detection processing with batch optimization")
            await self._process_document_async_optimized(document_id, images, total_pages)
            
            logger.info(f"Document processing completed successfully: {document_id}")
            
        except Exception as e:
            logger.error(f"Async document processing failed: {str(e)}")
            # Update document status to failed
            try:
                await firebase_service.update_document(
                    document_id, 
                    DocumentUpdate(status="failed")
                )
                logger.info(f"Document {document_id} status updated to 'failed' due to processing error")
            except Exception as update_error:
                logger.error(f"Failed to update document {document_id} status: {str(update_error)}")
            raise e
    
    async def _process_document_async_optimized(
        self, 
        document_id: str, 
        images: List, 
        total_pages: int
    ):
        """
        Process document asynchronously with batch processing for better performance.
        
        Args:
            document_id: Document ID
            images: List of image objects
            total_pages: Total number of pages
        """
        try:
            logger.info(f"Starting optimized async processing for document: {document_id}")
            logger.info(f"Total pages to process: {total_pages}")
            logger.info(f"Batch size: {self.batch_size}")
            
            # Track processing start
            self.active_processes[document_id] = {
                "start_time": time.time(),
                "total_pages": total_pages,
                "processed_pages": 0,
                "failed_pages": 0,
                "current_batch": 0
            }
            
            logger.info(f"Processing tracking initialized for document: {document_id}")
            
            # Process pages in batches for better performance
            for batch_start in range(0, len(images), self.batch_size):
                batch_end = min(batch_start + self.batch_size, len(images))
                batch_images = images[batch_start:batch_end]
                batch_page_numbers = list(range(batch_start + 1, batch_end + 1))
                
                logger.info(f"Processing batch {batch_start // self.batch_size + 1}: pages {batch_start + 1} to {batch_end}")
                
                # Update batch tracking
                self.active_processes[document_id]["current_batch"] = batch_start // self.batch_size + 1
                
                # Process batch in parallel
                await self._process_batch_parallel(
                    document_id, 
                    batch_images, 
                    batch_page_numbers
                )
                
                logger.info(f"Batch {batch_start // self.batch_size + 1} completed")
            
            # Generate final document summary
            logger.info(f"Generating final document summary for document {document_id}")
            await self._generate_final_document_summary(document_id, total_pages)
            
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
                total_processing_time = time.time() - self.active_processes[document_id]["start_time"]
                del self.active_processes[document_id]
                logger.info(f"Processing tracking cleaned up for document {document_id}")
                logger.info(f"Completed processing document: {document_id} in {total_processing_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error in optimized async processing for document {document_id}: {str(e)}")
            
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
    
    async def _process_batch_parallel(
        self, 
        document_id: str, 
        batch_images: List, 
        batch_page_numbers: List[int]
    ):
        """
        Process a batch of pages in parallel for better performance.
        
        Args:
            document_id: Document ID
            batch_images: List of images in the batch
            batch_page_numbers: List of page numbers in the batch
        """
        try:
            logger.info(f"Processing batch in parallel: {len(batch_images)} pages")
            
            # Create tasks for parallel processing
            tasks = []
            for image, page_number in zip(batch_images, batch_page_numbers):
                task = self._process_single_page(document_id, image, page_number)
                tasks.append(task)
            
            # Execute batch tasks in parallel
            logger.info(f"Executing {len(tasks)} batch tasks in parallel")
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                page_number = batch_page_numbers[i]
                if isinstance(result, Exception):
                    logger.error(f"Error processing page {page_number} in batch: {str(result)}")
                    # Update page status to failed
                    try:
                        await firebase_service.update_page_status(
                            document_id, page_number, "failed", str(result)
                        )
                    except Exception as update_error:
                        logger.error(f"Failed to update page {page_number} status: {str(update_error)}")
                    # Update tracking
                    self.active_processes[document_id]["failed_pages"] += 1
                else:
                    logger.info(f"Page {page_number} in batch completed successfully")
                    # Update tracking
                    self.active_processes[document_id]["processed_pages"] += 1
            
            logger.info(f"Batch processing completed: {len([r for r in results if not isinstance(r, Exception)])} successful, {len([r for r in results if isinstance(r, Exception)])} failed")
            
        except Exception as e:
            logger.error(f"Error processing batch for document {document_id}: {str(e)}")
            # Don't re-raise the exception to prevent application crash
            logger.error(f"Batch processing error will not crash the application: {str(e)}")
    
    async def _process_single_page(
        self, 
        document_id: str, 
        image, 
        page_number: int
    ):
        """
        Process a single page with optimized error handling.
        
        Args:
            document_id: Document ID
            image: Image object
            page_number: Page number
        """
        try:
            # Update page status to processing
            logger.info(f"Updating page {page_number} status to 'processing'")
            try:
                await firebase_service.update_page_status(
                    document_id, page_number, "processing"
                )
            except Exception as update_error:
                logger.error(f"Failed to update page {page_number} status to 'processing': {str(update_error)}")
            
            # Detect brands in image
            logger.info(f"Starting brand detection for page {page_number}")
            result = await brand_detection_service.detect_brands_in_image(
                image, page_number
            )
            
            # Save result to Firebase
            logger.info(f"Saving brand detection result for page {page_number}")
            try:
                await firebase_service.save_brand_detection_result(
                    document_id, page_number, result, 0  # Processing time will be calculated by the service
                )
            except Exception as save_error:
                logger.error(f"Failed to save brand detection result for page {page_number}: {str(save_error)}")
            
            logger.info(f"Page {page_number} completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing page {page_number} for document {document_id}: {str(e)}")
            # Don't re-raise the exception to prevent application crash
            logger.error(f"Page processing error will not crash the application: {str(e)}")
            raise e
    
    async def _generate_final_document_summary(self, document_id: str, total_pages: int):
        """
        Generate final document summary with all detected brands and statistics.
        
        Args:
            document_id: Document ID
            total_pages: Total number of pages processed
        """
        try:
            logger.info(f"Generating final summary for document {document_id}")
            
            # Get the document with all results
            document = await firebase_service.get_document(document_id)
            if not document:
                logger.error(f"Document {document_id} not found for summary generation")
                return
            
            # Collect all unique brands from all pages
            all_brands = set()
            successful_pages = 0
            failed_pages = 0
            total_processing_time = 0
            
            for result in document.results:
                if result.status == "completed":
                    successful_pages += 1
                    all_brands.update(result.brands_detected)
                    total_processing_time += result.processing_time
                else:
                    failed_pages += 1
            
            # Create document summary
            summary = {
                "total_pages": total_pages,
                "successful_pages": successful_pages,
                "failed_pages": failed_pages,
                "total_unique_brands": len(all_brands),
                "all_detected_brands": sorted(list(all_brands)),
                "total_processing_time": total_processing_time,
                "brands_by_page": {
                    str(result.page_number): {
                        "brands": result.brands_detected,
                        "brand_count": len(result.brands_detected),
                        "processing_time": result.processing_time,
                        "status": result.status
                    }
                    for result in document.results
                }
            }
            
            # Save summary to Firebase
            await firebase_service.save_document_summary(document_id, summary)
            
            logger.info(f"Final summary generated for document {document_id}:")
            logger.info(f"  - Total pages: {total_pages}")
            logger.info(f"  - Successful pages: {successful_pages}")
            logger.info(f"  - Failed pages: {failed_pages}")
            logger.info(f"  - Total unique brands detected: {len(all_brands)}")
            logger.info(f"  - Brands found: {sorted(list(all_brands))}")
            logger.info(f"  - Total processing time: {total_processing_time:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Failed to generate final summary for document {document_id}: {str(e)}")
    
    async def _process_document_async(
        self, 
        document_id: str, 
        images: List, 
        total_pages: int
    ):
        """
        Legacy processing method - kept for compatibility.
        Process document asynchronously.
        
        Args:
            document_id: Document ID
            images: List of image objects
            total_pages: Total number of pages
        """
        try:
            logger.info(f"Starting legacy async processing for document: {document_id}")
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
