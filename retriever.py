"""
MumzVerdicts — Vector Retriever (retriever.py)

Builds an in-memory vector index over product reviews.
Retrieves the top-k most relevant reviews for any aspect query
using cosine similarity.

Architecture:
  - Vectors stored as numpy array (N, D)
  - Cosine similarity via dot product on L2-normalized vectors
  - Production swap: replace numpy search with FAISS IndexFlatIP
    (one line: index = faiss.IndexFlatIP(D); index.add(vecs))
    — interface stays identical

Why RAG instead of full-context?
  - 200 reviews × 150 tokens ≈ 30,000 tokens → context overflow
  - Irrelevant reviews add noise to synthesis, reducing quality
  - Aspect-specific retrieval gives the LLM focused, relevant evidence
  - Cross-lingual: Arabic review retrieved by English query (and vice versa)
    because both live in the same embedding space

Cross-lingual retrieval example:
  Query: "fold mechanism" (EN)
  Retrieved: "الطي سهل جداً وأنا أحمل طفلتي" (AR, rating 5) ← correctly retrieved
"""

import numpy as np
from dataclasses import dataclass
from embedder import embed_texts, embed_single


@dataclass
class ReviewChunk:
    review_id: str
    product_id: str
    text: str
    language: str
    rating: int
    child_age: str
    aspect_hint: str     # pre-tagged aspect from dataset
    vector: np.ndarray   # shape (D,)


class ReviewVectorStore:
    """
    In-memory vector store for product reviews.
    One store instance per product (built on demand, cached in memory).
    """

    def __init__(self, product_id: str):
        self.product_id = product_id
        self.chunks: list[ReviewChunk] = []
        self.matrix: np.ndarray | None = None   # shape (N, D) — L2 normalized

    def build(self, reviews: list[dict]) -> "ReviewVectorStore":
        """
        Embed all reviews and build the vector index.
        Called once per product on first verdict request.
        Subsequent requests hit the in-memory cache.
        """
        if not reviews:
            return self

        texts = [r["review_text"] for r in reviews]
        vectors = embed_texts(texts)   # (N, D) — cached on disk

        # L2-normalize for cosine similarity via dot product
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-8, norms)
        normalized = vectors / norms

        self.matrix = normalized

        for i, (review, vec) in enumerate(zip(reviews, normalized)):
            self.chunks.append(ReviewChunk(
                review_id=review["review_id"],
                product_id=review["product_id"],
                text=review["review_text"],
                language=review["language"],
                rating=review["rating"],
                child_age=review["child_age_at_review"],
                aspect_hint=review.get("review_aspect", ""),
                vector=vec,
            ))

        return self

    def retrieve(self, query: str, top_k: int = 6) -> list[ReviewChunk]:
        """
        Retrieve top-k reviews most relevant to query via cosine similarity.

        Cross-lingual: query in EN retrieves AR reviews and vice versa.
        Both live in the same embedding space.

        Returns ReviewChunks sorted by descending similarity score.
        """
        if self.matrix is None or len(self.chunks) == 0:
            return []

        # Embed query and normalize
        q_vec = embed_single(query)
        q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)

        # Cosine similarity = dot product on normalized vectors
        # Shape: (N,)
        scores = self.matrix @ q_norm

        # Top-k indices (descending)
        top_k = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]

        return [self.chunks[i] for i in top_indices]

    def retrieve_all(self) -> list[ReviewChunk]:
        """Return all chunks (used when review count is small)."""
        return self.chunks


# ── Global in-memory cache: product_id → ReviewVectorStore ───────────────────
_store_cache: dict[str, ReviewVectorStore] = {}


def get_store(product_id: str, reviews: list[dict]) -> ReviewVectorStore:
    """
    Get or build a ReviewVectorStore for the given product.
    Built once, cached in memory for the server lifetime.
    """
    if product_id not in _store_cache:
        store = ReviewVectorStore(product_id)
        store.build(reviews)
        _store_cache[product_id] = store
    return _store_cache[product_id]


def invalidate_store(product_id: str):
    """Force rebuild on next request (e.g. after new reviews added)."""
    _store_cache.pop(product_id, None)
