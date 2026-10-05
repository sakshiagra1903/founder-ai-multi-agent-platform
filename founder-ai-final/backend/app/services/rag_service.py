"""
Retrieval-Augmented Generation (RAG) layer.

Two vector indices are used:

1. Rubric index (persistent, built once):
   Embeds the curated hiring rubric documents (app/knowledge_base/hiring_rubrics.py)
   so evaluation agents can retrieve the specific rubric passages relevant to
   whatever they're scoring instead of relying only on the LLM's own judgment.

2. Resume index (ephemeral, built per-analysis):
   Chunks the candidate's resume text and embeds it so each specialist agent
   retrieves only the passages relevant to *its* dimension (skills, education,
   red flags, etc.) instead of stuffing the whole resume into every prompt.
   This keeps prompts focused and scales to long, multi-page resumes.

Embeddings run locally via Sentence-Transformers (same embedding family used by
the Feedback and Support agents in this platform, for a consistent RAG stack
across all three agents) so RAG works even before the user configures an LLM key.
"""
import logging
import os
from typing import List, Optional

from chromadb.config import Settings as ChromaSettings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

_CHROMA_CLIENT_SETTINGS = ChromaSettings(anonymized_telemetry=False)

from app.core.config import settings
from app.knowledge_base.hiring_rubrics import RUBRIC_DOCS

logger = logging.getLogger(__name__)

_embeddings = None
_rubric_store: Optional[Chroma] = None

# Collection name intentionally changed from "hiring_rubrics" — the previous
# collection's vectors were embedded with a different model (BAAI/bge-small
# via fastembed) and are NOT compatible with Sentence-Transformers vectors.
# Reusing the old name would silently mix two incompatible embedding spaces
# and degrade retrieval quality without ever raising an error. A fresh
# collection name makes the existing auto-seed logic below (`existing <
# len(RUBRIC_DOCS)`) re-embed cleanly on first use instead.
_RUBRIC_COLLECTION_NAME = "hiring_rubrics_st"


def get_embeddings() -> HuggingFaceEmbeddings:
    """Lazily create a single shared local embedding model (downloaded once, cached on disk)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_rubric_store() -> Chroma:
    """
    Return the persistent rubric vector store, building/populating it on first use.
    Safe to call repeatedly — will not re-embed if the collection already has data.
    """
    global _rubric_store
    if _rubric_store is not None:
        return _rubric_store

    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    store = Chroma(
        collection_name=_RUBRIC_COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=settings.CHROMA_PERSIST_DIR,
        client_settings=_CHROMA_CLIENT_SETTINGS,
    )

    try:
        existing = store._collection.count()
    except Exception:
        existing = 0

    if existing < len(RUBRIC_DOCS):
        logger.info("Seeding rubric RAG index (%d documents)...", len(RUBRIC_DOCS))
        docs = [
            Document(page_content=d["text"], metadata={"category": d["category"], "id": d["id"]})
            for d in RUBRIC_DOCS
        ]
        ids = [d["id"] for d in RUBRIC_DOCS]
        store.add_documents(docs, ids=ids)

    _rubric_store = store
    return _rubric_store


def retrieve_rubric(query: str, category: Optional[str] = None, k: int = 2) -> str:
    """Retrieve the top-k rubric passages relevant to `query`, optionally filtered by category."""
    try:
        store = get_rubric_store()
        kwargs = {"k": k}
        if category:
            kwargs["filter"] = {"category": category}
        results = store.similarity_search(query, **kwargs)
        return "\n---\n".join(r.page_content for r in results)
    except Exception as e:
        logger.warning("Rubric retrieval failed, continuing without RAG grounding: %s", e)
        return ""


def chunk_resume(resume_text: str) -> List[Document]:
    """Split a (potentially multi-page) resume into overlapping chunks for retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_text(resume_text)
    return [Document(page_content=c, metadata={"chunk": i}) for i, c in enumerate(chunks)]


def build_resume_index(resume_text: str) -> Optional[Chroma]:
    """
    Build a throwaway (in-memory, not persisted) vector index for a single resume.
    Returns None if the resume is short enough that chunk-level retrieval adds no value
    (caller should just use the full text directly in that case).
    """
    if len(resume_text) < 1500:
        return None
    try:
        docs = chunk_resume(resume_text)
        return Chroma.from_documents(docs, embedding=get_embeddings(), client_settings=_CHROMA_CLIENT_SETTINGS)
    except Exception as e:
        logger.warning("Resume RAG indexing failed, falling back to full text: %s", e)
        return None


def retrieve_resume_context(
    resume_text: str,
    query: str,
    index: Optional[Chroma],
    k: int = 4,
    fallback_chars: int = 4000,
) -> str:
    """
    Retrieve the resume passages most relevant to `query`. Falls back to a plain
    truncated slice of the resume when no index was built (short resume) or retrieval fails.
    """
    if index is None:
        return resume_text[:fallback_chars]
    try:
        results = index.similarity_search(query, k=k)
        return "\n---\n".join(r.page_content for r in results)
    except Exception as e:
        logger.warning("Resume retrieval failed, falling back to truncated text: %s", e)
        return resume_text[:fallback_chars]
