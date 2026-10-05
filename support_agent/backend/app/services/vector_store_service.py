import os
import logging
from typing import List, Dict, Tuple
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document as LC_Document
from app.core.config import settings
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        self.embeddings = embedding_service.get_embeddings_model()
        self.index_path = settings.FAISS_INDEX_DIR
        self.db = None
        self.load_index()

    def load_index(self) -> None:
        """Loads FAISS index from disk. Creates an empty one if not found."""
        if os.path.exists(os.path.join(self.index_path, "index.faiss")):
            try:
                self.db = FAISS.load_local(
                    folder_path=self.index_path,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info("FAISS index loaded successfully from disk.")
            except Exception as e:
                logger.error(f"Error loading FAISS index: {str(e)}")
                self.create_index()
        else:
            logger.info("FAISS index not found on disk. Initializing a new one.")
            self.create_index()

    def create_index(self) -> None:
        """Initializes a new empty FAISS index with a dummy document."""
        try:
            # FAISS requires at least one document to initialize
            dummy_text = "Founder AI Assistant RAG Initialization Document."
            dummy_meta = {"document_id": "system", "page_number": 0, "filename": "system.txt"}
            self.db = FAISS.from_texts(
                texts=[dummy_text],
                embedding=self.embeddings,
                metadatas=[dummy_meta],
                ids=["system_init"]
            )
            self.save_index()
            logger.info("New FAISS index created and saved.")
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {str(e)}")
            raise

    def save_index(self) -> None:
        """Saves current FAISS index state to disk."""
        if self.db:
            try:
                self.db.save_local(self.index_path)
                logger.info("FAISS index saved successfully.")
            except Exception as e:
                logger.error(f"Error saving FAISS index to disk: {str(e)}")
                raise

    def add_documents(self, chunks: List[Dict[str, any]], filename: str) -> None:
        """
        Adds text chunks to the FAISS vector index.
        """
        if not chunks:
            return

        texts = [c["content"] for c in chunks]
        metadatas = [{
            "document_id": c["document_id"],
            "page_number": c["page_number"],
            "filename": filename
        } for c in chunks]
        ids = [c["chunk_id"] for c in chunks]

        try:
            if self.db is None:
                self.load_index()
            
            self.db.add_texts(texts=texts, metadatas=metadatas, ids=ids)
            self.save_index()
            logger.info(f"Added {len(chunks)} chunks for {filename} to FAISS index.")
        except Exception as e:
            logger.error(f"Error adding documents to FAISS: {str(e)}")
            raise ValueError(f"Failed to insert vectors into FAISS: {str(e)}")

    def delete_documents(self, chunk_ids: List[str]) -> None:
        """
        Removes vectors from the FAISS index by their unique chunk IDs.
        """
        if not chunk_ids or not self.db:
            return
        try:
            self.db.delete(chunk_ids)
            self.save_index()
            logger.info(f"Deleted {len(chunk_ids)} chunk vectors from FAISS index.")
        except Exception as e:
            logger.error(f"Error deleting vectors from FAISS: {str(e)}")
            raise ValueError(f"Failed to delete vectors from FAISS: {str(e)}")

    def search(self, query: str, top_k: int = 5) -> List[Tuple[LC_Document, float]]:
        """
        Performs similarity search on FAISS vector store.
        Returns:
            List of Tuples (Document, score)
        """
        if not self.db:
            self.load_index()
        try:
            # similarity_search_with_score returns lower distance scores for closer matches
            results = self.db.similarity_search_with_score(query, k=top_k)
            return results
        except Exception as e:
            logger.error(f"Error executing vector search: {str(e)}")
            return []

vector_store_service = VectorStoreService()
