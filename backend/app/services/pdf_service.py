"""
PDF processing service for extracting pages and converting to grayscale images using temporary files.
Optimized for memory efficiency with file-based processing and immediate cleanup.
"""

import io
import os
import logging
import asyncio
import tempfile
import shutil
from typing import List, Tuple, Optional, Dict
import PyPDF2
from pdf2image import convert_from_bytes
from PIL import Image
import concurrent.futures
import cv2
import numpy as np

from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Remove PIL limits for large images
Image.MAX_IMAGE_PIXELS = None


class PDFService:
    """Service for PDF processing operations using temporary files for memory efficiency."""
    
    def __init__(self):
        """Initialize PDF service with thread pool and temporary file management."""
        logger.info("PDFService initialized with memory-efficient file-based processing")
        # Create thread pool for CPU-intensive operations
        self.executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(4, settings.max_concurrent_pages),  # Reduced for memory efficiency
            thread_name_prefix="pdf_worker"
        )
        logger.info(f"Thread pool initialized with {min(4, settings.max_concurrent_pages)} workers")
        
        # Create base temp directory for this service
        self.temp_base_dir = os.path.join(tempfile.gettempdir(), "buscador_marca_images")
        os.makedirs(self.temp_base_dir, exist_ok=True)
        logger.info(f"Temporary directory created: {self.temp_base_dir}")
        
        # Track active temporary directories for cleanup
        self.active_temp_dirs = {}
        
        # Memory optimization settings
        self.chunk_processing_batch_size = 2  # Process fewer pages at once to save memory
    
    def create_temp_directory(self, document_id: str) -> str:
        """
        Create a temporary directory for storing document images.
        
        Args:
            document_id: Unique document identifier
            
        Returns:
            Path to the temporary directory
        """
        temp_dir = os.path.join(self.temp_base_dir, f"doc_{document_id}")
        os.makedirs(temp_dir, exist_ok=True)
        self.active_temp_dirs[document_id] = temp_dir
        logger.info(f"Created temporary directory for document {document_id}: {temp_dir}")
        return temp_dir
    
    def cleanup_temp_directory(self, document_id: str) -> bool:
        """
        Clean up temporary directory for a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if cleanup was successful
        """
        try:
            if document_id in self.active_temp_dirs:
                temp_dir = self.active_temp_dirs[document_id]
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                del self.active_temp_dirs[document_id]
                return True
            return True
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory for document {document_id}: {str(e)}")
            return False
    
    def _convert_to_grayscale_and_save(
        self, 
        pil_image: Image.Image, 
        output_path: str, 
        page_number: int
    ) -> bool:
        """
        Convert PIL image to grayscale and save as temporary file.
        
        Args:
            pil_image: PIL Image object
            output_path: Path to save the grayscale image
            page_number: Page number (for logging)
            
        Returns:
            True if conversion and save was successful
        """
        try:
            logger.info(f"Converting page {page_number} to grayscale and saving to: {output_path}")
            
            # Convert to grayscale using PIL (more efficient than OpenCV conversion)
            if pil_image.mode != 'L':  # L = Grayscale
                grayscale_image = pil_image.convert('L')
                logger.info(f"Converted page {page_number} from {pil_image.mode} to grayscale")
            else:
                grayscale_image = pil_image
                logger.info(f"Page {page_number} already in grayscale")
            
            # Save as PNG for lossless compression
            grayscale_image.save(output_path, 'PNG', optimize=True)
            
            # Free memory immediately
            del grayscale_image
            del pil_image
            
            logger.info(f"Page {page_number} saved as grayscale to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting page {page_number} to grayscale: {str(e)}")
            return False
    
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
    
    async def extract_pages_as_grayscale_files(
        self, 
        file_content: bytes,
        temp_dir: str,
        dpi: int = None,
        start_page: int = 1,
        end_page: Optional[int] = None
    ) -> List[str]:
        """
        Extract pages from PDF and save as grayscale image files for memory efficiency.
        
        Args:
            file_content: PDF file content as bytes
            temp_dir: Temporary directory to save images
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            start_page: First page to extract (1-based)
            end_page: Last page to extract (inclusive, None for all pages)
            
        Returns:
            List of file paths to grayscale image files
        """
        try:
            # Use configured DPI if not specified
            if dpi is None:
                dpi = settings.pdf_dpi
            
            logger.info(f"Extracting PDF pages as grayscale files with DPI: {dpi}")
            logger.info(f"File size: {len(file_content)} bytes")
            logger.info(f"Page range: {start_page} to {end_page or 'end'}")
            logger.info(f"Temporary directory: {temp_dir}")
            
            # Run conversion in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            image_files = await loop.run_in_executor(
                self.executor,
                self._extract_pages_as_grayscale_files_sync,
                file_content,
                temp_dir,
                dpi,
                start_page,
                end_page
            )
            
            logger.info(f"Successfully extracted and saved {len(image_files)} pages as grayscale files")
            return image_files
            
        except Exception as e:
            logger.error(f"Failed to extract pages as grayscale files: {str(e)}")
            logger.error(f"File size: {len(file_content)} bytes, DPI: {dpi}")
            raise Exception(f"Failed to extract pages as grayscale files: {str(e)}")
    
    def _extract_pages_as_grayscale_files_sync(
        self, 
        file_content: bytes, 
        temp_dir: str,
        dpi: int, 
        start_page: int, 
        end_page: Optional[int]
    ) -> List[str]:
        """Synchronous page extraction with immediate conversion to grayscale files."""
        try:
            logger.info(f"Starting synchronous extraction and grayscale conversion")
            
            # Convert PDF pages to images in memory (temporary)
            images = convert_from_bytes(
                file_content,
                dpi=dpi,
                fmt='PNG',
                first_page=start_page,
                last_page=end_page,
                # Use fewer threads for memory efficiency
                thread_count=min(2, settings.max_concurrent_pages)
            )
            
            logger.info(f"Extracted {len(images)} pages, converting to grayscale files")
            
            # Convert each image to grayscale and save immediately
            image_files = []
            for i, pil_image in enumerate(images):
                page_number = start_page + i
                filename = f"page_{page_number:04d}.png"
                output_path = os.path.join(temp_dir, filename)
                
                # Convert and save (this method frees memory immediately)
                success = self._convert_to_grayscale_and_save(pil_image, output_path, page_number)
                
                if success:
                    image_files.append(output_path)
                    logger.info(f"Page {page_number} converted and saved: {output_path}")
                else:
                    logger.error(f"Failed to convert and save page {page_number}")
            
            # Clear the images list to free memory
            del images
            
            logger.info(f"Completed grayscale conversion: {len(image_files)} files created")
            return image_files
            
        except Exception as e:
            logger.error(f"Failed to extract pages as grayscale files synchronously: {str(e)}")
            raise e
    
    def load_grayscale_image_from_file(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load grayscale image from file for OCR processing.
        
        Args:
            image_path: Path to the grayscale image file
            
        Returns:
            OpenCV grayscale image as numpy array or None if failed
        """
        try:
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return None
            
            # Load image using OpenCV in grayscale mode directly
            grayscale_image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            
            if grayscale_image is None:
                logger.error(f"Failed to load image from: {image_path}")
                return None
            
            logger.info(f"Loaded grayscale image from file: {image_path}, Shape: {grayscale_image.shape}")
            return grayscale_image
            
        except Exception as e:
            logger.error(f"Error loading grayscale image from {image_path}: {str(e)}")
            return None
    
    async def process_pdf_with_temp_files(
        self, 
        file_content: bytes, 
        document_id: str,
        filename: str,
        dpi: int = None,
        batch_size: int = 3
    ) -> Tuple[List[str], int, str]:
        """
        Process PDF file using temporary files for memory efficiency.
        
        Args:
            file_content: PDF file content
            document_id: Document identifier for temp directory
            filename: Original filename (for logging purposes)
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            batch_size: Number of pages to process in parallel batches
            
        Returns:
            Tuple of (image_file_paths, total_pages, temp_directory)
        """
        try:
            logger.info(f"Starting memory-efficient PDF processing: {filename}")
            logger.info(f"File size: {len(file_content)} bytes")
            logger.info(f"Batch size: {batch_size}")
            
            # Validate PDF
            is_valid, error_message, total_pages = await self.validate_pdf(file_content)
            if not is_valid:
                logger.error(f"PDF validation failed: {error_message}")
                raise Exception(error_message)
            
            logger.info(f"PDF validation successful: {total_pages} pages")
            
            # Create temporary directory for this document
            temp_dir = self.create_temp_directory(document_id)
            
            # Process pages in smaller batches for memory efficiency
            all_image_files = []
            
            for batch_start in range(1, total_pages + 1, batch_size):
                batch_end = min(batch_start + batch_size - 1, total_pages)
                logger.info(f"Processing batch: pages {batch_start} to {batch_end}")
                
                # Extract batch of pages and convert to grayscale files immediately
                batch_image_files = await self.extract_pages_as_grayscale_files(
                    file_content, temp_dir, dpi, batch_start, batch_end
                )
                
                all_image_files.extend(batch_image_files)
                logger.info(f"Batch {batch_start}-{batch_end} completed: {len(batch_image_files)} grayscale files created")
            
            logger.info(f"Memory-efficient PDF processing completed: {len(all_image_files)} grayscale files in {temp_dir}")
            return all_image_files, total_pages, temp_dir
            
        except Exception as e:
            logger.error(f"Memory-efficient PDF processing failed: {str(e)}")
            # Cleanup temp directory if created
            if document_id in self.active_temp_dirs:
                self.cleanup_temp_directory(document_id)
            raise e
    
    async def process_pdf(
        self, 
        file_content: bytes, 
        document_id: str,
        filename: str,
        dpi: int = None
    ) -> Tuple[List[str], int, str]:
        """
        Process PDF file with memory-efficient temporary files.
        
        Args:
            file_content: PDF file content
            document_id: Document identifier
            filename: Original filename (for logging purposes)
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            
        Returns:
            Tuple of (image_file_paths, total_pages, temp_directory)
        """
        # Use memory-efficient processing with temporary files
        return await self.process_pdf_with_temp_files(file_content, document_id, filename, dpi)
    
    def __del__(self):
        """Cleanup thread pool and temporary directories on deletion."""
        try:
            # Cleanup all active temporary directories
            if hasattr(self, 'active_temp_dirs'):
                for document_id in list(self.active_temp_dirs.keys()):
                    self.cleanup_temp_directory(document_id)
            
            # Cleanup thread pool executor
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
