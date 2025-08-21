# Technical Context: Document Brand Detection System

## Technology Stack

### Backend (FastAPI)
- **Framework**: FastAPI 0.104+
- **Package Manager**: UV
- **Python Version**: 3.11+
- **Key Dependencies**:
  - `fastapi`: Web framework
  - `uvicorn`: ASGI server
  - `langchain`: AI/LLM integration
  - `langchain-google-genai`: Google Gemini integration
  - `firebase-admin`: Firebase SDK for Python
  - `python-multipart`: File upload handling
  - `Pillow`: Image processing
  - `PyPDF2` or `pdf2image`: PDF processing
  - `websockets`: Real-time communication
  - `pydantic`: Data validation

### Frontend (React)
- **Framework**: React 18+
- **Package Manager**: Bun
- **Build Tool**: Vite
- **UI Library**: shadcn/ui with modern-minimal theme
- **Key Dependencies**:
  - `react`: Core framework
  - `react-dom`: DOM rendering
  - `@radix-ui/react-*`: UI primitives
  - `lucide-react`: Icons
  - `tailwindcss`: Styling
  - `axios`: HTTP client
  - `react-dropzone`: File upload
  - `react-query`: Data fetching
  - `zustand`: State management

### Database
- **Platform**: Firebase
- **Service**: Firestore
- **Project ID**: `proyectoshergon`
- **Authentication**: None (for now)

### AI/ML
- **Provider**: Google AI
- **Model**: Gemini 2.5
- **Integration**: Langchain
- **API**: Google Generative AI

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Development**: Local development environment
- **Deployment**: TBD (local for now)

## Development Environment Setup

### Prerequisites
- Docker & Docker Compose
- Bun (for frontend)
- UV (for backend)
- Firebase CLI (optional)
- Google AI API key

### Environment Variables
```bash
# Backend (.env)
GEMINI_API_KEY=your_gemini_api_key
FIREBASE_PROJECT_ID=proyectoshergon
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=your_cert_url

# Frontend (.env)
VITE_API_URL=http://localhost:8000
VITE_FIREBASE_PROJECT_ID=proyectoshergon
```

## Project Structure
```
buscador-marca/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── models/
│   │   ├── services/
│   │   ├── api/
│   │   └── utils/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── App.tsx
│   ├── package.json
│   ├── Dockerfile
│   └── tailwind.config.js
├── docker-compose.yml
└── README.md
```

## API Specifications

### Base URL
- Development: `http://localhost:8000`
- Production: TBD

### Authentication
- None required for initial version
- API key or JWT tokens for future versions

### Rate Limiting
- Basic rate limiting for file uploads
- Per-endpoint limits to be defined

### File Upload Limits
- Maximum file size: 50MB
- Supported formats: PDF only
- Maximum pages: 100 pages per document

## Firebase Configuration

### Firestore Collections
```javascript
// Documents collection
documents: {
  [documentId]: {
    metadata: {
      filename: string,
      upload_date: timestamp,
      total_pages: number,
      status: "processing" | "completed" | "failed"
    },
    results: {
      [pageNumber]: {
        brands_detected: string[],
        page_number: number,
        processing_time: number,
        status: "pending" | "processing" | "completed" | "failed"
      }
    }
  }
}
```

### Security Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /documents/{documentId} {
      allow read, write: if true; // Open for now, will be restricted later
    }
  }
}
```

## Performance Considerations

### Backend Performance
- Async processing for PDF analysis
- Image optimization before AI processing
- Efficient Firebase queries
- Connection pooling for database

### Frontend Performance
- Lazy loading for large result sets
- Virtual scrolling for long lists
- Image optimization and caching
- Efficient state management

### Scalability
- Horizontal scaling with Docker
- Load balancing for multiple instances
- Database indexing strategies
- Caching layers (future)

## Security Considerations

### Current (Basic)
- Input validation and sanitization
- File type validation
- Basic rate limiting
- Secure Firebase configuration

### Future Enhancements
- User authentication and authorization
- API key management
- File encryption
- Audit logging
- CORS configuration

## Monitoring and Logging

### Backend Logging
- Structured logging with Python logging
- Error tracking and monitoring
- Performance metrics
- API usage analytics

### Frontend Monitoring
- Error boundary logging
- Performance monitoring
- User interaction analytics
- Network request tracking

## Testing Strategy

### Backend Testing
- Unit tests with pytest
- Integration tests for API endpoints
- Mock testing for external services
- Performance testing

### Frontend Testing
- Component testing with React Testing Library
- E2E testing with Playwright
- Visual regression testing
- Performance testing

## Deployment Strategy

### Development
- Docker Compose for local development
- Hot reloading for both frontend and backend
- Local Firebase emulator (optional)

### Production (Future)
- Container orchestration (Kubernetes/Docker Swarm)
- CI/CD pipeline
- Environment-specific configurations
- Monitoring and alerting
