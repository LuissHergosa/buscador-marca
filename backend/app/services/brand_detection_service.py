"""
Brand detection service using Langchain and Google Gemini 2.5.
"""

import base64
import io
import json
import logging
import re
import time
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from PIL import Image

from ..config import settings
from ..models.brand_detection import BrandDetectionCreate

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrandDetectionService:
    """Service for brand detection using Google Gemini 2.5."""
    
    def __init__(self):
        """Initialize brand detection service."""
        logger.info("Initializing BrandDetectionService with Gemini 2.5")
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            max_retries=5,
            temperature=0.1
        )
        logger.info(f"BrandDetectionService initialized with model: {settings.gemini_model}")
    
    def _encode_image_to_base64(self, image) -> str:
        """
        Encode PIL Image to base64 string with high quality for better text detection.
        
        Args:
            image: PIL Image object
            
        Returns:
            Base64 encoded image string
        """
        try:
            logger.info(f"Encoding image to base64: Size={image.size}, Mode={image.mode}")
            
            # Convert PIL Image to bytes with high quality settings
            img_buffer = io.BytesIO()
            
            # Use high quality settings for better text preservation
            # PNG format preserves text clarity better than JPEG
            image.save(
                img_buffer, 
                format='PNG',
                optimize=False,  # Disable optimization to preserve text clarity
                quality=settings.image_quality
            )
            
            img_bytes = img_buffer.getvalue()
            encoded_size = len(img_bytes)
            logger.info(f"Image encoded successfully: {encoded_size} bytes")
            
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image: {str(e)}")
            logger.error(f"Image size: {image.size}, Mode: {image.mode}")
            raise Exception(f"Failed to encode image: {str(e)}")
    
    def _create_prompt(self, page_number: int) -> str:
        """
        Create prompt for brand detection optimized for text-based brand detection in architectural plans.
        
        Args:
            page_number: Page number being analyzed
            
        Returns:
            Formatted prompt string
        """
        logger.info(f"Creating brand detection prompt for page {page_number}")
        
        return f"""
        Analiza esta imagen de un plano arquitectónico (página {page_number}) y detecta TODAS las marcas comerciales mencionadas como texto.

        INSTRUCCIONES ESPECÍFICAS PARA DETECCIÓN DE TEXTO:
        1. **Enfoque en texto**: Busca EXCLUSIVAMENTE nombres de marcas escritos como texto en el plano
        2. **Escaneo completo**: Revisa TODO el plano, incluyendo:
           - Especificaciones técnicas
           - Notas y anotaciones
           - Leyendas y símbolos
           - Títulos de secciones
           - Detalles de equipos y materiales
        3. **Marcas como texto**: Identifica marcas que aparecen como palabras escritas, no como logos
        4. **Nombres exactos**: Captura los nombres exactos de las marcas tal como aparecen
        5. **Incluir variaciones**: Si una marca aparece con diferentes variaciones (ej: "Samsung" y "SAMSUNG"), incluye ambas
        6. **No descripciones**: Solo nombres de marcas, no descripciones genéricas de productos

        MARCAS EXCLUIDAS (NO DETECTAR):
        - Hergon y todas sus variantes (Grupo Hergon SA, Hergon SA, etc.)

        TIPOS DE MARCAS A BUSCAR EN TEXTO:
        - Equipos eléctricos y electrónicos (Samsung, LG, Bosch, Siemens, etc.)
        - Materiales de construcción (Cemex, Holcim, Cementos Argos, etc.)
        - Equipos de iluminación (Philips, Osram, GE, etc.)
        - Sistemas de seguridad (Honeywell, Johnson Controls, etc.)
        - Equipos de aire acondicionado (Carrier, Trane, York, etc.)
        - Herramientas y equipos (Makita, DeWalt, Milwaukee, etc.)
        - Pinturas y acabados (Sherwin-Williams, PPG, etc.)
        - Plomería y sanitarios (Kohler, Toto, American Standard, etc.)
        - Pisos y acabados (Armstrong, Mohawk, etc.)
        - Cualquier otra marca comercial mencionada como texto

        IMPORTANTE:
        - Lee TODO el texto visible en el plano
        - Busca en especificaciones, notas, leyendas y cualquier área con texto
        - Las marcas pueden aparecer en cualquier parte del plano como texto
        - EXCLUYE específicamente cualquier variante de "Hergon"
        - Si no encuentras marcas, responde con una lista vacía
        - Responde SOLO con un JSON válido

        Formato de respuesta:
        {{
            "brands_detected": [
                "Nombre exacto de la marca 1",
                "Nombre exacto de la marca 2"
            ],
            "page_number": {page_number}
        }}

        Responde únicamente con el JSON, sin texto adicional.
        """
    
    async def detect_brands_in_image(
        self, 
        image, 
        page_number: int
    ) -> BrandDetectionCreate:
        """
        Detect brands in a single image using Gemini 2.5.
        
        Args:
            image: PIL Image object
            page_number: Page number being analyzed
            
        Returns:
            BrandDetectionCreate object with detected brands
        """
        try:
            start_time = time.time()
            logger.info(f"Starting brand detection for page {page_number}")
            logger.info(f"Image size: {image.size}, Mode: {image.mode}")
            
            # Encode image to base64
            logger.info(f"Encoding image for page {page_number}")
            base64_image = self._encode_image_to_base64(image)
            
            # Create prompt
            logger.info(f"Creating prompt for page {page_number}")
            prompt = self._create_prompt(page_number)
            
            # Create message with image
            logger.info(f"Sending request to Gemini for page {page_number}")
            message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            )
            
            # Get response from Gemini
            logger.info(f"Waiting for Gemini response for page {page_number}")
            response = await self.llm.ainvoke([message])
            
            # Parse response
            response_text = response.content
            logger.info(f"Received response from Gemini for page {page_number}: {len(response_text)} characters")
            
            # Extract JSON from response (handle cases where response might have extra text)
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                logger.info(f"Found JSON in response for page {page_number}")
                result = json.loads(json_str)
            else:
                # If no JSON found, try to parse the entire response
                logger.warning(f"No JSON pattern found in response for page {page_number}, trying to parse entire response")
                result = json.loads(response_text)
            
            # Validate response structure
            if not isinstance(result, dict):
                logger.error(f"Invalid response format for page {page_number}: expected dictionary")
                raise Exception("Invalid response format: expected dictionary")
            
            if "brands_detected" not in result:
                logger.error(f"Invalid response format for page {page_number}: missing 'brands_detected' field")
                raise Exception("Invalid response format: missing 'brands_detected' field")
            
            if "page_number" not in result:
                logger.error(f"Invalid response format for page {page_number}: missing 'page_number' field")
                raise Exception("Invalid response format: missing 'page_number' field")
            
            # Ensure brands_detected is a list
            brands_detected = result["brands_detected"]
            if not isinstance(brands_detected, list):
                brands_detected = [brands_detected] if brands_detected else []
            
            # Filter out empty strings and normalize
            brands_detected = [
                brand.strip() for brand in brands_detected 
                if brand and brand.strip()
            ]
            
            # Filter out Hergon and its variants
            excluded_brands = ['hergon', 'grupo hergon', 'hergon sa', 'grupo hergon sa']
            brands_detected = [
                brand for brand in brands_detected
                if not any(excluded.lower() in brand.lower() for excluded in excluded_brands)
            ]
            
            # Calculate processing time
            processing_time = time.time() - start_time
            logger.info(f"Brand detection completed for page {page_number}: {len(brands_detected)} brands found in {processing_time:.2f} seconds")
            
            if brands_detected:
                logger.info(f"Brands detected on page {page_number}: {brands_detected}")
            
            return BrandDetectionCreate(
                page_number=page_number,
                brands_detected=brands_detected
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON for page {page_number}: {str(e)}")
            logger.error(f"Response text: {response_text[:500]}...")  # Log first 500 chars
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Brand detection failed for page {page_number}: {str(e)}")
            raise Exception(f"Brand detection failed: {str(e)}")
    
    async def detect_brands_in_multiple_images(
        self, 
        images: List[Image.Image]
    ) -> List[BrandDetectionCreate]:
        """
        Detect brands in multiple images concurrently.
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            List of BrandDetectionCreate objects
        """
        import asyncio
        
        try:
            logger.info(f"Starting brand detection for {len(images)} images")
            
            # Create tasks for concurrent processing
            tasks = []
            for i, image in enumerate(images):
                page_number = i + 1
                logger.info(f"Creating task for page {page_number}")
                task = self.detect_brands_in_image(image, page_number)
                tasks.append(task)
            
            # Execute tasks concurrently with semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(settings.max_concurrent_pages)
            logger.info(f"Using semaphore with limit: {settings.max_concurrent_pages}")
            
            async def process_with_semaphore(task):
                async with semaphore:
                    return await task
            
            # Process tasks with concurrency limit
            logger.info(f"Executing {len(tasks)} tasks concurrently")
            results = await asyncio.gather(
                *[process_with_semaphore(task) for task in tasks],
                return_exceptions=True
            )
            
            # Filter out exceptions and return valid results
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing page {i+1}: {str(result)}")
                    # Create empty result for failed pages
                    valid_results.append(BrandDetectionCreate(
                        page_number=i+1,
                        brands_detected=[]
                    ))
                else:
                    valid_results.append(result)
            
            logger.info(f"Brand detection completed: {len(valid_results)} results, {len([r for r in results if isinstance(r, Exception)])} errors")
            return valid_results
            
        except Exception as e:
            logger.error(f"Failed to process multiple images: {str(e)}")
            raise Exception(f"Failed to process multiple images: {str(e)}")


# Global brand detection service instance
brand_detection_service = BrandDetectionService()
