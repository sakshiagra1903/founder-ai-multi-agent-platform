from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.document import Document, DocumentChunk

class DocumentRepository:
    def create(self, db: Session, user_id: str, filename: str, file_path: str, file_size: int) -> Document:
        db_doc = Document(
            user_id=user_id,
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            status="processing"
        )
        db.add(db_doc)
        db.commit()
        db.refresh(db_doc)
        return db_doc

    def update_status(self, db: Session, document_id: str, status: str) -> Optional[Document]:
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            db_doc.status = status
            db.commit()
            db.refresh(db_doc)
        return db_doc

    def add_chunks(self, db: Session, document_id: str, chunks_data: List[dict]) -> List[DocumentChunk]:
        db_chunks = []
        for chunk in chunks_data:
            db_chunk = DocumentChunk(
                document_id=document_id,
                chunk_id=chunk["chunk_id"],
                page_number=chunk["page_number"],
                content=chunk["content"]
            )
            db.add(db_chunk)
            db_chunks.append(db_chunk)
        db.commit()
        return db_chunks

    def get_by_id(self, db: Session, document_id: str) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id).first()

    def get_by_id_and_user(self, db: Session, document_id: str, user_id: str) -> Optional[Document]:
        return db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()

    def list_by_user(self, db: Session, user_id: str) -> List[Document]:
        return db.query(Document).filter(Document.user_id == user_id).order_by(Document.created_at.desc()).all()

    def delete(self, db: Session, document_id: str) -> bool:
        db_doc = db.query(Document).filter(Document.id == document_id).first()
        if db_doc:
            db.delete(db_doc)
            db.commit()
            return True
        return False

document_repo = DocumentRepository()
