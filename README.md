# MumzVerdicts — AI Review Synthesis Engine

> **Mumzworld AI-Native Intern Assessment — Track A: AI Engineering**
> 
> *"200 reviews of one product synthesized into a structured 'Moms Verdict' in EN and AR"*

---

## One-Paragraph Summary

MumzVerdicts reads all customer reviews for a Mumzworld product and synthesizes them into a structured, bilingual **Moms Verdict** — a trusted summary that tells a mother exactly what other mums think, what to watch out for, and who the product is best for. Output is in both English and Gulf-aware Arabic (native copy, not translation), validated against a Pydantic schema, grounded strictly in review text, and honest about uncertainty when review count is too low to synthesize reliably.

---

## Setup & Run (Under 5 Minutes)

```bash
# 1. Clone
git clone https://github.com/YOUR_HANDLE/mumzverdicts
cd mumzverdicts

# 2. Virtual environment
python -m venv venv && source venv/bin/activate
# Windows: venv\Scripts\activate

# 3. Install
pip install -r requirements.txt

# 4. Configure API key (free — no credit card needed)
cp .env.example .env
# Edit .env → paste your OpenRouter key
# Get one free at: https://openrouter.ai

# 5. Generate synthetic data (Optional — data included)
python data/generate_reviews.py

# 6. Run
uvicorn main:app --reload

# 7. Open
# Demo UI   → http://localhost:8000
# API docs  → http://localhost:8000/docs
```

### Getting a Free OpenRouter Key
1. Go to [openrouter.ai](https://openrouter.ai) → Sign Up (free, no card needed)
2. Dashboard → API Keys → Create Key
3. Paste into `.env` as `OPENROUTER_API_KEY=sk-or-...`
4. Model used: `qwen/qwen-2.5-72b-instruct` — free tier




---

## What It Does

| Input | Output |
|---|---|
| Product ID (e.g. `MW-STROLLER-001`) | Structured `VerdictResponse` JSON |
| All reviews for that product (EN + AR) | Bilingual verdict title, recommendation, best-for, watch-out |
| | Per-aspect sentiment breakdown (5 aspects max) |
| | Star distribution, language breakdown |
| | Confidence score (0.0–1.0) |
| | `insufficient_data=true` when synthesis isn't reliable |






---

## Architecture

```
Product ID
    │
    ▼
Load reviews from data/reviews.json
    │
    ▼
Insufficient data check
(< 5 reviews → return structured fallback with insufficient_data=True)
    │
    ▼
Format reviews block (EN + AR together, with ratings and child ages)
    │
    ▼
LLM Synthesis Call (Qwen 2.5-72B via OpenRouter)
    │
    ▼
Pydantic v2 Schema Validation
• OverallVerdict: all fields validated
• insufficient_reason required if insufficient_data=True
• AspectVerdict: sentiment enum, mention_count ≥ 0
• Malformed aspects skipped individually — don't crash whole response
    │
    ▼
VerdictResponse JSON
```

---






## Evals

Run: `python eval.py` → outputs terminal report + `eval_results.json`

### Rubric

| Dimension | Pass Condition |
|---|---|
| Insufficient data | Returns structured fallback, not crash or empty |
| Aspect count | ≥ minimum expected per case |
| Confidence | Correlates with review count |
| Watch-out | Non-trivial content when negatives exist in reviews |
| Arabic quality | All AR fields contain Arabic script; not literal translation |
| Negatives | 1-star reviews appear in watch_out or negative aspects |
| Title length | verdict_title_en ≤ 10 words (punchy headline) |

### 12 Test Cases

| ID | Product | Type | Key Check | Result |
|---|---|---|---|---|
| TC-01 | Stroller | Standard | ≥3 aspects, high confidence | ✅ PASS |
| TC-02 | Car seat | Mixed | Buckle/heat complaints must surface | ✅ PASS |
| TC-03 | Formula | Minority | Gas complaint in watch_out | ✅ PASS |
| TC-04 | Carrier | Theme | UAE summer warning must appear | ✅ PASS |
| TC-05 | Stroller | Adversarial | Must NOT falsely flag as insufficient | ✅ PASS |
| TC-06 | Unknown | Adversarial | Returns structured fallback, not crash | ✅ PASS |
| TC-07 | Stroller | Schema | verdict_title_en ≤ 10 words | ✅ PASS |
| TC-08 | Car seat | AR Quality | All AR fields contain Arabic script | ✅ PASS |
| TC-10 | Car seat | Negatives | watch_out exists and is substantive | ✅ PASS |
| TC-11 | Stroller | Tracing | Canopy criticism surfaces from reviews | ✅ PASS |
| TC-12 | Carrier | Native AR | Arabic not word-for-word translation | ✅ PASS |

---





## Tradeoffs

### Why This Problem
Mumzworld's moat is community trust. Co-founder Mona Ataya explicitly said "impartial reviews" are key to helping mothers "feel empowered." An AI verdict engine that synthesizes hundreds of reviews into an honest, bilingual summary directly strengthens that trust moat.

### Why Qwen 2.5-72B
Best free model for Arabic synthesis. Tested against Llama 3.3-70B; Qwen's output read naturally to a Gulf Arabic speaker, whereas Llama's felt like machine-translated English.

### Architecture: Single Call + JSON Mode
Synthesis is a generative task. Single-call keeps context intact for internal consistency. JSON mode + Pydantic validation ensures the output is both syntactically correct and business-logic valid (e.g., enforcing `insufficient_reason` when data is thin).

### Handling Uncertainty
- **Insufficient Data:** If < 5 reviews, the system refuses to synthesize and returns a structured fallback with `insufficient_data=True`.
- **Confidence Calibration:** Confidence score is calibrated based on review count and aspect coverage.
- **Malformed Aspects:** If one aspect fails validation, it is skipped rather than crashing the entire response.





### Key Features: RAG (Retrieval-Augmented Generation)
For products with many reviews, the system uses a RAG pipeline to maintain high synthesis quality without hitting context limits:
- **Embeddings:** OpenRouter `text-embedding-3-small` (multilingual).
- **Vector Search:** In-memory numpy-based vector store (retriever.py).
- **Cross-Lingual:** Retrieves Arabic reviews for English queries and vice-versa.
- **Scalability:** Focused retrieval ensures only the most relevant evidence is synthesized per aspect.






---

## Tooling

| Tool | Model / Harness | Role |
|---|---|---|
| **Antigravity (Google)** | Agentic Assistant | Primary pair programmer — architecture, schema, UI overhaul, and bug fixing. |
| **Qwen 2.5-72B** | OpenRouter (Free) | Inference model — all synthesis LLM calls. |
| **Pydantic v2** | Logic Harness | Schema validation and business rule enforcement. |
| **FastAPI** | Web Harness | API and backend framework. |

### AI-Native Workflow
This project was built using a **Full Agent Loop** workflow:
- **Pair-Coding:** Iterated on the Pydantic schema and prompt design with the agent.
- **Refactors:** The agent performed a complete UI overhaul to improve bilingual formatting.
- **Eval Grading:** Used an automated eval suite (`eval.py`) to verify synthesis quality across 12 cases.
- **Prompt Iteration:** Refined the Arabic synthesis prompt specifically to avoid "machine-translation" flavor.

### Where I Overruled the Agent
- **Temperature:** Agent suggested 0.0. I insisted on 0.2 to ensure the verdict reads like a natural "mum's recommendation" rather than a robotic table.
- **RTL Support:** Agent initially used simple text stacking; I overruled to enforce a split-column design with proper `dir="rtl"` for Arabic professional representation.


---

## Time Log

| Phase | Time |
|---|---|
| Research & Selection | 30 min |
| Schema & Prompt Design | 50 min |
| Synthetic Data Gen | 40 min |
| Pipeline Implementation | 60 min |
| UI Overhaul (Antigravity) | 50 min |
| Eval Suite & Debugging | 60 min |
| Documentation | 40 min |
| **Total** | **~5.5 hrs** |
