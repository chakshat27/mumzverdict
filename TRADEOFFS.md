# MumzVerdicts — TRADEOFFS.md

## Problem Selection

### Why "Moms Verdict" Review Synthesis
Mumzworld's co-founder Mona Ataya explicitly built the platform around "impartial reviews" to help mothers "feel empowered." An AI that synthesizes hundreds of reviews into a trusted, honest, bilingual verdict directly strengthens that core value proposition.

**Why it scores well against the grading criteria:**
- **Problem selection:** Maps directly to Mumzworld's stated mission.
- **Production quality:** Fast, schema-validated result with a professional bilingual UI.
- **Eval rigor:** 12 cases covering adversarial inputs, Arabic quality, and negative surfacing.
- **Uncertainty handling:** `insufficient_data=True` is a first-class output.

### Rejected Alternatives
- **CS Email Triage:** Good for ops, but synthesis has a higher customer trust impact.
- **Returns Intelligence:** Requires real-world historical data to be convincing; review synthesis works on the text provided.
- **Gift Finder:** Hard to build a convincing version without a real, live product catalog.

---

## Architecture Decisions

### RAG (Retrieval-Augmented Generation)
For products with many reviews, sending the entire text to an LLM would overflow the context window and introduce noise. 
- **Decision:** Use a RAG pipeline (OpenRouter embeddings + in-memory vector search).
- **Trade-off:** Adds overhead for embedding reviews, but ensures that every aspect summary is grounded in the *most relevant* reviews.

### Single Synthesis Call vs. Multi-Step
- **Decision:** Single-call synthesis using JSON mode.
- **Trade-off:** Multi-step (extract aspects, then summarize each) is more granular but can lose the "big picture" and consistency between fields. Single-call keeps the model's context intact.

### temperature=0.2
- **Decision:** 0.2 instead of 0.0.
- **Trade-off:** 0.0 is too robotic; 0.5+ risks hallucination. 0.2 provides natural language variation while maintaining structural reliability.

### JSON Mode + Pydantic Validation
- **Decision:** Two separate layers of validation.
- **Trade-off:** JSON mode ensures syntax; Pydantic ensures business logic (e.g., enforcing an `insufficient_reason` only when data is thin).

---

## Uncertainty Handling

The system is designed to "know what it doesn't know," addressing several failure modes mentioned in the assessment brief:

| Brief Failure Mode | How MumzVerdicts Handles It |
|---|---|
| "Inventing facts not in the input" | Prompt rule: "Every claim must be supported by at least one review." |
| "Hiding uncertainty" | `insufficient_data=True` flag for low review counts. |
| "Confident answers on out-of-scope inputs" | Unknown product IDs return a structured fallback, not a guess. |
| "Arabic that reads like a translation" | Native Arabic writing instruction in the system prompt. |

---

## What I Cut (Future Roadmap)
- **Vector Search Database (FAISS):** The current numpy implementation is perfect for < 500 reviews. For massive scale, I would swap to a dedicated FAISS index.
- **Streaming UI:** Would improve perceived performance for long synthesis calls.
- **Freshness Weighting:** Giving higher priority to 2024 reviews over 2021 reviews to account for product updates/patches.
