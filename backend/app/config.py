"""
Configuration settings for the Document Brand Detection System.
Optimized for performance with parallel processing and memory efficiency.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings optimized for performance."""
    
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
    
    # Processing - Optimized for performance
    max_concurrent_pages: int = Field(default=8, env="MAX_CONCURRENT_PAGES")  # Increased for better parallelization
    processing_timeout: int = Field(default=0, env="PROCESSING_TIMEOUT")  # 0 = no timeout
    batch_size: int = Field(default=8, env="BATCH_SIZE")  # Process pages in batches
    max_concurrent_batches: int = Field(default=3, env="MAX_CONCURRENT_BATCHES")  # Limit concurrent batches

    # Image Processing - Optimized for performance while maintaining quality
    pdf_dpi: int = Field(default=600, env="PDF_DPI")  # High resolution for better text detection
    max_image_size: int = Field(default=20000, env="MAX_IMAGE_SIZE")  # Increased for better resolution
    image_quality: int = Field(default=95, env="IMAGE_QUALITY")  # PNG quality for better text clarity
    
    # Performance optimizations
    thread_pool_size: int = Field(default=8, env="THREAD_POOL_SIZE")  # Thread pool size for CPU-intensive tasks
    connection_pool_size: int = Field(default=10, env="CONNECTION_POOL_SIZE")  # Connection pool size
    request_timeout: int = Field(default=0, env="REQUEST_TIMEOUT")  # No request timeout
    
    # LangChain
    langchain_tracing_v2: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    langchain_api_key: Optional[str] = Field(default=None, env="LANGSMITH_API_KEY")
    langchain_project: Optional[str] = Field(default=None, env="LANGCHAIN_PROJECT")
    langsmith_endpoint: Optional[str] = Field(default=None, env="LANGSMITH_ENDPOINT")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
