"""
OCR Service using EasyOCR for text extraction from images.
Optimized for accuracy with coordinate preservation and retry logic.
Uses OpenCV for grayscale preprocessing to improve performance and accuracy.
"""

import asyncio
import logging
import time
import gc
from typing import List, Tuple, Dict
from dataclasses import dataclass
import easyocr
import cv2
import numpy as np

from ..config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TextDetection:
    """Represents a detected text with its coordinates and confidence."""
    text: str
    bbox: List[List[int]]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    confidence: float
    chunk_position: Tuple[int, int]


class OCRService:
    """Service for text extraction using EasyOCR with high accuracy settings."""
    
    def __init__(self):
        """Initialize OCR service with optimized settings for accuracy."""
        logger.info("Initializing OCRService with EasyOCR for Spanish and English")
        
        try:
            # Initialize EasyOCR reader with Spanish and English
            # Optimized for accuracy over speed
            self.reader = easyocr.Reader(
                settings.ocr_languages_list,  # Use the list property
                gpu=settings.use_gpu,  # Use GPU if available, fallback to CPU
                model_storage_directory='./models',  # Local model storage
                download_enabled=True,  # Download models if not present
                # Accuracy-focused settings
                # Recognition settings for better accuracy
            )
            
            logger.info(f"OCRService initialized with GPU: {settings.use_gpu}, Languages: {settings.ocr_languages_list}")
            
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR reader: {str(e)}")
            logger.info("Falling back to CPU-only mode")
            
            # Fallback to CPU-only mode
            self.reader = easyocr.Reader(
                settings.ocr_languages_list,  # Use the list property
                gpu=False,  # Force CPU mode
                model_storage_directory='./models',  # Local model storage
                download_enabled=True,  # Download models if not present
                # Simplified settings for CPU mode

            )
            
            logger.info("OCRService initialized in CPU-only mode")
        
        # Create semaphore for concurrent processing
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_pages)
        
        # Chunk configuration (same as brand detection service)
        self.chunk_size = (1024, 1024)  # 1024x1024 pixels per chunk
        self.chunk_overlap = 200  # 200 pixels overlap between chunks
        
        # Memory management configuration
        self.max_concurrent_chunks = 20  # Process max 20 chunks at once to prevent memory overflow
        self.chunk_batch_size = 10  # Process in smaller batches to manage memory better
        
        # Retry configuration
        self.max_retries = settings.ocr_max_retries
        self.retry_delay = settings.ocr_retry_delay  # seconds
    
    def _split_image_into_chunks(self, image: np.ndarray) -> List[Tuple[np.ndarray, Tuple[int, int]]]:
        """
        Split image into overlapping chunks for detailed text extraction.
        
        Args:
            image: OpenCV grayscale image (numpy array)
            
        Returns:
            List of tuples containing (chunk_image, chunk_position)
        """
        try:
            height, width = image.shape
            chunk_width, chunk_height = self.chunk_size
            overlap = self.chunk_overlap
            
            chunks = []
            
            # Calculate step sizes
            step_x = chunk_width - overlap
            step_y = chunk_height - overlap
            
            # Generate chunks
            for y in range(0, height, step_y):
                for x in range(0, width, step_x):
                    # Calculate chunk boundaries
                    left = x
                    top = y
                    right = min(x + chunk_width, width)
                    bottom = min(y + chunk_height, height)
                    
                    # Extract chunk using OpenCV array slicing
                    chunk = image[top:bottom, left:right]
                    
                    # Only add chunks that are large enough to be meaningful
                    chunk_height_actual, chunk_width_actual = chunk.shape
                    if chunk_width_actual >= 200 and chunk_height_actual >= 200:
                        chunks.append((chunk, (x, y)))
            
            logger.info(f"Split image into {len(chunks)} chunks for OCR analysis")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to split image into chunks: {str(e)}")
            raise Exception(f"Failed to split image into chunks: {str(e)}")
    
    def _adjust_coordinates_for_chunk(
        self, 
        bbox: List[List[int]], 
        chunk_position: Tuple[int, int]
    ) -> List[List[int]]:
        """
        Adjust text coordinates from chunk coordinates to full image coordinates.
        
        Args:
            bbox: Bounding box coordinates in chunk space
            chunk_position: Position of the chunk in the full image (x, y)
            
        Returns:
            Adjusted bounding box coordinates in full image space
        """
        chunk_x, chunk_y = chunk_position
        adjusted_bbox = []
        
        for point in bbox:
            adjusted_point = [point[0] + chunk_x, point[1] + chunk_y]
            adjusted_bbox.append(adjusted_point)
        
        return adjusted_bbox
    
    async def extract_text_from_chunk(
        self, 
        chunk_image: np.ndarray, 
        chunk_position: Tuple[int, int],
        page_number: int
    ) -> List[TextDetection]:
        """
        Extract text from a single image chunk using EasyOCR with retry logic.
        
        Args:
            chunk_image: OpenCV grayscale image chunk (numpy array)
            chunk_position: Position of the chunk (x, y)
            page_number: Page number being processed
            
        Returns:
            List of TextDetection objects with text and coordinates
        """
        async with self.semaphore:  # Rate limiting
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    logger.info(f"Starting OCR for page {page_number}, chunk at {chunk_position} (attempt {attempt + 1})")
                    
                    # Apply additional preprocessing for better OCR accuracy
                    processed_chunk = self._preprocess_chunk_for_ocr(chunk_image)
                    
                    # Perform OCR with EasyOCR (EasyOCR accepts both grayscale and color images)
                    results = self.reader.readtext(
                        processed_chunk,
                        detail=1,  # Get detailed results with coordinates
                        # Accuracy-focused settings for grayscale images
                    )
                    
                    # Clean up processed chunk to free memory immediately
                    del processed_chunk
                    
                    # Process results
                    text_detections = []
                    for bbox, text, confidence in results:
                        # Filter out low confidence detections
                        if confidence >= settings.ocr_confidence_threshold:
                            # Adjust coordinates to full image space
                            adjusted_bbox = self._adjust_coordinates_for_chunk(bbox, chunk_position)
                            
                            # Clean text
                            cleaned_text = text.strip()
                            if cleaned_text:  # Only add non-empty text
                                detection = TextDetection(
                                    text=cleaned_text,
                                    bbox=adjusted_bbox,
                                    confidence=confidence,
                                    chunk_position=chunk_position
                                )
                                text_detections.append(detection)
                    
                    # Clean up OCR results to free memory
                    del results
                    
                    processing_time = time.time() - start_time
                    logger.info(f"OCR completed for chunk {chunk_position}: {len(text_detections)} text detections in {processing_time:.2f} seconds")
                    
                    if text_detections:
                        logger.info(f"Texts detected in chunk {chunk_position}: {[td.text for td in text_detections[:5]]}...")
                    
                    return text_detections
                    
                except Exception as e:
                    logger.error(f"OCR attempt {attempt + 1} failed for chunk {chunk_position}: {str(e)}")
                    
                    if attempt < self.max_retries - 1:
                        logger.info(f"Retrying OCR for chunk {chunk_position} in {self.retry_delay} seconds...")
                        await asyncio.sleep(self.retry_delay)
                        self.retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"All OCR attempts failed for chunk {chunk_position}")
                        return []
            
            return []
    
    def _preprocess_chunk_for_ocr(self, chunk: np.ndarray) -> np.ndarray:
        """
        Apply additional preprocessing to grayscale chunk for better OCR accuracy.
        
        Args:
            chunk: OpenCV grayscale image chunk
            
        Returns:
            Preprocessed grayscale image
        """
        try:
            # Apply Gaussian blur to reduce noise (optional, can improve accuracy)
            # denoised = cv2.GaussianBlur(chunk, (3, 3), 0)
            
            # Apply histogram equalization to improve contrast
            equalized = cv2.equalizeHist(chunk)
            
            # Apply slight sharpening using unsharp masking (optional)
            # blurred = cv2.GaussianBlur(equalized, (0, 0), 2.0)
            # sharpened = cv2.addWeighted(equalized, 1.5, blurred, -0.5, 0)
            
            return equalized
            
        except Exception as e:
            logger.warning(f"Preprocessing failed, using original chunk: {str(e)}")
            return chunk

    def _convert_pil_to_grayscale_opencv(self, pil_image) -> np.ndarray:
        """
        Convert PIL Image to OpenCV grayscale format.
        
        Args:
            pil_image: PIL Image object (can be RGB or RGBA)
            
        Returns:
            OpenCV grayscale image as numpy array
        """
        try:
            # Convert PIL to OpenCV format (RGB to BGR)
            if pil_image.mode == 'RGBA':
                # Convert RGBA to RGB first
                pil_rgb = pil_image.convert('RGB')
                opencv_bgr = cv2.cvtColor(np.array(pil_rgb), cv2.COLOR_RGB2BGR)
            elif pil_image.mode == 'RGB':
                # Convert RGB to BGR
                opencv_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            else:
                # Already grayscale or other format
                opencv_bgr = np.array(pil_image)
            
            # Convert to grayscale using OpenCV
            if len(opencv_bgr.shape) == 3:
                grayscale = cv2.cvtColor(opencv_bgr, cv2.COLOR_BGR2GRAY)
            else:
                grayscale = opencv_bgr
            
            logger.info(f"Converted PIL image to grayscale OpenCV format: {grayscale.shape}")
            return grayscale
            
        except Exception as e:
            logger.error(f"Failed to convert PIL to OpenCV grayscale: {str(e)}")
            raise Exception(f"Failed to convert PIL to OpenCV grayscale: {str(e)}")

    async def extract_text_from_image(
        self, 
        pil_image, 
        page_number: int
    ) -> Dict[str, any]:
        """
        Extract all text from an image using chunk-based OCR processing with grayscale preprocessing.
        
        Args:
            pil_image: PIL Image object (will be converted to grayscale OpenCV format)
            page_number: Page number being processed
            
        Returns:
            Dictionary containing:
            - 'full_text': Complete extracted text
            - 'text_detections': List of TextDetection objects with coordinates
            - 'processing_time': Total processing time
        """
        try:
            start_time = time.time()
            logger.info(f"Starting chunk-based OCR for page {page_number}")
            
            # Convert PIL image to OpenCV grayscale format for better OCR performance
            logger.info(f"Converting PIL image to grayscale OpenCV format for page {page_number}")
            opencv_grayscale = self._convert_pil_to_grayscale_opencv(pil_image)
            logger.info(f"Grayscale image shape: {opencv_grayscale.shape}")
            
            # Split image into chunks
            logger.info(f"Splitting grayscale image into chunks for page {page_number}")
            chunks = self._split_image_into_chunks(opencv_grayscale)
            
            if not chunks:
                logger.warning(f"No valid chunks created for page {page_number}")
                return {
                    'full_text': '',
                    'text_detections': [],
                    'processing_time': time.time() - start_time
                }
            
            logger.info(f"Created {len(chunks)} grayscale chunks for OCR analysis")
            
            # Process chunks in batches to manage memory usage
            logger.info(f"Executing {len(chunks)} OCR tasks in batches of {self.chunk_batch_size} on grayscale chunks")
            chunk_results = []
            
            # Process chunks in smaller batches to prevent memory overflow
            for i in range(0, len(chunks), self.chunk_batch_size):
                batch_end = min(i + self.chunk_batch_size, len(chunks))
                batch_chunks = chunks[i:batch_end]
                
                logger.info(f"Processing OCR batch {i//self.chunk_batch_size + 1}/{(len(chunks) + self.chunk_batch_size - 1)//self.chunk_batch_size}: chunks {i+1}-{batch_end}")
                
                # Create tasks for current batch
                batch_tasks = []
                for chunk_image, chunk_position in batch_chunks:
                    task = self.extract_text_from_chunk(
                        chunk_image, 
                        chunk_position, 
                        page_number
                    )
                    batch_tasks.append(task)
                
                # Execute current batch concurrently
                batch_chunk_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                chunk_results.extend(batch_chunk_results)
                
                # Force garbage collection after each batch to free memory
                del batch_tasks
                del batch_chunks
                gc.collect()
                
                logger.info(f"Completed batch {i//self.chunk_batch_size + 1}, processed {len(batch_chunk_results)} chunks")
            
            # Collect all text detections from all chunks
            all_text_detections = []
            for i, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in OCR chunk {i}: {str(result)}")
                elif isinstance(result, list):
                    all_text_detections.extend(result)
                else:
                    logger.warning(f"Unexpected result type from OCR chunk {i}: {type(result)}")
            
            # Combine all text into a single document
            full_text = self._combine_text_detections(all_text_detections)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            logger.info(f"Grayscale OCR completed for page {page_number}: {len(all_text_detections)} text detections, {len(full_text)} characters in {processing_time:.2f} seconds")
            
            if full_text:
                logger.info(f"Sample text from grayscale OCR on page {page_number}: {full_text[:200]}...")
            
            # Clean up large variables to free memory
            del chunks
            del chunk_results
            gc.collect()
            
            return {
                'full_text': full_text,
                'text_detections': all_text_detections,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Grayscale OCR processing failed for page {page_number}: {str(e)}")
            return {
                'full_text': '',
                'text_detections': [],
                'processing_time': time.time() - start_time
            }
    
    def _combine_text_detections(self, text_detections: List[TextDetection]) -> str:
        """
        Combine text detections into a coherent document.
        
        Args:
            text_detections: List of TextDetection objects
            
        Returns:
            Combined text document
        """
        if not text_detections:
            return ""
        
        # Sort detections by vertical position (top to bottom)
        sorted_detections = sorted(text_detections, key=lambda td: td.bbox[0][1])
        
        # Combine text with appropriate spacing
        combined_text = ""
        current_y = -1
        line_threshold = 50  # Pixels threshold for same line
        
        for detection in sorted_detections:
            text = detection.text
            y_position = detection.bbox[0][1]
            
            # Add line break if significantly different Y position
            if current_y != -1 and abs(y_position - current_y) > line_threshold:
                combined_text += "\n"
            
            # Add text with space if not at beginning
            if combined_text and not combined_text.endswith('\n'):
                combined_text += " "
            
            combined_text += text
            current_y = y_position
        
        return combined_text.strip()
