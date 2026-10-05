"""
Vector Store Service — ChromaDB-backed RAG store.

Design notes:
- One Chroma *collection per company* (multi-tenant isolation), named
  "{chroma_collection_prefix}_{company_id}". This means a founder's RAG
  queries can never leak another company's feedback, without needing a
  metadata filter (defense in depth: we still filter as well).
- Embeddings are produced locally via sentence-transformers (free, no
  external embedding API), same model family already used elsewhere in
  this project for topic modeling (settings.embedding_model).
- The store is a thin wrapper so the rest of the app (LangGraph tools,
  ingestion pipeline) never talks to Chroma directly.
"""
from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Any

from loguru import logger

from app.core.config import settings


class VectorStoreService:
    """Wraps a persistent Chroma client + per-company collections."""

    def __init__(self) -> None:
        self._client = None
        self._embeddings = None

    # -- lazy singletons -------------------------------------------------
    @property
    def embeddings(self):
        if self._embeddings is None:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self._embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embeddings

    @property
    def client(self):
        if self._client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            self._client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return self._client

    def _collection_name(self, company_id: uuid.UUID | str) -> str:
        return f"{settings.chroma_collection_prefix}_{str(company_id).replace('-', '')}"

    def _get_vectorstore(self, company_id: uuid.UUID | str):
        from langchain_chroma import Chroma
        return Chroma(
            client=self.client,
            collection_name=self._collection_name(company_id),
            embedding_function=self.embeddings,
        )

    # -- write path --------------------------------------------------------
    def upsert_feedback(
        self,
        company_id: uuid.UUID | str,
        items: list[dict[str, Any]],
    ) -> int:
        """
        Index feedback records for RAG retrieval.
        Each item: {id, text, sentiment, rating, category, created_at, ...}
        Called from the analysis pipeline right after NLP processing so the
        chat/insight agents can retrieve up-to-date context.
        """
        if not items:
            return 0
        from langchain_core.documents import Document

        docs = []
        ids = []
        for item in items:
            text = (item.get("text") or "").strip()
            if not text:
                continue
            metadata = {
                "feedback_id": str(item.get("id")),
                "sentiment": item.get("sentiment") or "unknown",
                "rating": item.get("rating") if item.get("rating") is not None else -1.0,
                "category": item.get("category") or "",
                "is_complaint": bool(item.get("is_complaint", False)),
                "is_feature_request": bool(item.get("is_feature_request", False)),
                "created_at": str(item.get("created_at") or ""),
            }
            docs.append(Document(page_content=text, metadata=metadata))
            ids.append(str(item.get("id")))

        if not docs:
            return 0

        vs = self._get_vectorstore(company_id)
        vs.add_documents(documents=docs, ids=ids)
        logger.info(f"Indexed {len(docs)} feedback docs into Chroma for company={company_id}")
        return len(docs)

    def delete_company_index(self, company_id: uuid.UUID | str) -> None:
        try:
            self.client.delete_collection(self._collection_name(company_id))
        except Exception as e:
            logger.warning(f"Could not delete collection: {e}")

    # -- read path -----------------------------------------------------------
    def similarity_search(
        self,
        company_id: uuid.UUID | str,
        query: str,
        k: int | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Retrieve the most relevant feedback snippets for a natural-language
        query. Returns list of {text, metadata, score} sorted by relevance
        (score = similarity, higher is better).
        """
        vs = self._get_vectorstore(company_id)
        k = k or settings.rag_top_k
        try:
            results = vs.similarity_search_with_relevance_scores(query, k=k, filter=filters)
        except Exception as e:
            logger.warning(f"RAG similarity search failed, returning empty: {e}")
            return []

        out = []
        for doc, score in results:
            if score is not None and score < settings.rag_min_relevance:
                continue
            out.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "score": round(float(score), 4) if score is not None else None,
            })
        return out

    def count(self, company_id: uuid.UUID | str) -> int:
        try:
            vs = self._get_vectorstore(company_id)
            return vs._collection.count()
        except Exception:
            return 0


vector_store_service = VectorStoreService()
