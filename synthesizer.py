"""
MumzVerdicts — RAG Synthesis Pipeline (synthesizer.py)

UPGRADED: Now uses retrieval-augmented generation instead of
full-context synthesis.

Pipeline:
  1. Load reviews for product
  2. Build vector index (embedder.py → retriever.py)
  3. For each aspect query → retrieve top-k relevant reviews
  4. Synthesize retrieved reviews per aspect → LLM call
  5. Pydantic validation → VerdictResponse

Why RAG over full-context:
  - Scales to 200+ reviews without context overflow
  - Focused evidence per aspect → less hallucination
  - Cross-lingual: AR reviews retrieved by EN aspect queries
  - Mirrors production architecture (FAISS+BM25 hybrid, cross-encoder reranking)
"""

import json
import os
import httpx
from pydantic import ValidationError

from schema import VerdictResponse, OverallVerdict, AspectVerdict, SentimentLabel
from prompts import SYNTHESIS_SYSTEM, SYNTHESIS_USER
from retriever import get_store, ReviewChunk

OPENROUTER_URL   = "https://openrouter.ai/api/v1/chat/completions"
MODEL            = "qwen/qwen-2.5-72b-instruct"
MIN_REVIEWS      = 5
TOP_K_PER_ASPECT = 6
MAX_ASPECTS      = 5

# Aspect queries drive retrieval — embedded and used to find relevant reviews
ASPECT_QUERIES = {
    "strollers": [
        "fold mechanism ease of use one hand",
        "canopy sun protection size shade",
        "wheel quality smooth ride terrain",
        "weight lightweight travel portable",
        "durability long term quality build",
    ],
    "car_seats": [
        "installation ease ISOFIX setup",
        "safety harness strap secure protection",
        "comfort recline position baby sleep",
        "heat summer temperature fabric warmth",
        "longevity multiple stages years use",
    ],
    "formula": [
        "digestion colic gas tummy stomach",
        "mixing dissolve lumps water preparation",
        "baby acceptance taste rejection fussy",
        "nutrition growth weight gain health",
        "packaging lid scoop container quality",
    ],
    "carriers": [
        "back lumbar support pain ergonomic",
        "heat warmth summer ventilation airflow",
        "learning curve instructions setup difficulty",
        "hip health dysplasia seat position",
        "fit body type shoulder narrow adjustment",
    ],
    "default": [
        "quality build durability materials",
        "value money price worth cost",
        "ease use setup assembly instructions",
        "comfort baby happy experience",
        "delivery packaging arrival condition",
    ],
}


def load_reviews(product_id: str) -> list[dict]:
    with open("data/reviews.json", encoding="utf-8") as f:
        return [r for r in json.load(f) if r["product_id"] == product_id]


def load_products() -> list[dict]:
    with open("data/products.json", encoding="utf-8") as f:
        return json.load(f)


def get_product(product_id: str) -> dict | None:
    return next((p for p in load_products() if p["product_id"] == product_id), None)


def lang_breakdown(reviews: list[dict]) -> dict:
    return {
        "en": sum(1 for r in reviews if r["language"] == "en"),
        "ar": sum(1 for r in reviews if r["language"] == "ar"),
    }


def star_distribution(reviews: list[dict]) -> dict:
    dist = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
    for r in reviews:
        dist[str(r["rating"])] = dist.get(str(r["rating"]), 0) + 1
    return dist


def format_chunks(chunks: list[ReviewChunk]) -> str:
    lines = []
    for i, c in enumerate(chunks, 1):
        flag = "🇬🇧" if c.language == "en" else "🇦🇪"
        lines.append(
            f"[{i}] {flag} Rating: {c.rating}/5 | Age: {c.child_age}\n"
            f"    \"{c.text}\""
        )
    return "\n\n".join(lines)


def format_all_reviews(reviews: list[dict]) -> str:
    lines = []
    for i, r in enumerate(reviews, 1):
        flag = "🇬🇧" if r["language"] == "en" else "🇦🇪"
        lines.append(
            f"[{i}] {flag} Rating: {r['rating']}/5 | Age: {r['child_age_at_review']}\n"
            f"    \"{r['review_text']}\""
        )
    return "\n\n".join(lines)


def call_llm(system: str, user: str, temperature: float = 0.2) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENROUTER_API_KEY not set. See .env.example")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://mumzverdicts.local",
        "X-Title": "MumzVerdicts RAG",
    }
    payload = {
        "model": MODEL,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "response_format": {"type": "json_object"},
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(OPENROUTER_URL, headers=headers, json=payload)
        resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _fallback(product: dict, reviews: list[dict], reason: str) -> VerdictResponse:
    avg = sum(r["rating"] for r in reviews) / max(1, len(reviews)) if reviews else 0.0
    return VerdictResponse(
        product_id=product["product_id"],
        product_name_en=product["name_en"],
        product_name_ar=product["name_ar"],
        category=product["category"],
        overall=OverallVerdict(
            verdict_title_en="Verdict Unavailable",
            verdict_title_ar="الحكم غير متاح",
            recommendation_en="We could not generate a reliable synthesis for this product.",
            recommendation_ar="لم نتمكن من إنشاء ملخص موثوق لهذا المنتج.",
            best_for_en="Unknown — see individual reviews.",
            best_for_ar="غير معروف — راجع التقييمات الفردية.",
            watch_out_en="Please read individual reviews directly.",
            watch_out_ar="يرجى قراءة التقييمات الفردية مباشرة.",
            avg_rating=round(avg, 1) if avg > 0 else 0.0,
            total_reviews_used=len(reviews),
            confidence=0.0,
            insufficient_data=True,
            insufficient_reason=reason,
        ),
        aspects=[],
        star_distribution=star_distribution(reviews),
        language_breakdown=lang_breakdown(reviews),
        processing_note=f"Fallback: {reason}",
    )


def synthesize(product_id: str) -> VerdictResponse:
    """
    RAG synthesis pipeline:

    1. Load reviews
    2. Build vector index via embedder.py + retriever.py
    3. Retrieve top-k reviews per aspect query (cosine similarity)
    4. LLM synthesis on retrieved evidence only
    5. Pydantic validation

    Graceful degradation: if embedding API is unavailable,
    falls back to full-context synthesis automatically.
    """
    product = get_product(product_id)
    if not product:
        return _fallback(
            {"product_id": product_id, "name_en": "Unknown",
             "name_ar": "غير معروف", "category": "unknown"},
            [], f"Product ID '{product_id}' not found in catalog",
        )

    reviews = load_reviews(product_id)

    if len(reviews) < MIN_REVIEWS:
        return _fallback(
            product, reviews,
            f"Only {len(reviews)} reviews — minimum {MIN_REVIEWS} needed",
        )

    # ── Build vector index ────────────────────────────────────────────────
    use_rag = True
    processing_note = ""
    try:
        store = get_store(product_id, reviews)
    except Exception as e:
        use_rag = False
        processing_note = f"RAG degraded to full-context (embedding unavailable: {str(e)[:60]})"

    # ── Retrieve per-aspect evidence ──────────────────────────────────────
    queries = ASPECT_QUERIES.get(product["category"], ASPECT_QUERIES["default"])

    if use_rag:
        seen_ids: set[str] = set()
        all_retrieved: list[ReviewChunk] = []

        for query in queries[:MAX_ASPECTS]:
            for chunk in store.retrieve(query, top_k=TOP_K_PER_ASPECT):
                if chunk.review_id not in seen_ids:
                    all_retrieved.append(chunk)
                    seen_ids.add(chunk.review_id)

        reviews_block   = format_chunks(all_retrieved)
        n_reviews_used  = len(all_retrieved)
        processing_note = (
            f"RAG: {len(reviews)} total → {n_reviews_used} retrieved "
            f"across {len(queries[:MAX_ASPECTS])} aspect queries "
            f"(top-{TOP_K_PER_ASPECT} each, cosine similarity, cross-lingual EN+AR)"
        )
    else:
        reviews_block  = format_all_reviews(reviews)
        n_reviews_used = len(reviews)

    # ── LLM synthesis ─────────────────────────────────────────────────────
    lb       = lang_breakdown(reviews)
    lang_str = f"{lb['en']} English, {lb['ar']} Arabic"

    user_msg = SYNTHESIS_USER.format(
        product_name_en=product["name_en"],
        product_name_ar=product["name_ar"],
        category=product["category"],
        review_count=n_reviews_used,
        lang_breakdown=lang_str,
        reviews_block=reviews_block,
        max_aspects=MAX_ASPECTS,
    )

    try:
        raw = call_llm(SYNTHESIS_SYSTEM, user_msg)
    except httpx.HTTPStatusError as e:
        return _fallback(product, reviews, f"LLM API error {e.response.status_code}")
    except Exception as e:
        return _fallback(product, reviews, f"LLM call failed: {str(e)}")

    # ── Parse & validate ──────────────────────────────────────────────────
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return _fallback(product, reviews, f"JSON parse error: {e}")

    try:
        overall = OverallVerdict(**data.get("overall", {}))
    except (ValidationError, Exception) as e:
        return _fallback(product, reviews, f"Schema validation: {str(e)[:150]}")

    aspects = []
    for a in data.get("aspects", [])[:MAX_ASPECTS]:
        try:
            aspects.append(AspectVerdict(**a))
        except Exception:
            continue

    avg = sum(r["rating"] for r in reviews) / len(reviews)
    overall.avg_rating         = round(avg, 2)
    overall.total_reviews_used = len(reviews)

    return VerdictResponse(
        product_id=product["product_id"],
        product_name_en=product["name_en"],
        product_name_ar=product["name_ar"],
        category=product["category"],
        overall=overall,
        aspects=aspects,
        star_distribution=star_distribution(reviews),
        language_breakdown=lb,
        processing_note=processing_note,
    )
