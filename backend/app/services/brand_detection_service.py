"""
Brand detection service using Langchain and Google Gemini 2.5.
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrandDetectionService:
    """Service for brand detection using Google Gemini 2.5 with performance optimizations."""
    
    def __init__(self):
        """Initialize brand detection service with optimized settings."""
        logger.info("Initializing BrandDetectionService with Gemini 2.5 and performance optimizations")
        
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
        
        logger.info(f"BrandDetectionService initialized with {len(self.llm_instances)} LLM instances")
        
        # Create semaphore for rate limiting
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_pages)
        
        # Chunk analysis configuration - 6 chunks total
        self.num_chunks = 6  # Fixed number of chunks
        self.chunk_overlap = 100  # 100 pixels overlap between chunks for better coverage
    
    def _encode_image_to_base64(self, image) -> str:
        """
        Encode PIL Image to base64 string with optimized quality settings.
        
        Args:
            image: PIL Image object
            
        Returns:
            Base64 encoded image string
        """
        try:
            logger.info(f"Encoding image to base64: Size={image.size}, Mode={image.mode}")
            
            # Convert PIL Image to bytes with optimized settings
            img_buffer = io.BytesIO()
            
            # Use optimized settings for better performance while maintaining quality
            # PNG format preserves text clarity better than JPEG
            image.save(
                img_buffer, 
                format='PNG',
                optimize=True,  # Enable optimization for smaller file size
                quality=settings.image_quality,
                compress_level=6  # Balanced compression
            )
            
            img_bytes = img_buffer.getvalue()
            encoded_size = len(img_bytes)
            logger.info(f"Image encoded successfully: {encoded_size} bytes")
            
            return base64.b64encode(img_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encode image: {str(e)}")
            logger.error(f"Image size: {image.size}, Mode: {image.mode}")
            raise Exception(f"Failed to encode image: {str(e)}")
    
    def _split_image_into_chunks(self, image: Image.Image) -> List[Tuple[Image.Image, Tuple[int, int]]]:
        """
        Split image into exactly 6 chunks for detailed analysis.
        Uses a 2x3 grid layout to ensure uniform distribution.
        
        Args:
            image: PIL Image object
            
        Returns:
            List of tuples containing (chunk_image, chunk_position)
        """
        try:
            width, height = image.size
            overlap = self.chunk_overlap
            
            # Calculate chunk dimensions for 2x3 grid (6 chunks total)
            # 2 rows, 3 columns
            chunk_width = width // 3
            chunk_height = height // 2
            
            # Ensure minimum chunk size
            min_chunk_size = 300
            if chunk_width < min_chunk_size or chunk_height < min_chunk_size:
                logger.warning(f"Image too small for 6 chunks, using 4 chunks instead")
                # Fallback to 2x2 grid for small images
                chunk_width = width // 2
                chunk_height = height // 2
                grid_cols, grid_rows = 2, 2
            else:
                grid_cols, grid_rows = 3, 2
            
            chunks = []
            chunk_index = 0
            
            for row in range(grid_rows):
                for col in range(grid_cols):
                    # Calculate chunk boundaries with overlap
                    left = max(0, col * chunk_width - overlap)
                    top = max(0, row * chunk_height - overlap)
                    right = min(width, (col + 1) * chunk_width + overlap)
                    bottom = min(height, (row + 1) * chunk_height + overlap)
                    
                    # Extract chunk
                    chunk = image.crop((left, top, right, bottom))
                    
                    # Store chunk with its position and index
                    chunks.append((chunk, (left, top, chunk_index)))
                    chunk_index += 1
            
            logger.info(f"Split image into {len(chunks)} chunks ({grid_cols}x{grid_rows} grid) for analysis")
            logger.info(f"Chunk dimensions: {chunk_width}x{chunk_height} pixels")
            logger.info(f"Image dimensions: {width}x{height} pixels")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to split image into chunks: {str(e)}")
            raise Exception(f"Failed to split image into chunks: {str(e)}")
    
    def _create_chunk_prompt(self, page_number: int, chunk_position: Tuple[int, int, int], total_chunks: int) -> str:
        """
        Create optimized prompt for brand detection in a specific chunk.
        
        Args:
            page_number: Page number being analyzed
            chunk_position: Position of the chunk (x, y, index)
            total_chunks: Total number of chunks being analyzed
            
        Returns:
            Formatted prompt string for chunk analysis
        """
        chunk_x, chunk_y, chunk_index = chunk_position
        logger.info(f"Creating chunk analysis prompt for page {page_number}, chunk {chunk_index} at ({chunk_x}, {chunk_y})")
        
        # Determine chunk position description for better context
        if total_chunks == 6:
            # 2x3 grid layout
            row = chunk_index // 3
            col = chunk_index % 3
            position_desc = f"fila {row + 1}, columna {col + 1}"
        elif total_chunks == 4:
            # 2x2 grid layout (fallback)
            row = chunk_index // 2
            col = chunk_index % 2
            position_desc = f"fila {row + 1}, columna {col + 1}"
        else:
            position_desc = f"fragmento {chunk_index + 1}"
        
        return f"""
        Eres un experto analista especializado en detectar marcas comerciales en fragmentos de planos arquitectónicos. 
        Analiza este fragmento específico de un plano arquitectónico (página {page_number}, {position_desc}) 
        y detecta TODAS las marcas comerciales mencionadas como texto.

        CONTEXTO DEL FRAGMENTO:
        - Este es el {position_desc} de {total_chunks} fragmentos totales
        - Índice del fragmento: {chunk_index + 1}
        - Posición en el plano: coordenadas ({chunk_x}, {chunk_y})
        - Enfócate únicamente en el contenido visible en este fragmento específico

        METODOLOGÍA DE ANÁLISIS PARA FRAGMENTOS:
        
        1. **ANÁLISIS DETALLADO DEL FRAGMENTO**:
           - Examina cada elemento de texto visible en este fragmento
           - Busca marcas en cualquier orientación (horizontal, vertical, diagonal)
           - Considera texto de diferentes tamaños y estilos
           - Revisa especificaciones, notas y anotaciones en este área
        
        2. **ÁREAS ESPECÍFICAS A REVISAR EN ESTE FRAGMENTO**:
           - Títulos y subtítulos
           - Especificaciones técnicas
           - Notas y anotaciones
           - Leyendas y símbolos
           - Detalles de equipos y materiales
           - Números de modelo que incluyen marcas
           - Información de fabricantes
           - Cualquier texto que pueda contener nombres de marcas
        
        3. **TIPOS DE MARCAS A DETECTAR**:
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
        
        4. **CRITERIOS DE DETECCIÓN**:
           - Busca nombres de marcas completos y abreviados
           - Incluye variaciones de escritura (ej: "Samsung" y "SAMSUNG")
           - Detecta marcas en combinación con números de modelo
           - Considera marcas en contexto de especificaciones
           - Incluye marcas mencionadas en listas de materiales
        
        5. **EXCLUSIONES ESPECÍFICAS**:
           - Hergon y todas sus variantes (Grupo Hergon SA, Hergon SA, etc.)
           - Nombres genéricos de productos (ej: "lámpara", "interruptor")
           - Nombres de materiales genéricos (ej: "concreto", "acero")
           - Nombres de empresas que no son marcas comerciales
           - Texto que no representa marcas comerciales
        
        EJEMPLOS DE DETECCIÓN CORRECTA:
        ✅ "Samsung" 
        ✅ "LG" 
        ✅ "Bosch" 
        ✅ "Philips" 
        ✅ "Carrier" 
        ✅ "Kohler" 
        ✅ "Cemex" 
        ✅ "Aluzinc" 
        ❌ "Hergon" (excluido)
        ❌ "lámpara LED" (descripción genérica)
        ❌ "interruptor simple" (descripción genérica)
        
        INSTRUCCIONES FINALES:
        - Analiza únicamente el contenido visible en este fragmento específico
        - Si no encuentras marcas en este fragmento, responde con una lista vacía
        - Responde ÚNICAMENTE con el JSON especificado
        - Asegúrate de que el JSON sea válido y completo
        
        Formato de respuesta requerido:
        {{
            "brands_detected": [
                "Nombre exacto de la marca 1",
                "Nombre exacto de la marca 2"
            ],
            "chunk_position": [{chunk_x}, {chunk_y}],
            "chunk_index": {chunk_index},
            "page_number": {page_number}
        }}

        Responde únicamente con el JSON, sin texto adicional ni explicaciones.
        """
    
    def _create_prompt(self, page_number: int) -> str:
        """
        Create optimized prompt for brand detection.
        
        Args:
            page_number: Page number being analyzed
            
        Returns:
            Formatted prompt string
        """
        logger.info(f"Creating optimized brand detection prompt for page {page_number}")
        
        return f"""
        Eres un experto analista de planos arquitectónicos especializado en detectar marcas comerciales. Analiza esta imagen de un plano arquitectónico (página {page_number}) y detecta TODAS las marcas comerciales mencionadas como texto.

        METODOLOGÍA DE ANÁLISIS SISTEMÁTICO:
        
        1. **ESCANEO VISUAL COMPLETO**:
           - Revisa cada centímetro cuadrado de la imagen
           - Examina TODAS las áreas con texto o gráfico sin importar el tamaño
           - Busca en orientación horizontal, vertical y diagonal
           - Considera texto en diferentes tamaños de fuente
        
        2. **UBICACIONES ESPECÍFICAS A REVISAR**:
           - Títulos principales y subtítulos
           - Especificaciones técnicas y notas
           - Leyendas y símbolos con texto
           - Detalles de equipos y materiales
           - Anotaciones y comentarios
           - Tablas y listas de especificaciones
           - Referencias y notas al pie
           - Nombres de secciones y áreas
           - Especificaciones de productos
           - Marcas en dibujos y diagramas
           - Texto en esquinas y márgenes
           - Información de fabricantes
        
        3. **FORMATOS DE TEXTO A CONSIDERAR**:
           - Texto impreso y manuscrito
           - Mayúsculas, minúsculas y mixtas
           - Texto con diferentes estilos (negrita, cursiva, etc.)
           - Números de modelo que incluyen marcas
           - Abreviaciones de marcas conocidas
           - Texto en diferentes idiomas
           - Marcas con símbolos especiales
        
        4. **TIPOS DE MARCAS A DETECTAR**:
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
        
        5. **CRITERIOS DE DETECCIÓN**:
           - Busca nombres de marcas completos y abreviados
           - Incluye variaciones de escritura (ej: "Samsung" y "SAMSUNG")
           - Detecta marcas en combinación con números de modelo
           - Considera marcas en contexto de especificaciones
           - Incluye marcas mencionadas en listas de materiales
           - Detecta marcas en notas técnicas y especificaciones
        
        6. **EXCLUSIONES ESPECÍFICAS**:
           - Hergon y todas sus variantes (Grupo Hergon SA, Hergon SA, etc.)
           - Nombres genéricos de productos (ej: "lámpara", "interruptor")
           - Nombres de materiales genéricos (ej: "concreto", "acero")
           - Nombres de empresas que no son marcas comerciales
           - Texto que no representa marcas comerciales
        
        7. **PROCESO DE VALIDACIÓN**:
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
        ✅ "Aluzinc" 
        ❌ "Hergon" (excluido)
        ❌ "lámpara LED" (descripción genérica)
        ❌ "interruptor simple" (descripción genérica)
        
        INSTRUCCIONES FINALES:
        - Realiza un análisis exhaustivo y sistemático
        - No te apresures, revisa cada área con atención
        - Si no encuentras marcas, responde con una lista vacía
        - Responde ÚNICAMENTE con el JSON especificado
        - Asegúrate de que el JSON sea válido y completo
        
        Formato de respuesta requerido:
        {{
            "brands_detected": [
                "Nombre exacto de la marca 1",
                "Nombre exacto de la marca 2"
            ],
            "page_number": {page_number}
        }}

        Responde únicamente con el JSON, sin texto adicional ni explicaciones.
        """
    
    async def detect_brands_in_chunk(
        self, 
        chunk_image: Image.Image, 
        chunk_position: Tuple[int, int, int],
        page_number: int,
        total_chunks: int
    ) -> List[str]:
        """
        Detect brands in a single image chunk using Gemini 2.5.
        
        Args:
            chunk_image: PIL Image chunk
            chunk_position: Position of the chunk (x, y)
            page_number: Page number being analyzed
            total_chunks: Total number of chunks being analyzed
            
        Returns:
            List of detected brands in this chunk
        """
        async with self.semaphore:  # Rate limiting
            try:
                start_time = time.time()
                chunk_x, chunk_y, chunk_index = chunk_position
                logger.info(f"Starting chunk analysis for page {page_number}, chunk {chunk_index} at ({chunk_x}, {chunk_y})")
                
                # Encode chunk image to base64
                base64_chunk = self._encode_image_to_base64(chunk_image)
                
                # Create chunk-specific prompt
                prompt = self._create_chunk_prompt(page_number, chunk_position, total_chunks)
                
                # Create message with chunk image
                message = HumanMessage(
                    content=[
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_chunk}"
                            }
                        }
                    ]
                )
                
                # Get response from Gemini
                try:
                    response = await self.llm_instances[chunk_index % len(self.llm_instances)].ainvoke([message])
                    response_text = response.content
                    logger.info(f"Received chunk response for page {page_number}, chunk {chunk_index}: {len(response_text)} characters")
                except Exception as e:
                    logger.error(f"Error getting Gemini response for chunk {chunk_index}: {str(e)}")
                    return []
                
                # Parse response
                if not response_text or response_text.strip() == "":
                    logger.info(f"Empty response for chunk {chunk_index} - no brands detected")
                    return []
                
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    result = json.loads(json_str)
                else:
                    logger.warning(f"No JSON pattern found in chunk response {chunk_index}, trying to parse entire response")
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
                        logger.info(f"Chunk analysis completed for chunk {chunk_index}: {len(brands)} brands found in {processing_time:.2f} seconds")
                        
                        if brands:
                            logger.info(f"Brands detected in chunk {chunk_index}: {brands}")
                        
                        return brands
                
                logger.warning(f"Invalid response format for chunk {chunk_index}")
                return []
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse chunk response as JSON for chunk {chunk_index}: {str(e)}")
                return []
            except Exception as e:
                logger.error(f"Chunk analysis failed for chunk {chunk_index}: {str(e)}")
                return []
    
    async def detect_brands_in_image(
        self, 
        image, 
        page_number: int
    ) -> BrandDetectionCreate:
        """
        Detect brands in a single image using chunk-based analysis with Gemini 2.5.
        
        Args:
            image: PIL Image object
            page_number: Page number being analyzed
            
        Returns:
            BrandDetectionCreate object with detected brands
        """
        try:
            start_time = time.time()
            logger.info(f"Starting chunk-based brand detection for page {page_number}")
            logger.info(f"Image size: {image.size}, Mode: {image.mode}")
            
            # Split image into chunks
            logger.info(f"Splitting image into chunks for page {page_number}")
            chunks = self._split_image_into_chunks(image)
            
            if not chunks:
                logger.warning(f"No valid chunks created for page {page_number}, falling back to full image analysis")
                return await self._detect_brands_full_image(image, page_number)
            
            logger.info(f"Created {len(chunks)} chunks for analysis")
            
            # Create tasks for concurrent chunk analysis
            tasks = []
            for chunk_image, chunk_position in chunks:
                task = self.detect_brands_in_chunk(
                    chunk_image, 
                    chunk_position, 
                    page_number, 
                    len(chunks)
                )
                tasks.append(task)
            
            # Execute chunk analysis concurrently
            logger.info(f"Executing {len(tasks)} chunk analysis tasks concurrently")
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect all brands from all chunks
            all_brands = []
            for i, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    logger.error(f"Error in chunk {i}: {str(result)}")
                elif isinstance(result, list):
                    all_brands.extend(result)
                else:
                    logger.warning(f"Unexpected result type from chunk {i}: {type(result)}")
            
            # Remove duplicates while preserving order
            unique_brands = []
            seen_brands = set()
            for brand in all_brands:
                brand_lower = brand.lower().strip()
                if brand_lower not in seen_brands:
                    seen_brands.add(brand_lower)
                    unique_brands.append(brand)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            logger.info(f"Chunk-based brand detection completed for page {page_number}: {len(unique_brands)} unique brands found in {processing_time:.2f} seconds")
            
            if unique_brands:
                logger.info(f"Brands detected on page {page_number}: {unique_brands}")
            
            return BrandDetectionCreate(
                page_number=page_number,
                brands_detected=unique_brands
            )
            
        except Exception as e:
            logger.error(f"Chunk-based brand detection failed for page {page_number}: {str(e)}")
            logger.info(f"Falling back to full image analysis for page {page_number}")
            return await self._detect_brands_full_image(image, page_number)
    
    async def _detect_brands_full_image(
        self, 
        image, 
        page_number: int
    ) -> BrandDetectionCreate:
        """
        Fallback method: Detect brands in full image using original method.
        
        Args:
            image: PIL Image object
            page_number: Page number being analyzed
            
        Returns:
            BrandDetectionCreate object with detected brands
        """
        async with self.semaphore:  # Rate limiting
            try:
                start_time = time.time()
                logger.info(f"Starting full image brand detection for page {page_number}")
                
                # Encode image to base64
                base64_image = self._encode_image_to_base64(image)
                
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
                try:
                    response = await self.llm_instances[page_number % len(self.llm_instances)].ainvoke([message])
                    response_text = response.content
                    logger.info(f"Received full image response for page {page_number}: {len(response_text)} characters")
                except Exception as e:
                    logger.error(f"Error getting Gemini response for page {page_number}: {str(e)}")
                    raise Exception(f"Error getting AI response for page {page_number}: {str(e)}")
                
                # Handle empty responses
                if not response_text or response_text.strip() == "":
                    logger.info(f"Empty response from Gemini for page {page_number} - treating as no brands detected")
                    result = {
                        "brands_detected": [],
                        "page_number": page_number
                    }
                else:
                    # Extract JSON from response
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                    else:
                        logger.warning(f"No JSON pattern found in response for page {page_number}, trying to parse entire response")
                        result = json.loads(response_text)
                
                # Validate response structure
                if not isinstance(result, dict):
                    logger.error(f"Invalid response format for page {page_number}: expected dictionary")
                    raise Exception("Invalid response format: expected dictionary")
                
                if "brands_detected" not in result:
                    logger.error(f"Invalid response format for page {page_number}: missing 'brands_detected' field")
                    raise Exception("Invalid response format: missing 'brands_detected' field")
                
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
                logger.info(f"Full image brand detection completed for page {page_number}: {len(brands_detected)} brands found in {processing_time:.2f} seconds")
                
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
                logger.error(f"Full image brand detection failed for page {page_number}: {str(e)}")
                raise Exception(f"Brand detection failed: {str(e)}")
    
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
