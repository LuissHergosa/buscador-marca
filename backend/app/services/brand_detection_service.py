"""
Brand detection service using Langchain and Google Gemini 2.5.
"""

import base64
import time
from typing import List, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from PIL import Image

from ..config import settings
from ..models.brand_detection import BrandDetectionCreate


class BrandDetectionService:
    """Service for brand detection using Google Gemini 2.5."""
    
    def __init__(self):
        """Initialize brand detection service."""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
            max_retries=5,
            temperature=0.1
        )
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """
        Encode image to base64 string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to encode image: {str(e)}")
    
    def _create_prompt(self, page_number: int) -> str:
        """
        Create prompt for brand detection.
        
        Args:
            page_number: Page number being analyzed
            
        Returns:
            Formatted prompt string
        """
        return f"""
        Analiza esta imagen de un plano arquitectónico (página {page_number}) y detecta todas las marcas comerciales mencionadas.

        Instrucciones específicas:
        1. Busca nombres de marcas comerciales en el texto visible
        2. Identifica marcas en especificaciones técnicas, equipos, materiales, etc.
        3. Incluye solo nombres exactos de marcas (no descripciones genéricas)
        4. Si no encuentras marcas, responde con una lista vacía
        5. Responde SOLO con un JSON válido en el siguiente formato:
        
        {{
            "brands_detected": [
                "Nombre exacto de la marca 1",
                "Nombre exacto de la marca 2"
            ],
            "page_number": {page_number}
        }}
        
        Ejemplos de marcas que podrías encontrar:
        - Nombres de equipos (Samsung, LG, Bosch, etc.)
        - Materiales de construcción (Cemex, Holcim, etc.)
        - Equipos de iluminación (Philips, Osram, etc.)
        - Sistemas de seguridad (Honeywell, Johnson Controls, etc.)
        - Equipos de aire acondicionado (Carrier, Trane, etc.)
        
        Responde únicamente con el JSON, sin texto adicional.
        """
    
    async def detect_brands_in_image(
        self, 
        image_path: str, 
        page_number: int
    ) -> BrandDetectionCreate:
        """
        Detect brands in a single image using Gemini 2.5.
        
        Args:
            image_path: Path to the image file
            page_number: Page number being analyzed
            
        Returns:
            BrandDetectionCreate object with detected brands
        """
        try:
            start_time = time.time()
            
            # Encode image to base64
            base64_image = self._encode_image_to_base64(image_path)
            
            # Create prompt
            prompt = self._create_prompt(page_number)
            
            # Create message with image
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
            response = await self.llm.ainvoke([message])
            
            # Parse response
            response_text = response.content
            
            # Extract JSON from response (handle cases where response might have extra text)
            import json
            import re
            
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)
            else:
                # If no JSON found, try to parse the entire response
                result = json.loads(response_text)
            
            # Validate response structure
            if not isinstance(result, dict):
                raise Exception("Invalid response format: expected dictionary")
            
            if "brands_detected" not in result:
                raise Exception("Invalid response format: missing 'brands_detected' field")
            
            if "page_number" not in result:
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
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            return BrandDetectionCreate(
                page_number=page_number,
                brands_detected=brands_detected
            )
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise Exception(f"Brand detection failed: {str(e)}")
    
    async def detect_brands_in_multiple_images(
        self, 
        image_paths: List[str]
    ) -> List[BrandDetectionCreate]:
        """
        Detect brands in multiple images concurrently.
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of BrandDetectionCreate objects
        """
        import asyncio
        
        try:
            # Create tasks for concurrent processing
            tasks = []
            for i, image_path in enumerate(image_paths):
                page_number = i + 1
                task = self.detect_brands_in_image(image_path, page_number)
                tasks.append(task)
            
            # Execute tasks concurrently with semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(settings.max_concurrent_pages)
            
            async def process_with_semaphore(task):
                async with semaphore:
                    return await task
            
            # Process tasks with concurrency limit
            results = await asyncio.gather(
                *[process_with_semaphore(task) for task in tasks],
                return_exceptions=True
            )
            
            # Filter out exceptions and return valid results
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error processing page {i+1}: {str(result)}")
                    # Create empty result for failed pages
                    valid_results.append(BrandDetectionCreate(
                        page_number=i+1,
                        brands_detected=[]
                    ))
                else:
                    valid_results.append(result)
            
            return valid_results
            
        except Exception as e:
            raise Exception(f"Failed to process multiple images: {str(e)}")


# Global brand detection service instance
brand_detection_service = BrandDetectionService()
