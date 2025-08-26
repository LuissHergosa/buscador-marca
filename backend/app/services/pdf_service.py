"""
PDF processing service for extracting pages and converting to images in memory.
Optimized for performance with parallel processing and memory efficiency.
"""

import io
import logging
import asyncio
from typing import List, Tuple, Optional
import PyPDF2
from pdf2image import convert_from_bytes
from PIL import Image
import concurrent.futures

from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Remove PIL limits for large images
Image.MAX_IMAGE_PIXELS = None


class PDFService:
    """Service for PDF processing operations in memory with performance optimizations."""
    
    def __init__(self):
        """Initialize PDF service with thread pool for parallel processing."""
        logger.info("PDFService initialized with performance optimizations")
        # Create thread pool for CPU-intensive operations
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(8, settings.max_concurrent_pages),
            thread_name_prefix="pdf_worker"
        )
        logger.info(f"Thread pool initialized with {min(8, settings.max_concurrent_pages)} workers")
    
    async def validate_pdf(self, file_content: bytes) -> Tuple[bool, str, int]:
        """
        Validate PDF file content and get basic information.
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            Tuple of (is_valid, error_message, total_pages)
        """
        try:
            logger.info(f"Validating PDF file (size: {len(file_content)} bytes)")
            
            # Run validation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._validate_pdf_sync,
                file_content
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            return False, f"Error reading PDF: {str(e)}", 0
    
    def _validate_pdf_sync(self, file_content: bytes) -> Tuple[bool, str, int]:
        """Synchronous PDF validation for thread pool execution."""
        try:
            # Create file-like object from bytes
            pdf_stream = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            # Check if PDF is encrypted
            if pdf_reader.is_encrypted:
                logger.error("PDF is encrypted and cannot be processed")
                return False, "PDF is encrypted and cannot be processed", 0
            
            # Get total pages
            total_pages = len(pdf_reader.pages)
            logger.info(f"PDF validation successful: {total_pages} pages found")
            
            # Check if PDF is empty
            if total_pages == 0:
                logger.error("PDF is empty")
                return False, "PDF is empty", 0
            
            return True, "", total_pages
            
        except PyPDF2.PdfReadError as e:
            logger.error(f"Invalid PDF file: {str(e)}")
            return False, f"Invalid PDF file: {str(e)}", 0
        except Exception as e:
            logger.error(f"Error reading PDF: {str(e)}")
            return False, f"Error reading PDF: {str(e)}", 0
    
    async def extract_pages_as_images(
        self, 
        file_content: bytes,
        dpi: int = None,
        start_page: int = 1,
        end_page: Optional[int] = None
    ) -> List[Image.Image]:
        """
        Extract pages from PDF as PIL Image objects with parallel processing.
        
        Args:
            file_content: PDF file content as bytes
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            start_page: First page to extract (1-based)
            end_page: Last page to extract (inclusive, None for all pages)
            
        Returns:
            List of PIL Image objects
        """
        try:
            # Use configured DPI if not specified
            if dpi is None:
                dpi = settings.pdf_dpi
            
            logger.info(f"Extracting PDF pages as images with DPI: {dpi}")
            logger.info(f"File size: {len(file_content)} bytes")
            logger.info(f"Page range: {start_page} to {end_page or 'end'}")
            
            # Run conversion in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            images = await loop.run_in_executor(
                self.executor,
                self._extract_pages_sync,
                file_content,
                dpi,
                start_page,
                end_page
            )
            
            logger.info(f"Successfully extracted {len(images)} pages as images")
            
            # Log image details for debugging
            for i, image in enumerate(images):
                logger.info(f"Page {start_page + i}: Size={image.size}, Mode={image.mode}")
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to extract pages as images: {str(e)}")
            logger.error(f"File size: {len(file_content)} bytes, DPI: {dpi}")
            raise Exception(f"Failed to extract pages as images: {str(e)}")
    
    def _extract_pages_sync(
        self, 
        file_content: bytes, 
        dpi: int, 
        start_page: int, 
        end_page: Optional[int]
    ) -> List[Image.Image]:
        """Synchronous page extraction for thread pool execution."""
        try:
            # Convert PDF pages to images in memory with optimized settings
            images = convert_from_bytes(
                file_content,
                dpi=dpi,
                fmt='PNG',
                first_page=start_page,
                last_page=end_page,
                # Use multiple threads for conversion
                thread_count=min(4, settings.max_concurrent_pages)
            )
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to extract pages synchronously: {str(e)}")
            raise e
    
    async def optimize_image(self, image: Image.Image, max_size: int = None) -> Image.Image:
        """
        Optimize image for AI processing in memory while preserving text clarity.
        Uses parallel processing for optimization.
        
        Args:
            image: PIL Image object
            max_size: Maximum dimension size (defaults to settings.max_image_size)
            
        Returns:
            Optimized PIL Image object
        """
        try:
            # Use configured max size if not specified
            if max_size is None:
                max_size = settings.max_image_size
            
            original_size = image.size
            logger.info(f"Optimizing image: Original size={original_size}, Max size={max_size}")
            
            # Run optimization in thread pool
            loop = asyncio.get_event_loop()
            optimized_image = await loop.run_in_executor(
                self.executor,
                self._optimize_image_sync,
                image,
                max_size
            )
            
            return optimized_image
            
        except Exception as e:
            logger.error(f"Failed to optimize image: {str(e)}")
            logger.error(f"Image size: {image.size}, Mode: {image.mode}")
            raise Exception(f"Failed to optimize image: {str(e)}")
    
    def _optimize_image_sync(self, image: Image.Image, max_size: int) -> Image.Image:
        """Synchronous image optimization for thread pool execution."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                logger.info(f"Converting image from {image.mode} to RGB")
                image = image.convert('RGB')
            
            # Only resize if image is extremely large to preserve text clarity
            # For architectural plans, we want to maintain high resolution for text detection
            if max(image.size) > max_size:
                logger.info(f"Resizing image from {image.size} to max {max_size}")
                # Use high-quality resampling for better text preservation
                image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.info(f"Image resized to: {image.size}")
            else:
                logger.info(f"Image size {image.size} is within limits, no resizing needed")
            
            return image
            
        except Exception as e:
            logger.error(f"Failed to optimize image synchronously: {str(e)}")
            raise e
    
    async def process_pdf_parallel(
        self, 
        file_content: bytes, 
        filename: str,
        dpi: int = None,
        batch_size: int = 5
    ) -> Tuple[List[Image.Image], int]:
        """
        Process PDF file with parallel processing for better performance.
        
        Args:
            file_content: PDF file content
            filename: Original filename (for logging purposes)
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            batch_size: Number of pages to process in parallel batches
            
        Returns:
            Tuple of (optimized_images, total_pages)
        """
        try:
            logger.info(f"Starting parallel PDF processing: {filename}")
            logger.info(f"File size: {len(file_content)} bytes")
            logger.info(f"Batch size: {batch_size}")
            
            # Validate PDF
            is_valid, error_message, total_pages = await self.validate_pdf(file_content)
            if not is_valid:
                logger.error(f"PDF validation failed: {error_message}")
                raise Exception(error_message)
            
            logger.info(f"PDF validation successful: {total_pages} pages")
            
            # Process pages in parallel batches
            all_images = []
            
            for batch_start in range(1, total_pages + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, total_pages)
                logger.info(f"Processing batch: pages {batch_start} to {batch_end}")
                
                # Extract batch of pages
                batch_images = await self.extract_pages_as_images(
                    file_content, dpi, batch_start, batch_end
                )
                
                # Optimize batch images in parallel
                optimization_tasks = []
                for image in batch_images:
                    task = self.optimize_image(image)
                    optimization_tasks.append(task)
                
                # Wait for all optimizations to complete
                optimized_batch = await asyncio.gather(*optimization_tasks)
                all_images.extend(optimized_batch)
                
                logger.info(f"Batch {batch_start}-{batch_end} completed: {len(optimized_batch)} images")
            
            logger.info(f"Parallel PDF processing completed: {len(all_images)} optimized images")
            return all_images, total_pages
            
        except Exception as e:
            logger.error(f"Parallel PDF processing failed: {str(e)}")
            raise e
    
    async def process_pdf(
        self, 
        file_content: bytes, 
        filename: str,
        dpi: int = None
    ) -> Tuple[List[Image.Image], int]:
        """
        Process PDF file in memory: validate and extract pages as optimized images.
        Uses parallel processing for better performance.
        
        Args:
            file_content: PDF file content
            filename: Original filename (for logging purposes)
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            
        Returns:
            Tuple of (optimized_images, total_pages)
        """
        # Use parallel processing for better performance
        return await self.process_pdf_parallel(file_content, filename, dpi)
    
    def __del__(self):
        """Cleanup thread pool on deletion."""
        try:
            if hasattr(self, 'executor') and self.executor:
                logger.info("Shutting down PDF service thread pool executor")
                # Use shutdown with wait=False to avoid blocking during cleanup
                self.executor.shutdown(wait=False)
                logger.info("PDF service thread pool executor shutdown completed")
        except Exception as e:
            # Don't log during shutdown as it might cause issues
            pass


# Global PDF service instance
pdf_service = PDFService()
