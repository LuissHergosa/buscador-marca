# Document Brand Detection System

A modern web application for analyzing PDF documents to detect brand names using AI. Built with FastAPI, React, and Google Gemini 2.5.

## 🚀 Features

- **PDF Upload & Processing**: Drag-and-drop interface for uploading PDF documents
- **AI-Powered Brand Detection**: Uses Google Gemini 2.5 to detect brands in document images
- **Real-time Processing**: Live progress updates during document analysis
- **Modern UI/UX**: Beautiful interface built with shadcn/ui and modern-minimal theme
- **Document Management**: View, filter, and manage uploaded documents
- **Export Results**: Download analysis results as JSON
- **Responsive Design**: Works on desktop and mobile devices

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │  Firebase DB    │
│                 │    │                 │    │                 │
│ - Document Upload│◄──►│ - PDF Processing│◄──►│ - Firestore     │
│ - Real-time UI   │    │ - Brand Detection│    │ - Document Store│
│ - Results Display│    │ - Async Tasks   │    │ - Results Store │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI with UV package manager
- **AI/ML**: Langchain + Google Gemini 2.5
- **Database**: Firebase Firestore
- **Image Processing**: Pillow, pdf2image
- **PDF Processing**: PyPDF2

### Frontend
- **Framework**: React 19 with TypeScript
- **Package Manager**: Bun
- **UI Library**: shadcn/ui with modern-minimal theme
- **Styling**: Tailwind CSS
- **State Management**: Zustand + React Query
- **File Upload**: React Dropzone

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (production)

## 📋 Prerequisites

- Docker & Docker Compose
- Google AI API key (Gemini 2.5)
- Firebase project credentials
- Node.js 18+ (for local development)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd buscador-marca
```

### 2. Configure Environment Variables
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env with your credentials
GEMINI_API_KEY=your_gemini_api_key_here
FIREBASE_PROJECT_ID=proyectoshergon
FIREBASE_PRIVATE_KEY_ID=your_private_key_id
FIREBASE_PRIVATE_KEY=your_private_key
FIREBASE_CLIENT_EMAIL=your_client_email
FIREBASE_CLIENT_ID=your_client_id
FIREBASE_CLIENT_X509_CERT_URL=your_cert_url
```

### 3. Run with Docker Compose
```bash
docker-compose up --build
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🔧 Development Setup

### Backend Development
```bash
cd backend

# Install UV (if not already installed)
pip install uv

# Install dependencies
uv sync

# Run development server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install Bun (if not already installed)
curl -fsSL https://bun.sh/install | bash

# Install dependencies
bun install

# Run development server
bun run dev
```

## 📖 API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation.

### Key Endpoints
- `POST /api/documents/upload` - Upload PDF for analysis
- `GET /api/documents/` - List all documents
- `GET /api/documents/{id}` - Get document details
- `GET /api/documents/{id}/status` - Get processing status
- `GET /api/documents/{id}/results` - Get analysis results
- `DELETE /api/documents/{id}` - Delete document

## 🎨 UI/UX Features

### Modern Design
- Clean, minimalist interface using shadcn/ui
- Modern-minimal theme for professional appearance
- Responsive design for all screen sizes
- Smooth animations and transitions

### User Experience
- Intuitive drag-and-drop file upload
- Real-time progress indicators
- Comprehensive document management
- Advanced filtering and search
- Export functionality for results

## 🔒 Security

- File type validation (PDF only)
- File size limits (50MB max)
- Input sanitization and validation
- Secure Firebase configuration
- CORS protection

## 📊 Performance

- Asynchronous PDF processing
- Concurrent page analysis
- Image optimization for AI processing
- Efficient state management
- Real-time updates with React Query

## 🧪 Testing

### Backend Testing
```bash
cd backend
uv run pytest
```

### Frontend Testing
```bash
cd frontend
bun test
```

## 📦 Deployment

### Production Build
```bash
# Build and run production containers
docker-compose -f docker-compose.yml up --build -d
```

### Environment Configuration
Make sure to set all required environment variables in production:
- `GEMINI_API_KEY`
- Firebase credentials
- `DEBUG=false`
- Production database settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the API documentation at `/docs`
- Review the logs: `docker-compose logs`
- Open an issue on GitHub

## 🔄 Updates

The system automatically:
- Refreshes document status every 5 seconds
- Updates processing progress every 2 seconds
- Maintains real-time connection with the backend

---

**Built with ❤️ using FastAPI, React, and Google Gemini 2.5**
