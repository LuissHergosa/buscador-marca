"""
PDF processing service for extracting pages and converting to images in memory.
"""

import io
import logging
from typing import List, Tuple
import PyPDF2
from pdf2image import convert_from_bytes
from PIL import Image

from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Remove PIL limits for large images
Image.MAX_IMAGE_PIXELS = None


class PDFService:
    """Service for PDF processing operations in memory."""
    
    def __init__(self):
        """Initialize PDF service."""
        logger.info("PDFService initialized with no image size limits")
        pass
    
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
            
            # Check page limit
            if total_pages > 100:
                logger.warning(f"PDF has many pages ({total_pages}), but processing will continue")
            
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
        dpi: int = None
    ) -> List[Image.Image]:
        """
        Extract all pages from PDF as PIL Image objects in memory.
        
        Args:
            file_content: PDF file content as bytes
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            
        Returns:
            List of PIL Image objects
        """
        try:
            # Use configured DPI if not specified
            if dpi is None:
                dpi = settings.pdf_dpi
            
            logger.info(f"Extracting PDF pages as images with DPI: {dpi}")
            logger.info(f"File size: {len(file_content)} bytes")
            
            # Convert PDF pages to images in memory with higher resolution
            images = convert_from_bytes(
                file_content,
                dpi=dpi,
                fmt='PNG'
            )
            
            logger.info(f"Successfully extracted {len(images)} pages as images")
            
            # Log image details for debugging
            for i, image in enumerate(images):
                logger.info(f"Page {i+1}: Size={image.size}, Mode={image.mode}, Format={image.format}")
            
            return images
            
        except Exception as e:
            logger.error(f"Failed to extract pages as images: {str(e)}")
            logger.error(f"File size: {len(file_content)} bytes, DPI: {dpi}")
            raise Exception(f"Failed to extract pages as images: {str(e)}")
    
    async def optimize_image(self, image: Image.Image, max_size: int = None) -> Image.Image:
        """
        Optimize image for AI processing in memory while preserving text clarity.
        
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
            logger.error(f"Failed to optimize image: {str(e)}")
            logger.error(f"Image size: {image.size}, Mode: {image.mode}")
            raise Exception(f"Failed to optimize image: {str(e)}")
    
    async def process_pdf(
        self, 
        file_content: bytes, 
        filename: str,
        dpi: int = None
    ) -> Tuple[List[Image.Image], int]:
        """
        Process PDF file in memory: validate and extract pages as optimized images.
        
        Args:
            file_content: PDF file content
            filename: Original filename (for logging purposes)
            dpi: Resolution for image conversion (defaults to settings.pdf_dpi)
            
        Returns:
            Tuple of (optimized_images, total_pages)
        """
        try:
            logger.info(f"Starting PDF processing: {filename}")
            logger.info(f"File size: {len(file_content)} bytes")
            
            # Validate PDF
            is_valid, error_message, total_pages = await self.validate_pdf(file_content)
            if not is_valid:
                logger.error(f"PDF validation failed: {error_message}")
                raise Exception(error_message)
            
            logger.info(f"PDF validation successful: {total_pages} pages")
            
            # Extract pages as images in memory with high resolution
            images = await self.extract_pages_as_images(file_content, dpi)
            
            # Optimize images for AI processing while preserving text clarity
            optimized_images = []
            for i, image in enumerate(images):
                logger.info(f"Optimizing page {i+1}/{len(images)}")
                optimized_image = await self.optimize_image(image)
                optimized_images.append(optimized_image)
            
            logger.info(f"PDF processing completed successfully: {len(optimized_images)} optimized images")
            return optimized_images, total_pages
            
        except Exception as e:
            logger.error(f"PDF processing failed: {str(e)}")
            raise e


# Global PDF service instance
pdf_service = PDFService()
