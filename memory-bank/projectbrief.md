# Project Brief: Document Brand Detection System

## Project Overview
A document management system that analyzes PDF documents (specifically architectural plans) to detect and identify brand names within the document images. The system processes each page of a PDF asynchronously and provides real-time updates on brand detection progress.

## Core Requirements

### Functional Requirements
1. **PDF Upload & Processing**: Users can upload PDF documents containing architectural plans
2. **Brand Detection**: System analyzes each page (plan) to identify brand names within images
3. **Asynchronous Processing**: Each page is processed independently and asynchronously
4. **Real-time Updates**: Frontend receives real-time updates on processing status
5. **Results Display**: Shows detected brands with their corresponding page numbers
6. **Document Management**: CRUD operations for uploaded documents and their analysis results

### Technical Requirements
1. **Backend**: FastAPI with UV package manager
2. **Frontend**: React with Bun, shadcn/ui with modern-minimal theme
3. **Database**: Firebase Firestore for data persistence
4. **AI Integration**: Langchain with Google Gemini 2.5 for brand detection
5. **Containerization**: Docker Compose for local development
6. **Real-time Communication**: WebSocket or Server-Sent Events for live updates

### Data Structure
```json
{
  "brands_detected": [
    "Nombre exacto de la marca",
    ...
  ],
  "page_number": n
}
```

## Success Criteria
- Successfully detect brand names in PDF architectural plans
- Process multiple pages asynchronously
- Provide real-time feedback during processing
- Store and retrieve analysis results from Firebase
- Modern, intuitive UI/UX for document management

## Constraints
- No Redis or caching systems
- No user authentication (for now)
- No PDF storage (only analysis results)
- No bounding box detection (LLM text response only)
- Keep the system simple and focused
