"""RAG (Retrieval-Augmented Generation) engine for security knowledge retrieval.

Uses ChromaDB for vector storage with a local TF-IDF embedding function.
Falls back to sentence-transformers when available.
Provides hybrid search combining vector similarity with keyword matching.
"""

import logging
import re
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Module-level state (lazy initialization)
_client = None
_collection = None


def _get_chromadb_path() -> str:
    from ..settings import settings
    return settings.chromadb_path


class TfidfEmbeddingFunction:
    """Custom hash-based embedding function for ChromaDB.

    Uses feature hashing into a fixed-dimension vector with bigrams.
    No external downloads required.
    """

    def __init__(self):
        self._dim = 512

    @staticmethod
    def name() -> str:
        return "tfidf_hash"

    @staticmethod
    def is_legacy() -> bool:
        return False

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'[a-z0-9一-鿿]+', text)
        bigrams = [tokens[i] + "_" + tokens[i + 1] for i in range(len(tokens) - 1)]
        return tokens + bigrams

    def _hash_features(self, tokens: List[str]) -> np.ndarray:
        """Hash tokens into a fixed-dimension feature vector."""
        vec = np.zeros(self._dim, dtype=np.float32)
        for token in tokens:
            idx = hash(token) % self._dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def _embed_text(self, text: str) -> np.ndarray:
        tokens = self._tokenize(text)
        return self._hash_features(tokens)

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Embed documents into vectors."""
        return [self._embed_text(text).tolist() for text in input]

    def embed_query(self, input: List[str]) -> List[np.ndarray]:
        """Embed query texts into vectors."""
        return [self._embed_text(text) for text in input]


def _create_embedding_function():
    """Create embedding function. Tries sentence-transformers first, falls back to TF-IDF."""
    from ..settings import settings
    model_name = settings.embedding_model

    # Try sentence-transformers (requires network access to download model)
    try:
        from chromadb.utils import embedding_functions
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)
        # Quick test
        ef(["test"])
        logger.info("Using sentence-transformers embedding: %s", model_name)
        return ef
    except Exception as e:
        logger.info("sentence-transformers unavailable (%s), using TF-IDF", type(e).__name__)

    # Fallback: TF-IDF (no network required)
    return TfidfEmbeddingFunction()


def _ensure_initialized():
    """Lazy-initialize ChromaDB client and collection with embedding function."""
    global _client, _collection
    if _collection is not None:
        return

    import chromadb
    path = _get_chromadb_path()
    _client = chromadb.PersistentClient(path=path)

    ef = _create_embedding_function()
    try:
        _collection = _client.get_or_create_collection(
            name="attack_knowledge",
            metadata={"hnsw:space": "cosine"},
            embedding_function=ef,
        )
    except Exception:
        # Collection exists with different embedding function config; recreate
        try:
            _client.delete_collection("attack_knowledge")
        except Exception:
            pass
        _collection = _client.get_or_create_collection(
            name="attack_knowledge",
            metadata={"hnsw:space": "cosine"},
            embedding_function=ef,
        )
    logger.info("ChromaDB collection ready at %s (count=%d)", path, _collection.count())


def add_documents(
    documents: List[str],
    metadatas: List[dict],
    ids: List[str],
) -> int:
    """Add documents to the vector store. Returns count added."""
    _ensure_initialized()

    batch_size = 100
    total = 0
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        _collection.add(
            documents=batch_docs,
            metadatas=batch_meta,
            ids=batch_ids,
        )
        total += len(batch_docs)
    logger.info("Added %d documents to RAG store", total)
    return total


def query(
    query_text: str,
    top_k: int = 5,
    where: Optional[dict] = None,
) -> List[dict]:
    """Semantic search using vector similarity.

    Returns list of dicts with keys: id, document, metadata, distance.
    """
    _ensure_initialized()
    if _collection.count() == 0:
        return []

    kwargs = {
        "query_texts": [query_text],
        "n_results": min(top_k, _collection.count()),
    }
    if where:
        kwargs["where"] = where

    results = _collection.query(**kwargs)

    items = []
    for i in range(len(results["ids"][0])):
        items.append({
            "id": results["ids"][0][i],
            "document": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return items


def hybrid_search(
    query_text: str,
    top_k: int = 5,
    keyword_weight: float = 0.3,
    where: Optional[dict] = None,
) -> List[dict]:
    """Hybrid search combining vector similarity with keyword matching.

    keyword_weight: 0.0 = pure vector, 1.0 = pure keyword.
    """
    vector_results = query(query_text, top_k=top_k * 3, where=where)
    if not vector_results:
        return []

    query_tokens = set(re.findall(r'[a-z0-9]+', query_text.lower()))

    reranked = []
    for item in vector_results:
        vector_score = max(0.0, 1.0 - item["distance"])

        doc_tokens = set(re.findall(r'[a-z0-9]+', item["document"].lower()))
        if query_tokens:
            keyword_score = len(query_tokens & doc_tokens) / len(query_tokens)
        else:
            keyword_score = 0.0

        final_score = (1 - keyword_weight) * vector_score + keyword_weight * keyword_score
        reranked.append({
            **item,
            "relevance": round(final_score, 4),
            "vector_score": round(vector_score, 4),
            "keyword_score": round(keyword_score, 4),
        })

    reranked.sort(key=lambda x: -x["relevance"])
    return reranked[:top_k]


def get_collection_stats() -> dict:
    """Return collection statistics."""
    try:
        _ensure_initialized()
        return {
            "total_documents": _collection.count(),
            "collection_name": _collection.name,
        }
    except Exception as e:
        return {"total_documents": 0, "error": str(e)}


def reset():
    """Reset the RAG engine state (for testing)."""
    global _client, _collection
    _client = None
    _collection = None
