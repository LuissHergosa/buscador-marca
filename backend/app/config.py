"""
Configuration settings for the Document Brand Detection System.
Optimized for Windows GPU performance with parallel processing and memory efficiency.
"""

import os
import platform
from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, field_serializer


class Settings(BaseSettings):
    """Application settings optimized for Windows GPU performance."""
    
    # Application
    app_name: str = "Document Brand Detection System"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # File Upload - No limits for heavy files
    max_file_size: int = Field(default=0, env="MAX_FILE_SIZE")  # 0 = no limit
    upload_dir: str = Field(default="./uploads", env="UPLOAD_DIR")
    allowed_extensions: list[str] = Field(default=[".pdf"], env="ALLOWED_EXTENSIONS")
    
    # Google Gemini
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash-exp", env="GEMINI_MODEL")
    
    # Firebase
    firebase_project_id: str = Field(default="proyectoshergon", env="FIREBASE_PROJECT_ID")
    firebase_private_key_id: Optional[str] = Field(default=None, env="FIREBASE_PRIVATE_KEY_ID")
    firebase_private_key: Optional[str] = Field(default=None, env="FIREBASE_PRIVATE_KEY")
    firebase_client_email: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_EMAIL")
    firebase_client_id: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_ID")
    firebase_auth_uri: str = Field(default="https://accounts.google.com/o/oauth2/auth", env="FIREBASE_AUTH_URI")
    firebase_token_uri: str = Field(default="https://oauth2.googleapis.com/token", env="FIREBASE_TOKEN_URI")
    firebase_auth_provider_x509_cert_url: str = Field(
        default="https://www.googleapis.com/oauth2/v1/certs", 
        env="FIREBASE_AUTH_PROVIDER_X509_CERT_URL"
    )
    firebase_client_x509_cert_url: Optional[str] = Field(default=None, env="FIREBASE_CLIENT_X509_CERT_URL")
    
    # Processing - Windows GPU Optimized
    max_concurrent_pages: int = Field(default=4, env="MAX_CONCURRENT_PAGES")  # Reduced for Windows stability
    processing_timeout: int = Field(default=0, env="PROCESSING_TIMEOUT")  # 0 = no timeout
    batch_size: int = Field(default=4, env="BATCH_SIZE")  # Smaller batches for Windows
    max_concurrent_batches: int = Field(default=2, env="MAX_CONCURRENT_BATCHES")  # Conservative for Windows

    # Image Processing - High quality for Windows GPU
    pdf_dpi: int = Field(default=600, env="PDF_DPI")  # High resolution for better text detection
    max_image_size: int = Field(default=20000, env="MAX_IMAGE_SIZE")  # Increased for better resolution
    image_quality: int = Field(default=95, env="IMAGE_QUALITY")  # PNG quality for better text clarity
    
    # OCR Processing - Windows GPU Optimized
    use_gpu: bool = Field(default=True, env="USE_GPU")  # Use GPU if available, fallback to CPU
    ocr_languages: str = Field(default="es,en", env="OCR_LANGUAGES")  # Spanish and English as comma-separated string
    ocr_confidence_threshold: float = Field(default=0.3, env="OCR_CONFIDENCE_THRESHOLD")  # Minimum confidence for text detection
    ocr_max_retries: int = Field(default=3, env="OCR_MAX_RETRIES")  # Retry attempts for OCR
    ocr_retry_delay: float = Field(default=1.0, env="OCR_RETRY_DELAY")  # Initial retry delay in seconds
    
    # Windows-specific optimizations
    thread_pool_size: int = Field(default=4, env="THREAD_POOL_SIZE")  # Conservative for Windows
    connection_pool_size: int = Field(default=5, env="CONNECTION_POOL_SIZE")  # Reduced for Windows
    request_timeout: int = Field(default=0, env="REQUEST_TIMEOUT")  # No request timeout
    
    # GPU Memory Management
    gpu_memory_fraction: float = Field(default=0.8, env="GPU_MEMORY_FRACTION")  # Use 80% of GPU memory
    gpu_allow_growth: bool = Field(default=True, env="GPU_ALLOW_GROWTH")  # Allow GPU memory growth
    
    # LangChain
    langchain_tracing_v2: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    langchain_api_key: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    langchain_project: Optional[str] = Field(default=None, env="LANGCHAIN_PROJECT")
    langsmith_endpoint: Optional[str] = Field(default=None, env="LANGSMITH_ENDPOINT")
    
    @property
    def ocr_languages_list(self) -> List[str]:
        """Get OCR languages as a list."""
        return [lang.strip() for lang in self.ocr_languages.split(',') if lang.strip()]
    
    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return platform.system().lower() == "windows"
    
    @property
    def optimized_settings(self) -> dict:
        """Get platform-optimized settings."""
        if self.is_windows:
            return {
                "max_concurrent_pages": min(self.max_concurrent_pages, 4),
                "batch_size": min(self.batch_size, 4),
                "thread_pool_size": min(self.thread_pool_size, 4),
                "gpu_memory_fraction": 0.8,
                "use_gpu": self.use_gpu and self._check_gpu_availability(),
            }
        return {
            "max_concurrent_pages": self.max_concurrent_pages,
            "batch_size": self.batch_size,
            "thread_pool_size": self.thread_pool_size,
            "gpu_memory_fraction": self.gpu_memory_fraction,
            "use_gpu": self.use_gpu,
        }
    
    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available and accessible."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
