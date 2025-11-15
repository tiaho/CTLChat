"""File upload and processing handler for CTLChat RAG application."""
from pathlib import Path
from typing import Dict, Optional
import tempfile
import shutil
from fastapi import UploadFile, HTTPException
from loguru import logger
from config import settings
from utils import clean_text, chunk_text, get_file_extension
from document_loader import DocumentLoader
from vector_store import VectorStore


class FileUploadHandler:
    """Handle file uploads and processing for the RAG system."""

    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.md'}

    def __init__(self, vector_store: VectorStore):
        """Initialize the file upload handler.

        Args:
            vector_store: VectorStore instance to add documents to
        """
        self.vector_store = vector_store
        self.doc_loader = DocumentLoader()

    def validate_file(self, filename: str) -> None:
        """Validate that the uploaded file type is supported.

        Args:
            filename: Name of the uploaded file

        Raises:
            HTTPException: If file type is not supported
        """
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.SUPPORTED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Supported types: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            )

    def process_uploaded_file(
        self,
        file: UploadFile,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        visibility: str = "personal"
    ) -> Dict[str, any]:
        """Process an uploaded file and add it to the vector store.

        This method:
        1. Validates the file type
        2. Saves the file temporarily
        3. Extracts and cleans text content
        4. Chunks the text
        5. Creates embeddings and stores in vector database

        Args:
            file: Uploaded file object
            user_id: User ID for metadata (optional)
            org_id: Organization ID for metadata (optional)
            visibility: Visibility setting ("personal" or "org-wide")

        Returns:
            Dictionary with processing results:
                - filename: Name of the processed file
                - chunks_added: Number of chunks created
                - total_documents: Total documents in vector store

        Raises:
            HTTPException: If file processing fails
        """
        # Validate file type
        self.validate_file(file.filename)

        logger.info(f"Processing uploaded file: {file.filename}")

        # Create temporary file
        file_ext = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            # Copy uploaded file to temp location
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)

        try:
            # Extract text content
            content = self.doc_loader.load_file(temp_path)

            # Clean the text
            content = clean_text(content)

            # Chunk the document
            chunks = chunk_text(
                content,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap
            )

            # Create document entries with metadata
            documents = self._create_document_entries(
                chunks=chunks,
                filename=file.filename,
                file_ext=get_file_extension(temp_path),
                user_id=user_id,
                org_id=org_id,
                visibility=visibility
            )

            # Add documents to vector store (creates embeddings automatically)
            self.vector_store.add_documents(documents)

            # Get updated count
            total_docs = self.vector_store.get_collection_count()

            logger.info(f"Successfully processed {file.filename}: {len(chunks)} chunks added")

            return {
                "filename": file.filename,
                "chunks_added": len(chunks),
                "total_documents": total_docs
            }

        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")
        finally:
            # Clean up temporary file
            if temp_path.exists():
                temp_path.unlink()

    def _create_document_entries(
        self,
        chunks: list[str],
        filename: str,
        file_ext: str,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        visibility: str = "personal"
    ) -> list[Dict[str, any]]:
        """Create document entries with metadata for each chunk.

        Args:
            chunks: List of text chunks
            filename: Original filename
            file_ext: File extension
            user_id: User ID for metadata
            org_id: Organization ID for metadata
            visibility: Visibility setting

        Returns:
            List of document dictionaries with content and metadata
        """
        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                'content': chunk,
                'metadata': {
                    'source': filename,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'file_type': file_ext,
                    'user_id': user_id or 'anonymous',
                    'org_id': org_id or 'default',
                    'visibility': visibility
                }
            })
        return documents


# Convenience function for use in API
def process_file_upload(
    vector_store: VectorStore,
    file: UploadFile,
    user_id: Optional[str] = None,
    org_id: Optional[str] = None,
    visibility: str = "personal"
) -> Dict[str, any]:
    """Process a file upload and add to vector store.

    Args:
        vector_store: VectorStore instance
        file: Uploaded file
        user_id: User ID (optional)
        org_id: Organization ID (optional)
        visibility: Visibility setting

    Returns:
        Dictionary with processing results
    """
    handler = FileUploadHandler(vector_store)
    return handler.process_uploaded_file(file, user_id, org_id, visibility)
