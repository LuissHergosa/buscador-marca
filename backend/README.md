# Document Brand Detection System - Backend

FastAPI backend for analyzing PDF documents to detect brand names using Google Gemini 2.5.

## Features

- PDF document upload and processing
- Asynchronous brand detection using AI
- Real-time processing status updates
- Firebase Firestore integration
- RESTful API with automatic documentation

## Technology Stack

- **Framework**: FastAPI
- **Package Manager**: UV
- **AI/ML**: Langchain + Google Gemini 2.5
- **Database**: Firebase Firestore
- **Image Processing**: Pillow, pdf2image
- **PDF Processing**: PyPDF2

## Prerequisites

- Python 3.11+
- UV package manager
- Google AI API key
- Firebase project credentials

## Installation

1. **Clone the repository**
   ```bash
   cd backend
   ```

2. **Install UV (if not already installed)**
   ```bash
   pip install uv
   ```

3. **Install dependencies**
   ```bash
   uv sync
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Google Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# Firebase
FIREBASE_PROJECT_ID=proyectoshergon
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_X509_CERT_URL=your_cert_url

# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000
MAX_FILE_SIZE=52428800
```

### Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (`proyectoshergon`)
3. Go to Project Settings > Service Accounts
4. Generate a new private key
5. Use the credentials in your `.env` file

## Running the Application

### Development

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t buscador-marca-backend .
docker run -p 8000:8000 --env-file .env buscador-marca-backend
```

## API Documentation

Once the application is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Documents

- `POST /api/documents/upload` - Upload PDF for analysis
- `GET /api/documents/` - Get all documents
- `GET /api/documents/{id}` - Get specific document
- `DELETE /api/documents/{id}` - Delete document
- `GET /api/documents/{id}/status` - Get processing status
- `GET /api/documents/{id}/results` - Get analysis results
- `POST /api/documents/{id}/cancel` - Cancel processing

### Health

- `GET /health/` - Health check
- `GET /health/ready` - Readiness check

## Development

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic services
│   └── api/                 # API routes
├── pyproject.toml           # Project configuration
├── Dockerfile              # Docker configuration
└── README.md               # This file
```

### Adding New Features

1. **Models**: Add Pydantic models in `app/models/`
2. **Services**: Add business logic in `app/services/`
3. **API Routes**: Add endpoints in `app/api/`
4. **Tests**: Add tests in `tests/` directory

### Code Quality

```bash
# Format code
uv run black app/

# Sort imports
uv run isort app/

# Type checking
uv run mypy app/

# Linting
uv run flake8 app/
```

## Testing

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=app
```

## Deployment

### Docker Compose

The backend is designed to work with Docker Compose. See the root `docker-compose.yml` file.

### Environment Variables

Make sure all required environment variables are set in your deployment environment.

## Troubleshooting

### Common Issues

1. **Firebase Connection**: Ensure Firebase credentials are correct
2. **Gemini API**: Verify API key and model name
3. **File Upload**: Check file size limits and allowed extensions
4. **Memory Issues**: Adjust `MAX_CONCURRENT_PAGES` for large documents

### Logs

Check application logs for detailed error information:

```bash
uv run uvicorn app.main:app --log-level debug
```

## Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Use conventional commit messages

## License

This project is part of the Document Brand Detection System.
