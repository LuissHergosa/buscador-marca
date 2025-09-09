"""
Brand detection service using OCR + LLM pipeline.
First extracts text using EasyOCR, then analyzes text with Google Gemini 2.5.
Optimized for performance with parallel processing and connection pooling.
"""

import json
import logging
import re
import time
import asyncio
import gc
from typing import List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage

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
           - Analiza nombres de modelos y números de serie que puedan indicar marcas
        
        2. **TIPOS DE MARCAS A DETECTAR**:
           - Equipos eléctricos y electrónicos (Samsung, LG, Bosch, Siemens, Schneider, ABB, General Electric, Westinghouse, etc.)
           - Materiales de construcción (Cemex, Holcim, Cementos Argos, Corona, LafargeHolcim, etc.)
           - Equipos de iluminación (Philips, Osram, GE Lighting, Sylvania, Cree, etc.)
           - Sistemas de seguridad (Honeywell, Johnson Controls, Bosch Security, Axis, Hikvision, etc.)
           - Equipos de aire acondicionado (Carrier, Trane, York, Daikin, Mitsubishi Electric, Lennox, etc.)
           - Herramientas y equipos (Makita, DeWalt, Milwaukee, Bosch, Hilti, Caterpillar, etc.)
           - Pinturas y acabados (Sherwin-Williams, PPG, Comex, Pinturas Osel, Benjamin Moore, etc.)
           - Plomería y sanitarios (Kohler, Toto, American Standard, Corona, Moen, Delta, etc.)
           - Pisos y acabados (Armstrong, Mohawk, Porcelanite, Tarkett, Shaw, etc.)
           - Equipos de cocina (Whirlpool, Samsung, LG, Bosch, KitchenAid, Frigidaire, etc.)
           - Sistemas de audio/video (Sony, Samsung, LG, Bose, JBL, Yamaha, etc.)
           - Equipos de cómputo (Dell, HP, Lenovo, Apple, IBM, Microsoft, etc.)
           - Equipos de red (Cisco, TP-Link, Netgear, Ubiquiti, D-Link, etc.)
           - Equipos médicos (Philips Healthcare, GE Healthcare, Siemens Healthineers, etc.)
           - Elevadores y escaleras (Otis, Schindler, KONE, ThyssenKrupp, etc.)
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
           - Hergonsa y todas sus variantes (HERGONSA, hergonsa, Grupo Hergonsa, Hergonsa SA, etc.)
           - Nombres genéricos de productos (ej: "lámpara", "interruptor", "cable", "tubo")
           - Nombres de materiales genéricos (ej: "concreto", "acero", "aluminio", "cobre")
           - Nombres de empresas que no son marcas comerciales reconocidas
           - Texto que no representa marcas comerciales (códigos, referencias, medidas)
           - Palabras comunes que no son marcas (colores, formas, tamaños)
           - Términos técnicos genéricos (voltaje, amperaje, frecuencia)
        
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
        ❌ "Hergonsa" (excluido - nombre de la empresa cliente)
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
    
    async def detect_brands_in_image_file(
        self, 
        image_path: str, 
        page_number: int
    ) -> BrandDetectionCreate:
        """
        Detect brands in a grayscale image file using memory-efficient OCR + LLM pipeline.
        
        Process:
        1. Load grayscale image from file for OCR analysis
        2. Extract text from all chunks using memory-efficient processing
        3. Analyze the complete page text with LLM for brand detection
        4. Free all memory immediately after processing
        
        Args:
            image_path: Path to the grayscale image file
            page_number: Page number being analyzed
            
        Returns:
            BrandDetectionCreate object with detected brands
        """
        try:
            start_time = time.time()
            logger.info(f"Starting memory-efficient OCR + LLM brand detection for page {page_number}")
            logger.info(f"Image file: {image_path}")
            
            # Step 1: Extract text using memory-efficient chunk-based OCR
            logger.info(f"Step 1: Extracting text using memory-efficient OCR for page {page_number}")
            ocr_result = await self.ocr_service.extract_text_from_image_file(image_path, page_number)
            
            extracted_text = ocr_result['full_text']
            text_detections = ocr_result['text_detections']
            ocr_processing_time = ocr_result['processing_time']
            
            logger.info(f"Memory-efficient OCR completed for page {page_number}: {len(extracted_text)} characters extracted from {len(text_detections)} text detections in {ocr_processing_time:.2f} seconds")
            
            if not extracted_text or extracted_text.strip() == "":
                logger.warning(f"No text extracted from page {page_number} - no brands to detect")
                return BrandDetectionCreate(
                    page_number=page_number,
                    brands_detected=[]
                )
            
            # Step 2: Analyze the complete page text for brands using LLM
            logger.info(f"Step 2: Analyzing complete page text for brands on page {page_number}")
            logger.info(f"Text sample for LLM analysis: {extracted_text[:500]}...")
            
            detected_brands = await self.detect_brands_from_text(extracted_text, page_number)
            
            # Clear large text variables to free memory immediately
            del extracted_text
            del text_detections
            del ocr_result
            gc.collect()
            
            # Calculate total processing time
            total_processing_time = time.time() - start_time
            logger.info(f"Memory-efficient OCR + LLM brand detection completed for page {page_number}: {len(detected_brands)} brands found in {total_processing_time:.2f} seconds")
            
            if detected_brands:
                logger.info(f"Brands detected on page {page_number}: {detected_brands}")
            else:
                logger.info(f"No brands detected on page {page_number}")
            
            return BrandDetectionCreate(
                page_number=page_number,
                brands_detected=detected_brands
            )
            
        except Exception as e:
            logger.error(f"Memory-efficient OCR + LLM brand detection failed for page {page_number}: {str(e)}")
            # Return empty result instead of raising exception
            return BrandDetectionCreate(
                page_number=page_number,
                brands_detected=[]
            )
    
    async def detect_brands_in_multiple_image_files(
        self, 
        image_paths: List[str]
    ) -> List[BrandDetectionCreate]:
        """
        Detect brands in multiple grayscale image files with memory-efficient parallel processing.
        
        Args:
            image_paths: List of paths to grayscale image files
            
        Returns:
            List of BrandDetectionCreate objects
        """
        try:
            logger.info(f"Starting memory-efficient brand detection for {len(image_paths)} image files")
            
            # Create tasks for concurrent processing with better error handling
            tasks = []
            for i, image_path in enumerate(image_paths):
                page_number = i + 1
                logger.info(f"Creating task for page {page_number}: {image_path}")
                task = self.detect_brands_in_image_file(image_path, page_number)
                tasks.append(task)
            
            # Execute tasks concurrently with improved error handling
            logger.info(f"Executing {len(tasks)} memory-efficient tasks concurrently")
            results = await asyncio.gather(
                *tasks,
                return_exceptions=True
            )
            
            # Filter out exceptions and return valid results
            valid_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing page {i+1} from {image_paths[i]}: {str(result)}")
                    # Create empty result for failed pages
                    valid_results.append(BrandDetectionCreate(
                        page_number=i+1,
                        brands_detected=[]
                    ))
                else:
                    valid_results.append(result)
            
            logger.info(f"Memory-efficient brand detection completed: {len(valid_results)} results, {len([r for r in results if isinstance(r, Exception)])} errors")
            return valid_results
            
        except Exception as e:
            logger.error(f"Failed to process multiple image files: {str(e)}")
            raise Exception(f"Failed to process multiple image files: {str(e)}")


# Global brand detection service instance
brand_detection_service = BrandDetectionService()
