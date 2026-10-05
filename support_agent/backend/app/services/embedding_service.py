import logging
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        try:
            # Standard sentence-transformers/all-MiniLM-L6-v2 model
            # This runs entirely locally and exposes the embed_documents/embed_query methods compatible with FAISS
            self.model = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            logger.info("SentenceTransformers (all-MiniLM-L6-v2) embedding model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise

    def get_embeddings_model(self) -> HuggingFaceEmbeddings:
        return self.model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        try:
            return self.model.embed_documents(texts)
        except Exception as e:
            logger.error(f"Error generating embeddings for batch documents: {str(e)}")
            raise ValueError(f"Embedding generation failed: {str(e)}")

    def embed_query(self, text: str) -> List[float]:
        try:
            return self.model.embed_query(text)
        except Exception as e:
            logger.error(f"Error generating embedding for query: {str(e)}")
            raise ValueError(f"Query embedding generation failed: {str(e)}")

embedding_service = EmbeddingService()
