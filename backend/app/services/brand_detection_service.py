"""
Brand detection service using OCR + LLM pipeline.
First extracts text using EasyOCR, then analyzes text with Google Gemini 2.5.
Optimized for performance with parallel processing and connection pooling.
"""

import base64
import io
import json
import logging
import re
import time
import asyncio
from typing import List, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage
from PIL import Image

from ..config import settings
from ..models.brand_detection import BrandDetectionCreate
from .ocr_service import OCRService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrandDetectionService:
    """Service for brand detection using OCR + LLM pipeline with performance optimizations."""
    
    def __init__(self):
        """Initialize brand detection service with OCR + LLM pipeline."""
        logger.info("Initializing BrandDetectionService with OCR + LLM pipeline")
        
        # Initialize OCR service
        self.ocr_service = OCRService()
        
        # Create multiple LLM instances for parallel processing
        self.llm_instances = []
        max_instances = min(5, settings.max_concurrent_pages)  # Limit instances to avoid rate limits
        
        for i in range(max_instances):
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model,
                google_api_key=settings.gemini_api_key,
                max_retries=3,  # Reduced retries for faster failure
                temperature=0.1,
                # Optimize for speed
                max_tokens=1000,  # Limit response size for faster processing
                timeout=0  # No timeout
            )
            self.llm_instances.append(llm)
        
        logger.info(f"BrandDetectionService initialized with {len(self.llm_instances)} LLM instances and OCR service")
        
        # Create semaphore for rate limiting
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_pages)
    
    def _create_text_analysis_prompt(self, page_number: int, extracted_text: str) -> str:
        """
        Create optimized prompt for brand detection from extracted text.
        
        Args:
            page_number: Page number being analyzed
            extracted_text: Complete text extracted from the page
            
        Returns:
            Formatted prompt string for text analysis
        """
        logger.info(f"Creating text analysis prompt for page {page_number}")
        
        return f"""
        Eres un experto analista especializado en detectar marcas comerciales en texto extraído de planos arquitectónicos. 
        Analiza el siguiente texto extraído de un plano arquitectónico (página {page_number}) y detecta TODAS las marcas comerciales mencionadas.

        TEXTO EXTRAÍDO DEL PLANO (PÁGINA {page_number}):
        {extracted_text}

        METODOLOGÍA DE ANÁLISIS SISTEMÁTICO:
        
        1. **ANÁLISIS COMPLETO DEL TEXTO**:
           - Revisa cada palabra y frase del texto extraído
           - Examina TODAS las líneas y párrafos sin importar el contexto
           - Busca marcas en diferentes formatos (mayúsculas, minúsculas, mixtas)
           - Considera variaciones de escritura y abreviaciones
        
        2. **TIPOS DE MARCAS A DETECTAR**:
           - Equipos eléctricos y electrónicos (Samsung, LG, Bosch, Siemens, Schneider, ABB, etc.)
           - Materiales de construcción (Cemex, Holcim, Cementos Argos, Corona, etc.)
           - Equipos de iluminación (Philips, Osram, GE, Sylvania, etc.)
           - Sistemas de seguridad (Honeywell, Johnson Controls, Bosch Security, etc.)
           - Equipos de aire acondicionado (Carrier, Trane, York, Daikin, Mitsubishi, etc.)
           - Herramientas y equipos (Makita, DeWalt, Milwaukee, Bosch, Hilti, etc.)
           - Pinturas y acabados (Sherwin-Williams, PPG, Comex, Pinturas Osel, etc.)
           - Plomería y sanitarios (Kohler, Toto, American Standard, Corona, etc.)
           - Pisos y acabados (Armstrong, Mohawk, Porcelanite, etc.)
           - Equipos de cocina (Whirlpool, Samsung, LG, Bosch, etc.)
           - Sistemas de audio/video (Sony, Samsung, LG, Bose, etc.)
           - Equipos de cómputo (Dell, HP, Lenovo, Apple, etc.)
           - Equipos de red (Cisco, TP-Link, Netgear, etc.)
           - Cualquier otra marca comercial reconocible
        
        3. **CRITERIOS DE DETECCIÓN**:
           - Busca nombres de marcas completos y abreviados
           - Incluye variaciones de escritura (ej: "Samsung" y "SAMSUNG")
           - Detecta marcas en combinación con números de modelo
           - Considera marcas en contexto de especificaciones
           - Incluye marcas mencionadas en listas de materiales
           - Detecta marcas en notas técnicas y especificaciones
           - Considera marcas en diferentes idiomas (español e inglés)
        
        4. **EXCLUSIONES ESPECÍFICAS**:
           - Hergon y todas sus variantes (Grupo Hergon SA, Hergon SA, etc.)
           - Nombres genéricos de productos (ej: "lámpara", "interruptor")
           - Nombres de materiales genéricos (ej: "concreto", "acero")
           - Nombres de empresas que no son marcas comerciales
           - Texto que no representa marcas comerciales
           - Palabras comunes que no son marcas
        
        5. **PROCESO DE VALIDACIÓN**:
           - Verifica que cada detección sea una marca comercial real
           - Confirma que el texto detectado sea legible y completo
           - Asegúrate de que no sean nombres genéricos o descriptivos
           - Valida que las marcas estén en contexto comercial
        
        EJEMPLOS DE DETECCIÓN CORRECTA:
        ✅ "Samsung" 
        ✅ "LG" 
        ✅ "Bosch" 
        ✅ "Philips" 
        ✅ "Carrier" 
        ✅ "Kohler" 
        ✅ "Cemex" 
        ❌ "Hergon" (excluido)
        ❌ "lámpara LED" (descripción genérica)
        ❌ "interruptor simple" (descripción genérica)
        
        INSTRUCCIONES FINALES:
        - Analiza exhaustivamente todo el texto proporcionado
        - No te apresures, revisa cada palabra con atención
        - Si no encuentras marcas, responde con una lista vacía
        - Responde ÚNICAMENTE con el JSON especificado
        - Asegúrate de que el JSON sea válido y completo
        
        Formato de respuesta requerido:
        {{
            "brands_detected": [
                "Nombre exacto de la marca 1",
                "Nombre exacto de la marca 2"
            ],
            "page_number": {page_number},
            "text_analysis_summary": "Resumen breve del análisis realizado"
        }}

        Responde únicamente con el JSON, sin texto adicional ni explicaciones.
        """
    
    async def detect_brands_from_text(
        self, 
        extracted_text: str, 
        page_number: int
    ) -> List[str]:
        """
        Detect brands from extracted text using Gemini 2.5.
        
        Args:
            extracted_text: Complete text extracted from the page
            page_number: Page number being analyzed
            
        Returns:
            List of detected brands
        """
        async with self.semaphore:  # Rate limiting
            try:
                start_time = time.time()
                logger.info(f"Starting text-based brand detection for page {page_number}")
                logger.info(f"Text length: {len(extracted_text)} characters")
                
                if not extracted_text or extracted_text.strip() == "":
                    logger.info(f"No text extracted for page {page_number} - no brands to detect")
                    return []
                
                # Create text analysis prompt
                prompt = self._create_text_analysis_prompt(page_number, extracted_text)
                
                # Create message with text
                message = HumanMessage(content=prompt)
                
                # Get response from Gemini
                try:
                    response = await self.llm_instances[page_number % len(self.llm_instances)].ainvoke([message])
                    response_text = response.content
                    logger.info(f"Received text analysis response for page {page_number}: {len(response_text)} characters")
                except Exception as e:
                    logger.error(f"Error getting Gemini response for page {page_number}: {str(e)}")
                    return []
                
                # Parse response
                if not response_text or response_text.strip() == "":
                    logger.info(f"Empty response for page {page_number} - no brands detected")
                    return []
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                else:
                    logger.warning(f"No JSON pattern found in response for page {page_number}, trying to parse entire response")
                    result = json.loads(response_text)
                
                # Validate and extract brands
                if isinstance(result, dict) and "brands_detected" in result:
                    brands = result["brands_detected"]
                    if isinstance(brands, list):
                        # Filter out empty strings and normalize
                        brands = [brand.strip() for brand in brands if brand and brand.strip()]
                        
                        # Filter out Hergon and its variants
                        excluded_brands = ['hergon', 'grupo hergon', 'hergon sa', 'grupo hergon sa']
                        brands = [
                            brand for brand in brands
                            if not any(excluded.lower() in brand.lower() for excluded in excluded_brands)
                        ]
                        
                        processing_time = time.time() - start_time
                        logger.info(f"Text analysis completed for page {page_number}: {len(brands)} brands found in {processing_time:.2f} seconds")
                        
                        if brands:
                            logger.info(f"Brands detected on page {page_number}: {brands}")
                        
                        return brands
                
                logger.warning(f"Invalid response format for page {page_number}")
                return []
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse response as JSON for page {page_number}: {str(e)}")
                return []
            except Exception as e:
                logger.error(f"Text analysis failed for page {page_number}: {str(e)}")
                return []
    
    async def detect_brands_in_image(
        self, 
        image, 
        page_number: int
    ) -> BrandDetectionCreate:
        """
        Detect brands in a single image using OCR + LLM pipeline.
        
        Args:
            image: PIL Image object
            page_number: Page number being analyzed
            
        Returns:
            BrandDetectionCreate object with detected brands
        """
        try:
            start_time = time.time()
            logger.info(f"Starting OCR + LLM brand detection for page {page_number}")
            logger.info(f"Image size: {image.size}, Mode: {image.mode}")
            
            # Step 1: Extract text using OCR
            logger.info(f"Step 1: Extracting text using OCR for page {page_number}")
            ocr_result = await self.ocr_service.extract_text_from_image(image, page_number)
            
            extracted_text = ocr_result['full_text']
            ocr_processing_time = ocr_result['processing_time']
            
            logger.info(f"OCR completed for page {page_number}: {len(extracted_text)} characters extracted in {ocr_processing_time:.2f} seconds")
            
            if not extracted_text or extracted_text.strip() == "":
                logger.warning(f"No text extracted from page {page_number} - no brands to detect")
                return BrandDetectionCreate(
                    page_number=page_number,
                    brands_detected=[]
                )
            
            # Step 2: Analyze text for brands using LLM
            logger.info(f"Step 2: Analyzing extracted text for brands on page {page_number}")
            detected_brands = await self.detect_brands_from_text(extracted_text, page_number)
            
            # Calculate total processing time
            total_processing_time = time.time() - start_time
            logger.info(f"OCR + LLM brand detection completed for page {page_number}: {len(detected_brands)} brands found in {total_processing_time:.2f} seconds")
            
            if detected_brands:
                logger.info(f"Brands detected on page {page_number}: {detected_brands}")
            
            return BrandDetectionCreate(
                page_number=page_number,
                brands_detected=detected_brands
            )
            
        except Exception as e:
            logger.error(f"OCR + LLM brand detection failed for page {page_number}: {str(e)}")
            # Return empty result instead of raising exception
            return BrandDetectionCreate(
                page_number=page_number,
                brands_detected=[]
            )
    
    async def detect_brands_in_multiple_images(
        self, 
        images: List[Image.Image]
    ) -> List[BrandDetectionCreate]:
        """
        Detect brands in multiple images with optimized parallel processing.
        
        Args:
            images: List of PIL Image objects
            
        Returns:
            List of BrandDetectionCreate objects
        """
        try:
            logger.info(f"Starting optimized brand detection for {len(images)} images")
            
            # Create tasks for concurrent processing with better error handling
            tasks = []
            for i, image in enumerate(images):
                page_number = i + 1
                logger.info(f"Creating task for page {page_number}")
                task = self.detect_brands_in_image(image, page_number)
                tasks.append(task)
            
            # Execute tasks concurrently with improved error handling
            logger.info(f"Executing {len(tasks)} tasks concurrently")
            results = await asyncio.gather(
                *tasks,
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
