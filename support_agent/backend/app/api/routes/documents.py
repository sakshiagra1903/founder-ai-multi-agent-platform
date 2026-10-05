import os
import uuid
import shutil
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.document_repo import document_repo
from app.schemas.document import DocumentOut, DocumentUploadResponse
from app.core.config import settings
from app.services.pdf_service import pdf_service
from app.services.chunking_service import chunking_service
from app.services.vector_store_service import vector_store_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Uploads and processes a PDF document:
    1. Validates PDF type and file size.
    2. Saves file locally in uploads/.
    3. Extracts text using PyMuPDF.
    4. Splits text into overlapping chunks.
    5. Saves chunks to database and generates/registers vector embeddings in FAISS.
    """
    # Validate PDF extension
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF documents are supported."
        )

    # Validate file size via content-length or spool file size
    # Read file contents to check size
    file_bytes = await file.read()
    file_size = len(file_bytes)
    
    if file_size > settings.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024*1024)}MB."
        )
    
    # Reset file cursor after reading
    await file.seek(0)
    
    # Generate a temporary unique ID just for the filename on disk
    temp_id = str(uuid.uuid4())
    unique_filename = f"{temp_id}_{file.filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    
    # Save PDF locally
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Failed to write file to disk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file locally."
        )
        
    # Store initial metadata in PostgreSQL
    db_doc = document_repo.create(
        db,
        user_id=current_user.id,
        filename=file.filename,
        file_path=file_path,
        file_size=file_size
    )

    # IMPORTANT FIX: document_repo.create() assigns its own DB id, which is NOT
    # the same as temp_id generated above. All downstream chunk/vector records
    # must reference the REAL id that now exists in the "documents" table,
    # otherwise inserting chunks fails with a ForeignKeyViolation.
    doc_id = str(db_doc.id)
    
    # Process document
    try:
        # Extract text
        pages_data = pdf_service.extract_text(file_path)
        
        # Chunk text
        chunks = chunking_service.create_chunks(pages_data, document_id=doc_id)
        
        # Save chunks to PostgreSQL
        document_repo.add_chunks(db, document_id=doc_id, chunks_data=chunks)
        
        # Generate embeddings and add to FAISS
        vector_store_service.add_documents(chunks, filename=file.filename)
        
        # Update document status to processed
        document_repo.update_status(db, document_id=doc_id, status="processed")
        db_doc.status = "processed"
        logger.info(f"Successfully processed and indexed document {file.filename} (ID: {doc_id})")
        
    except Exception as e:
        logger.error(f"Failed to process document {file.filename}: {str(e)}")
        # A failed insert/flush leaves the SQLAlchemy session in a broken state;
        # roll it back before issuing any further queries (e.g. update_status),
        # otherwise you get a PendingRollbackError on the next statement.
        db.rollback()
        document_repo.update_status(db, document_id=doc_id, status="failed")
        db_doc.status = "failed"
        # If processing failed, we still keep the document in the DB but marked as failed.
        # We don't raise an exception here so that the response returns the failed status properly.
        
    return {
        "document_id": db_doc.id,
        "filename": db_doc.filename,
        "status": db_doc.status
    }

@router.get("", response_model=List[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lists all documents uploaded by the current user.
    """
    return document_repo.list_by_user(db, user_id=current_user.id)

@router.delete("/{document_id}", status_code=status.HTTP_200_OK)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a document:
    1. Verifies ownership.
    2. Deletes vectors from FAISS.
    3. Removes local file.
    4. Deletes Postgres database entry (cascades chunk cleanup).
    """
    doc = document_repo.get_by_id_and_user(db, document_id=document_id, user_id=current_user.id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or access denied."
        )

    # 1. Collect chunk IDs to delete from FAISS
    chunk_ids = [chunk.id for chunk in doc.chunks] if doc.chunks else []
    if not chunk_ids:
        # If chunks aren't loaded or weren't stored (e.g. failed state), query them
        # Note: chunk IDs are generated as {doc_id}_p{page}_c{idx}
        # However, document_repo holds database chunks with their DB ids
        # Let's inspect: our chunk_id field in DocumentChunk contains the custom UUID we generated (e.g. doc_id_p1_c0)
        # So yes, chunk.chunk_id is what we sent to FAISS!
        chunk_ids = [chunk.chunk_id for chunk in doc.chunks]

    # Delete vectors from FAISS index
    if chunk_ids:
        try:
            vector_store_service.delete_documents(chunk_ids)
        except Exception as e:
            logger.error(f"Error removing vectors from FAISS for document {document_id}: {str(e)}")

    # 2. Remove local file from disk
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception as e:
            logger.error(f"Failed to delete local file {doc.file_path}: {str(e)}")

    # 3. Delete document record (cascade deletes chunks in DB)
    success = document_repo.delete(db, document_id=document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from database."
        )

    return {"detail": "Document successfully deleted."}