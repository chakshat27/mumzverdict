"""
MumzVerdicts — Embedding Engine (embedder.py)

Generates dense vector embeddings for reviews using OpenRouter's
free embedding endpoint (text-embedding-3-small via OpenAI-compatible API).

Architecture note:
  In production this would use sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
  loaded locally via HuggingFace. For this prototype we use OpenRouter's embedding
  endpoint with the same API key already required for synthesis — zero extra setup.

  Swapping to local sentence-transformers requires one line change:
    embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    vectors  = embedder.encode(texts)

  The retriever.py interface stays identical regardless.

Supports English and Arabic — both are embedded in the same vector space,
enabling cross-lingual retrieval (AR review retrieved by EN query and vice versa).
"""

import os
import json
import hashlib
import numpy as np
import httpx
from pathlib import Path

OPENROUTER_EMBED_URL = "https://openrouter.ai/api/v1/embeddings"
EMBED_MODEL          = "openai/text-embedding-3-small"   # free on OpenRouter
EMBED_DIM            = 1536
CACHE_PATH           = Path("data/embed_cache.json")     # persist embeddings — avoid re-calling API


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_cache(cache: dict):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)


def _text_hash(text: str) -> str:
    """Deterministic key for cache lookup."""
    return hashlib.md5(text.strip().lower().encode()).hexdigest()


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Embed a list of texts → numpy array of shape (N, EMBED_DIM).

    Uses a disk cache so reviews are only embedded once.
    Cache survives server restarts — important for free-tier rate limits.

    Cross-lingual: Arabic and English texts embedded in same vector space.
    An Arabic review CAN be retrieved by an English aspect query.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY not set")

    cache = _load_cache()
    vectors   = []
    to_embed  = []   # texts not in cache
    to_embed_idx = []

    # ── Check cache first ──────────────────────────────────────────────────
    result_map = {}
    for i, text in enumerate(texts):
        key = _text_hash(text)
        if key in cache:
            result_map[i] = np.array(cache[key], dtype=np.float32)
        else:
            to_embed.append(text)
            to_embed_idx.append(i)

    # ── Embed uncached texts in one batch call ─────────────────────────────
    if to_embed:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://mumzverdicts.local",
            "X-Title": "MumzVerdicts RAG Layer"
        }
        payload = {"model": EMBED_MODEL, "input": to_embed}

        with httpx.Client(timeout=45.0) as client:
            resp = client.post(OPENROUTER_EMBED_URL, headers=headers, json=payload)
            resp.raise_for_status()

        data = resp.json()
        new_vectors = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]

        # Store in cache
        for text, vec in zip(to_embed, new_vectors):
            cache[_text_hash(text)] = vec

        _save_cache(cache)

        for idx, vec in zip(to_embed_idx, new_vectors):
            result_map[idx] = np.array(vec, dtype=np.float32)

    # ── Assemble in original order ─────────────────────────────────────────
    all_vecs = np.stack([result_map[i] for i in range(len(texts))], axis=0)
    return all_vecs


def embed_single(text: str) -> np.ndarray:
    """Convenience wrapper for single text."""
    return embed_texts([text])[0]
