"""
Firebase service for database operations.
"""

import uuid
from datetime import datetime
from typing import List, Optional
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
        self.documents_collection = self.db.collection("documents")

    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase is already initialized
            firebase_admin.get_app()
        except ValueError:
            # Initialize Firebase with service account credentials
            if all(
                [
                    settings.firebase_private_key_id,
                    settings.firebase_private_key,
                    settings.firebase_client_email,
                    settings.firebase_client_id,
                    settings.firebase_client_x509_cert_url,
                ]
            ):
                # Use service account credentials
                cred = credentials.Certificate(
                    {
                        "type": "service_account",
                        "project_id": settings.firebase_project_id,
                        "private_key_id": settings.firebase_private_key_id,
                        "private_key": settings.firebase_private_key.replace(
                            "\\n", "\n"
                        ),
                        "client_email": settings.firebase_client_email,
                        "client_id": settings.firebase_client_id,
                        "auth_uri": settings.firebase_auth_uri,
                        "token_uri": settings.firebase_token_uri,
                        "auth_provider_x509_cert_url": settings.firebase_auth_provider_x509_cert_url,
                        "client_x509_cert_url": settings.firebase_client_x509_cert_url,
                    }
                )
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
                "results": {},
            }

            # Create document with metadata
            self.documents_collection.document(doc_id).set(doc_data)

            return Document(
                id=doc_id,
                filename=document_data.filename,
                total_pages=document_data.total_pages,
                upload_date=doc_data["upload_date"],
                status="processing",
                results=[],
            )
        except FirebaseError as e:
            raise Exception(f"Failed to create document: {str(e)}")

    async def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID with improved error handling."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.info(f"Fetching document: {document_id}")

            # Add timeout and retry logic for Firebase operations
            import time

            max_retries = 3
            retry_delay = 1

            for attempt in range(max_retries):
                try:
                    doc_ref = self.documents_collection.document(document_id)
                    doc = doc_ref.get()

                    if not doc.exists:
                        logger.info(f"Document not found: {document_id}")
                        return None

                    doc_data = doc.to_dict()

                    # Validate document data
                    if not doc_data or "id" not in doc_data:
                        logger.warning(f"Invalid document data for {document_id}")
                        return None

                    results = []

                    # Get results for each page
                    if "results" in doc_data and doc_data["results"]:
                        for page_num, result_data in doc_data["results"].items():
                            if isinstance(result_data, dict):
                                try:
                                    # Handle both successful and failed results
                                    if "error_message" in result_data:
                                        # This is a failed result, create with default values
                                        results.append(
                                            BrandDetection(
                                                page_number=int(page_num),
                                                brands_detected=[],
                                                processing_time=0.0,
                                                status=result_data.get(
                                                    "status", "failed"
                                                ),
                                                brands_review_status={},
                                            )
                                        )
                                    else:
                                        # This is a successful result
                                        # Ensure brands_review_status exists
                                        if "brands_review_status" not in result_data:
                                            result_data["brands_review_status"] = {}
                                        results.append(BrandDetection(**result_data))
                                except Exception as e:
                                    logger.warning(
                                        f"Error processing result for page {page_num} in document {document_id}: {str(e)}"
                                    )
                                    continue

                    # Create document with validated data
                    document = Document(
                        id=doc_data["id"],
                        filename=doc_data.get("filename", "Unknown"),
                        total_pages=doc_data.get("total_pages", 0),
                        upload_date=doc_data.get("upload_date", datetime.utcnow()),
                        status=doc_data.get("status", "unknown"),
                        results=results,
                    )

                    logger.info(f"Successfully fetched document: {document_id}")
                    return document

                except FirebaseError as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Firebase error fetching document {document_id} on attempt {attempt + 1}/{max_retries}: {str(e)}. Retrying in {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(
                            f"Firebase error after {max_retries} attempts for document {document_id}: {str(e)}"
                        )
                        raise Exception(
                            f"Failed to get document after {max_retries} attempts: {str(e)}"
                        )
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Unexpected error fetching document {document_id} on attempt {attempt + 1}/{max_retries}: {str(e)}. Retrying in {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(
                            f"Unexpected error after {max_retries} attempts for document {document_id}: {str(e)}"
                        )
                        raise Exception(
                            f"Failed to get document after {max_retries} attempts: {str(e)}"
                        )

        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {str(e)}")
            return None

    async def get_all_documents(self) -> List[Document]:
        """Get all documents with improved error handling and connection management."""
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.info("Fetching all documents from Firebase")

            # Add timeout and retry logic for Firebase operations
            import time

            max_retries = 3
            retry_delay = 1

            for attempt in range(max_retries):
                try:
                    docs = self.documents_collection.stream()
                    documents = []

                    for doc in docs:
                        doc_data = doc.to_dict()

                        # Validate document data
                        if not doc_data or "id" not in doc_data:
                            logger.warning(f"Skipping invalid document: {doc.id}")
                            continue

                        results = []

                        # Get results for each page
                        if "results" in doc_data and doc_data["results"]:
                            for page_num, result_data in doc_data["results"].items():
                                if isinstance(result_data, dict):
                                    try:
                                        # Handle both successful and failed results
                                        if "error_message" in result_data:
                                            # This is a failed result, create with default values
                                            results.append(
                                                BrandDetection(
                                                    page_number=int(page_num),
                                                    brands_detected=[],
                                                    processing_time=0.0,
                                                    status=result_data.get(
                                                        "status", "failed"
                                                    ),
                                                    brands_review_status={},
                                                )
                                            )
                                        else:
                                            # This is a successful result
                                            # Ensure brands_review_status exists
                                            if (
                                                "brands_review_status"
                                                not in result_data
                                            ):
                                                result_data["brands_review_status"] = {}
                                            results.append(
                                                BrandDetection(**result_data)
                                            )
                                    except Exception as e:
                                        logger.warning(
                                            f"Error processing result for page {page_num}: {str(e)}"
                                        )
                                        continue

                        # Create document with validated data
                        try:
                            document = Document(
                                id=doc_data["id"],
                                filename=doc_data.get("filename", "Unknown"),
                                total_pages=doc_data.get("total_pages", 0),
                                upload_date=doc_data.get(
                                    "upload_date", datetime.utcnow()
                                ),
                                status=doc_data.get("status", "unknown"),
                                results=results,
                            )
                            documents.append(document)
                        except Exception as e:
                            logger.warning(
                                f"Error creating document object for {doc.id}: {str(e)}"
                            )
                            continue

                    logger.info(f"Successfully fetched {len(documents)} documents")
                    return documents

                except FirebaseError as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Firebase error on attempt {attempt + 1}/{max_retries}: {str(e)}. Retrying in {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        logger.error(
                            f"Firebase error after {max_retries} attempts: {str(e)}"
                        )
                        raise
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Unexpected error on attempt {attempt + 1}/{max_retries}: {str(e)}. Retrying in {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        logger.error(
                            f"Unexpected error after {max_retries} attempts: {str(e)}"
                        )
                        raise

        except Exception as e:
            logger.error(f"Failed to get documents: {str(e)}")
            # Return empty list instead of raising exception to prevent 500 errors
            return []

    async def update_document(
        self, document_id: str, update_data: DocumentUpdate
    ) -> Optional[Document]:
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
        processing_time: float,
    ) -> BrandDetection:
        """Save brand detection result for a specific page."""
        try:
            doc_ref = self.documents_collection.document(document_id)

            # Initialize brands_review_status for each detected brand
            brands_review_status = {}
            for brand in result.brands_detected:
                brands_review_status[brand] = False  # Default to not reviewed

            # Create result data
            result_data = {
                "page_number": result.page_number,
                "brands_detected": result.brands_detected,
                "processing_time": processing_time,
                "status": "completed",
                "brands_review_status": brands_review_status,
            }

            # Update the results subcollection
            doc_ref.update({f"results.{page_number}": result_data})

            return BrandDetection(
                page_number=result.page_number,
                brands_detected=result.brands_detected,
                processing_time=processing_time,
                status="completed",
                brands_review_status=brands_review_status,
            )
        except FirebaseError as e:
            raise Exception(f"Failed to save brand detection result: {str(e)}")

    async def update_page_status(
        self,
        document_id: str,
        page_number: int,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Update the status of a specific page."""
        try:
            doc_ref = self.documents_collection.document(document_id)

            update_data = {f"results.{page_number}.status": status}

            if error_message:
                update_data[f"results.{page_number}.error_message"] = error_message

            doc_ref.update(update_data)
        except FirebaseError as e:
            raise Exception(f"Failed to update page status: {str(e)}")

    async def get_processing_status(
        self, document_id: str
    ) -> Optional[ProcessingStatus]:
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
            progress_percentage = (
                (processed_pages / doc.total_pages) * 100 if doc.total_pages > 0 else 0
            )

            # Determine overall status
            if processed_pages == doc.total_pages:
                overall_status = "completed"
            elif (
                failed_pages > 0 and (processed_pages + failed_pages) == doc.total_pages
            ):
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
                page_status=page_status,
            )
        except FirebaseError as e:
            raise Exception(f"Failed to get processing status: {str(e)}")

    async def update_brand_review_status(
        self, document_id: str, page_number: int, brand_name: str, is_reviewed: bool
    ) -> bool:
        """Update the review status of a detected brand."""
        try:
            doc_ref = self.documents_collection.document(document_id)
            doc = doc_ref.get()

            if not doc.exists:
                return False

            doc_data = doc.to_dict()

            # Check if the page exists in results
            if "results" not in doc_data or str(page_number) not in doc_data["results"]:
                return False

            page_result = doc_data["results"][str(page_number)]

            # Check if the brand exists in the detected brands
            if (
                "brands_detected" not in page_result
                or brand_name not in page_result["brands_detected"]
            ):
                return False

            # Initialize brands_review_status if it doesn't exist
            if "brands_review_status" not in page_result:
                page_result["brands_review_status"] = {}

            # Update the review status
            page_result["brands_review_status"][brand_name] = is_reviewed

            # Update the document in Firestore
            doc_ref.update({f"results.{page_number}": page_result})

            return True
        except FirebaseError as e:
            raise Exception(f"Failed to update brand review status: {str(e)}")


# Global Firebase service instance
firebase_service = FirebaseService()
