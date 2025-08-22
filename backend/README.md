# Document Brand Detection Backend

Backend service for the Document Brand Detection System using FastAPI, EasyOCR, and Google Gemini LLM.

## Features

- **OCR + LLM Pipeline**: Text extraction with EasyOCR followed by LLM analysis
- **Multi-language Support**: Spanish and English text recognition
- **Coordinate Preservation**: Maintains text position information
- **GPU/CPU Support**: Works on both GPU and CPU environments
- **Retry Logic**: Automatic retry for OCR failures with exponential backoff
- **Accuracy Optimization**: Configured for maximum text detection precision
- **Chunk Processing**: Processes large images in manageable chunks
- **Real-time Processing**: Asynchronous processing with live updates
- **Firebase Integration**: Data persistence and retrieval
- **Brand Review System**: Individual brand review status tracking

## Architecture

The system uses a two-stage pipeline:

1. **OCR Stage**: EasyOCR extracts text from image chunks with coordinate preservation
2. **LLM Stage**: Google Gemini analyzes the complete extracted text for brand detection

```
PDF → Images → Chunks → EasyOCR → Text → LLM → Brands
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Environment variables configured (see Configuration section)

### Using Docker (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd backend
   ```

2. **Set up environment variables:**
   Create a `.env` file with the required variables (see Configuration section)

3. **Build and run with Docker Compose:**
   ```bash
   docker compose up --build
   ```

4. **Verify the service is running:**
   ```bash
   curl http://localhost:8000/health
   ```

### Local Development

1. **Install dependencies:**
   ```bash
   pip install uv
   uv sync
   ```

2. **Set up environment variables**

3. **Run the application:**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Verify the service is running:**
   ```bash
   curl http://localhost:8000/health
   ```

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Firebase (required for data persistence)
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_X509_CERT_URL=your_cert_url

# Optional - LangChain tracing
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=your_project_name
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

# OCR Configuration
USE_GPU=false                    # Set to true if GPU is available
OCR_LANGUAGES=es,en              # Comma-separated language codes
OCR_CONFIDENCE_THRESHOLD=0.3     # Minimum confidence for text detection
OCR_MAX_RETRIES=3                # Retry attempts for OCR
OCR_RETRY_DELAY=1.0              # Initial retry delay in seconds

# Processing Configuration
MAX_CONCURRENT_PAGES=8           # Concurrent page processing
PDF_DPI=300                      # PDF resolution for processing
MAX_IMAGE_SIZE=20000             # Maximum image size in pixels
IMAGE_QUALITY=95                 # Image quality for processing
```

### Docker Configuration

The Docker setup includes:

- **Multi-stage build** for optimized container size
- **System dependencies** for EasyOCR and image processing
- **GPU support** (optional, falls back to CPU)
- **Health checks** for monitoring
- **Volume mounts** for development

## Testing

### API Testing

Once the service is running, test the API endpoints:

```bash
# Health check
curl http://localhost:8000/health

# Upload a PDF (using a tool like Postman or curl)
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@your_document.pdf"
```

### Manual Testing

You can test the OCR functionality by:

1. **Uploading a PDF** through the API
2. **Monitoring the logs** for OCR processing information
3. **Checking the results** for detected brands

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Document Management
- `POST /api/documents/upload` - Upload PDF document
- `GET /api/documents` - List all documents
- `GET /api/documents/{document_id}` - Get document details
- `DELETE /api/documents/{document_id}` - Delete document

### Brand Detection
- `GET /api/documents/{document_id}/brands` - Get detected brands
- `POST /api/documents/{document_id}/brands/review` - Update brand review status

## Troubleshooting

### Common Issues

1. **OCR Not Detecting Text**
   - Check image quality and resolution
   - Verify language settings
   - Adjust confidence thresholds

2. **Slow Processing**
   - Enable GPU acceleration if available
   - Reduce chunk size for memory-constrained environments
   - Adjust concurrent processing limits

3. **Memory Issues**
   - Reduce max image size
   - Process smaller chunks
   - Monitor GPU memory usage

4. **Docker Build Failures**
   - Ensure all system dependencies are available
   - Check architecture compatibility (ARM64 vs x86_64)
   - Verify Docker and Docker Compose versions

5. **Configuration Errors**
   - Check environment variable format
   - Ensure all required variables are set
   - Verify JSON parsing for complex values

### Debug Mode

Enable debug logging:

```bash
export DEBUG=true
```

### Logs

Check container logs:

```bash
# Backend logs
docker logs buscador-marca-backend

# Follow logs in real-time
docker logs -f buscador-marca-backend
```

## Performance Optimization

### OCR Settings

The system is configured for maximum accuracy:

- **High resolution processing** (300-600 DPI)
- **Optimized chunk size** (1024x1024 pixels)
- **Concurrent processing** (up to 8 parallel tasks)
- **Retry logic** with exponential backoff

### GPU vs CPU

- **GPU mode**: Faster processing, requires CUDA
- **CPU mode**: Slower but more compatible
- **Automatic fallback**: Falls back to CPU if GPU fails

## Development

### Project Structure

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   │   ├── ocr_service.py           # OCR functionality
│   │   ├── brand_detection_service.py # Brand detection
│   │   ├── firebase_service.py      # Data persistence
│   │   ├── pdf_service.py           # PDF processing
│   │   └── processing_service.py    # Orchestration
│   ├── config.py         # Configuration
│   └── main.py           # Application entry point
├── uploads/              # Temporary file storage
├── Dockerfile            # Container configuration
├── pyproject.toml        # Dependencies and project config
└── README.md             # This file
```

### Adding New Features

1. **Service Layer**: Add business logic in `app/services/`
2. **API Layer**: Add endpoints in `app/api/`
3. **Models**: Define data structures in `app/models/`
4. **Configuration**: Add settings in `app/config.py`
5. **Testing**: Add tests and update integration tests

## Support

For issues or questions:

1. Check the logs for detailed error information
2. Verify configuration settings
3. Monitor system resources (GPU memory, CPU usage)
4. Check the [OCR Integration Documentation](OCR_INTEGRATION.md) for detailed technical information

## License

This project is part of the Document Brand Detection System.
