"""
Firebase service for database operations.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from ..config import settings
from ..models.document import Document, DocumentCreate, DocumentUpdate
from ..models.brand_detection import BrandDetection, BrandDetectionCreate
from ..models.processing_status import ProcessingStatus


class FirebaseService:
    """Service for Firebase Firestore operations."""
    
    def __init__(self):
        """Initialize Firebase service."""
        self._initialize_firebase()
        self.db = firestore.client()
        self.documents_collection = self.db.collection('documents')
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
        except ValueError:
            # Initialize Firebase with service account credentials
            if all([
                settings.firebase_private_key_id,
                settings.firebase_private_key,
                settings.firebase_client_email,
                settings.firebase_client_id,
                settings.firebase_client_x509_cert_url
            ]):
                # Use service account credentials
                cred = credentials.Certificate({
                    "type": "service_account",
                    "project_id": settings.firebase_project_id,
                    "private_key_id": settings.firebase_private_key_id,
                    "private_key": settings.firebase_private_key.replace('\\n', '\n'),
                    "client_email": settings.firebase_client_email,
                    "client_id": settings.firebase_client_id,
                    "auth_uri": settings.firebase_auth_uri,
                    "token_uri": settings.firebase_token_uri,
                    "auth_provider_x509_cert_url": settings.firebase_auth_provider_x509_cert_url,
                    "client_x509_cert_url": settings.firebase_client_x509_cert_url
                })
                firebase_admin.initialize_app(cred)
            else:
                # Use default credentials (for local development)
                firebase_admin.initialize_app()
    
    async def create_document(self, document_data: DocumentCreate) -> Document:
        """Create a new document in Firestore."""
        try:
            doc_id = str(uuid.uuid4())
            doc_data = {
                "id": doc_id,
                "filename": document_data.filename,
                "total_pages": document_data.total_pages,
                "upload_date": datetime.utcnow(),
                "status": "processing",
                "results": {}
            }
            
            # Create document with metadata
            self.documents_collection.document(doc_id).set(doc_data)
            
            return Document(
                id=doc_id,
                filename=document_data.filename,
                total_pages=document_data.total_pages,
                upload_date=doc_data["upload_date"],
                status="processing",
                results=[]
            )
        except FirebaseError as e:
            raise Exception(f"Failed to create document: {str(e)}")
    
    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        try:
            doc_ref = self.documents_collection.document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            doc_data = doc.to_dict()
            results = []
            
            # Get results for each page
            if "results" in doc_data:
                for page_num, result_data in doc_data["results"].items():
                    if isinstance(result_data, dict):
                        results.append(BrandDetection(**result_data))
            
            return Document(
                id=doc_data["id"],
                filename=doc_data["filename"],
                total_pages=doc_data["total_pages"],
                upload_date=doc_data["upload_date"],
                status=doc_data["status"],
                results=results
            )
        except FirebaseError as e:
            raise Exception(f"Failed to get document: {str(e)}")
    
    async def get_all_documents(self) -> List[Document]:
        """Get all documents."""
        try:
            docs = self.documents_collection.stream()
            documents = []
            
            for doc in docs:
                doc_data = doc.to_dict()
                results = []
                
                # Get results for each page
                if "results" in doc_data:
                    for page_num, result_data in doc_data["results"].items():
                        if isinstance(result_data, dict):
                            results.append(BrandDetection(**result_data))
                
                documents.append(Document(
                    id=doc_data["id"],
                    filename=doc_data["filename"],
                    total_pages=doc_data["total_pages"],
                    upload_date=doc_data["upload_date"],
                    status=doc_data["status"],
                    results=results
                ))
            
            return documents
        except FirebaseError as e:
            raise Exception(f"Failed to get documents: {str(e)}")
    
    async def update_document(self, document_id: str, update_data: DocumentUpdate) -> Optional[Document]:
        """Update a document."""
        try:
            doc_ref = self.documents_collection.document(document_id)
            
            # Prepare update data
            update_dict = {}
            if update_data.filename is not None:
                update_dict["filename"] = update_data.filename
            if update_data.status is not None:
                update_dict["status"] = update_data.status
            
            if update_dict:
                doc_ref.update(update_dict)
            
            return await self.get_document(document_id)
        except FirebaseError as e:
            raise Exception(f"Failed to update document: {str(e)}")
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        try:
            doc_ref = self.documents_collection.document(document_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.delete()
            return True
        except FirebaseError as e:
            raise Exception(f"Failed to delete document: {str(e)}")
    
    async def save_brand_detection_result(
        self, 
        document_id: str, 
        page_number: int, 
        result: BrandDetectionCreate,
        processing_time: float
    ) -> BrandDetection:
        """Save brand detection result for a specific page."""
        try:
            doc_ref = self.documents_collection.document(document_id)
            
            # Create result data
            result_data = {
                "page_number": result.page_number,
                "brands_detected": result.brands_detected,
                "processing_time": processing_time,
                "status": "completed"
            }
            
            # Update the results subcollection
            doc_ref.update({
                f"results.{page_number}": result_data
            })
            
            return BrandDetection(
                page_number=result.page_number,
                brands_detected=result.brands_detected,
                processing_time=processing_time,
                status="completed"
            )
        except FirebaseError as e:
            raise Exception(f"Failed to save brand detection result: {str(e)}")
    
    async def update_page_status(
        self, 
        document_id: str, 
        page_number: int, 
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """Update the status of a specific page."""
        try:
            doc_ref = self.documents_collection.document(document_id)
            
            update_data = {
                f"results.{page_number}.status": status
            }
            
            if error_message:
                update_data[f"results.{page_number}.error_message"] = error_message
            
            doc_ref.update(update_data)
        except FirebaseError as e:
            raise Exception(f"Failed to update page status: {str(e)}")
    
    async def get_processing_status(self, document_id: str) -> Optional[ProcessingStatus]:
        """Get the processing status of a document."""
        try:
            doc = await self.get_document(document_id)
            if not doc:
                return None
            
            # Count processed and failed pages
            processed_pages = 0
            failed_pages = 0
            page_status = {}
            
            if doc.results:
                for result in doc.results:
                    page_status[result.page_number] = result.status
                    if result.status == "completed":
                        processed_pages += 1
                    elif result.status == "failed":
                        failed_pages += 1
            
            # Calculate progress percentage
            progress_percentage = (processed_pages / doc.total_pages) * 100 if doc.total_pages > 0 else 0
            
            # Determine overall status
            if processed_pages == doc.total_pages:
                overall_status = "completed"
            elif failed_pages > 0 and (processed_pages + failed_pages) == doc.total_pages:
                overall_status = "failed"
            else:
                overall_status = "processing"
            
            return ProcessingStatus(
                document_id=document_id,
                status=overall_status,
                total_pages=doc.total_pages,
                processed_pages=processed_pages,
                failed_pages=failed_pages,
                progress_percentage=progress_percentage,
                page_status=page_status
            )
        except FirebaseError as e:
            raise Exception(f"Failed to get processing status: {str(e)}")


# Global Firebase service instance
firebase_service = FirebaseService()
