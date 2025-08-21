# System Patterns: Document Brand Detection System

## Architecture Overview

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │  Firebase DB    │
│                 │    │                 │    │                 │
│ - Document Upload│◄──►│ - PDF Processing│◄──►│ - Firestore     │
│ - Real-time UI   │    │ - Brand Detection│    │ - Document Store│
│ - Results Display│    │ - Async Tasks   │    │ - Results Store │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Backend Architecture (FastAPI)

### Core Components
1. **PDF Processing Service**
   - PDF to image conversion
   - Page extraction and management
   - Async task coordination

2. **Brand Detection Service**
   - Langchain integration with Gemini 2.5
   - Image analysis and brand extraction
   - Result formatting and validation

3. **Firebase Integration**
   - Document metadata storage
   - Analysis results persistence
   - Real-time data synchronization

4. **Real-time Communication**
   - WebSocket or Server-Sent Events
   - Progress updates to frontend
   - Status notifications

### API Endpoints
```
POST   /api/documents/upload          # Upload PDF for analysis
GET    /api/documents/                # List all documents
GET    /api/documents/{id}            # Get document details
GET    /api/documents/{id}/results    # Get analysis results
DELETE /api/documents/{id}            # Delete document
GET    /api/documents/{id}/progress   # Get processing progress
```

### Data Models
```python
# Document Model
class Document:
    id: str
    filename: str
    upload_date: datetime
    total_pages: int
    status: str  # "processing", "completed", "failed"
    results: List[BrandDetection]

# Brand Detection Model
class BrandDetection:
    page_number: int
    brands_detected: List[str]
    processing_time: float
    status: str  # "pending", "processing", "completed", "failed"
```

## Frontend Architecture (React)

### Component Structure
```
App/
├── DocumentUpload/
│   ├── DragDropZone
│   ├── FileValidator
│   └── UploadProgress
├── DocumentList/
│   ├── DocumentCard
│   ├── FilterBar
│   └── SearchInput
├── DocumentDetail/
│   ├── ResultsView
│   ├── BrandList
│   └── PageViewer
└── Common/
    ├── Header
    ├── LoadingSpinner
    └── ErrorBoundary
```

### State Management
- React Context for global state
- Local state for component-specific data
- Real-time updates via WebSocket/SSE

### UI/UX Patterns
- Modern minimal design theme
- Responsive grid layout
- Real-time progress indicators
- Intuitive drag-and-drop interface
- Clean, professional styling

## Database Schema (Firebase Firestore)

### Collections
```
documents/
├── {document_id}/
│   ├── metadata
│   │   ├── filename
│   │   ├── upload_date
│   │   ├── total_pages
│   │   └── status
│   └── results/
│       ├── page_1/
│       │   ├── brands_detected
│       │   ├── page_number
│       │   └── processing_time
│       └── page_n/
```

## Processing Flow

### 1. Document Upload
```
User Upload → File Validation → Firebase Metadata → Start Processing
```

### 2. PDF Processing
```
PDF → Extract Pages → Convert to Images → Queue for Analysis
```

### 3. Brand Detection
```
Image → Gemini 2.5 → Brand Extraction → Format Results → Store in Firebase
```

### 4. Real-time Updates
```
Processing Status → WebSocket/SSE → Frontend Update → UI Refresh
```

## Error Handling Patterns

### Backend Error Handling
- Graceful degradation for failed pages
- Retry mechanisms for API failures
- Comprehensive logging and monitoring
- User-friendly error messages

### Frontend Error Handling
- Error boundaries for component failures
- Network error recovery
- User feedback for failed operations
- Fallback UI states

## Security Considerations
- File upload validation and sanitization
- API rate limiting
- Input validation and sanitization
- Secure Firebase configuration

## Performance Patterns
- Asynchronous processing for scalability
- Efficient image handling and optimization
- Lazy loading for large result sets
- Caching strategies for frequently accessed data
