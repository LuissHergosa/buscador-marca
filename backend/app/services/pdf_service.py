"""
PDF processing service for extracting pages and converting to images.
"""

import os
import tempfile
from pathlib import Path
from typing import List, Tuple
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image
import aiofiles

from ..config import settings


class PDFService:
    """Service for PDF processing operations."""
    
    def __init__(self):
        """Initialize PDF service."""
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
    
    async def validate_pdf(self, file_path: str) -> Tuple[bool, str, int]:
        """
        Validate PDF file and get basic information.
        
        Returns:
            Tuple of (is_valid, error_message, total_pages)
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    return False, "PDF is encrypted and cannot be processed", 0
                
                # Get total pages
                total_pages = len(pdf_reader.pages)
                
                # Check page limit
                if total_pages > 100:
                    return False, f"PDF has too many pages ({total_pages}). Maximum allowed is 100.", 0
                
                # Check if PDF is empty
                if total_pages == 0:
                    return False, "PDF is empty", 0
                
                return True, "", total_pages
                
        except PyPDF2.PdfReadError as e:
            return False, f"Invalid PDF file: {str(e)}", 0
        except Exception as e:
            return False, f"Error reading PDF: {str(e)}", 0
    
    async def extract_pages_as_images(
        self, 
        pdf_path: str, 
        output_dir: str,
        dpi: int = 300
    ) -> List[str]:
        """
        Extract all pages from PDF as images.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save images
            dpi: Resolution for image conversion
            
        Returns:
            List of paths to the generated images
        """
        try:
            # Convert PDF pages to images
            images = convert_from_path(
                pdf_path,
                dpi=dpi,
                fmt='PNG',
                output_folder=output_dir,
                output_file='page'
            )
            
            # Return list of image paths
            image_paths = []
            for i, image in enumerate(images):
                image_path = os.path.join(output_dir, f"page_{i+1:03d}.png")
                image.save(image_path, 'PNG')
                image_paths.append(image_path)
            
            return image_paths
            
        except Exception as e:
            raise Exception(f"Failed to extract pages as images: {str(e)}")
    
    async def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file to temporary location.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        try:
            # Create temporary file
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Failed to save uploaded file: {str(e)}")
    
    async def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """
        Clean up temporary files.
        
        Args:
            file_paths: List of file paths to delete
        """
        try:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    
            # Remove empty directories
            for file_path in file_paths:
                dir_path = os.path.dirname(file_path)
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    
        except Exception as e:
            # Log error but don't raise exception for cleanup
            print(f"Warning: Failed to cleanup temp files: {str(e)}")
    
    async def optimize_image(self, image_path: str, max_size: int = 1024) -> str:
        """
        Optimize image for AI processing.
        
        Args:
            image_path: Path to the image
            max_size: Maximum dimension size
            
        Returns:
            Path to optimized image
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if image is too large
                if max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Save optimized image
                optimized_path = image_path.replace('.png', '_optimized.png')
                img.save(optimized_path, 'PNG', optimize=True, quality=85)
                
                return optimized_path
                
        except Exception as e:
            raise Exception(f"Failed to optimize image: {str(e)}")
    
    async def process_pdf(
        self, 
        file_content: bytes, 
        filename: str,
        dpi: int = 300
    ) -> Tuple[str, List[str], int]:
        """
        Process PDF file: validate, save, and extract pages as images.
        
        Args:
            file_content: PDF file content
            filename: Original filename
            dpi: Resolution for image conversion
            
        Returns:
            Tuple of (pdf_path, image_paths, total_pages)
        """
        try:
            # Save uploaded file
            pdf_path = await self.save_uploaded_file(file_content, filename)
            
            # Validate PDF
            is_valid, error_message, total_pages = await self.validate_pdf(pdf_path)
            if not is_valid:
                await self.cleanup_temp_files([pdf_path])
                raise Exception(error_message)
            
            # Create output directory for images
            output_dir = tempfile.mkdtemp()
            
            # Extract pages as images
            image_paths = await self.extract_pages_as_images(pdf_path, output_dir, dpi)
            
            # Optimize images for AI processing
            optimized_paths = []
            for image_path in image_paths:
                optimized_path = await self.optimize_image(image_path)
                optimized_paths.append(optimized_path)
            
            return pdf_path, optimized_paths, total_pages
            
        except Exception as e:
            # Cleanup on error
            if 'pdf_path' in locals():
                await self.cleanup_temp_files([pdf_path])
            if 'image_paths' in locals():
                await self.cleanup_temp_files(image_paths)
            raise e


# Global PDF service instance
pdf_service = PDFService()
