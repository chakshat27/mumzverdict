"""
MumzVerdicts — FastAPI Application
"""
import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from synthesizer import synthesize, load_products

load_dotenv()

app = FastAPI(
    title="MumzVerdicts",
    description=(
        "Synthesizes customer reviews into structured bilingual 'Moms Verdict' summaries. "
        "Mumzworld AI Intern Assessment — Track A."
    ),
    version="1.0.0",
    docs_url="/docs",
)
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home(request: Request):
    products = load_products()
    return templates.TemplateResponse("index.html", {"request": request, "products": products})


@app.post("/verdict/{product_id}", summary="Generate Moms Verdict for a product")
async def get_verdict(product_id: str):
    """
    Synthesizes all reviews for the given product_id into a structured
    bilingual Moms Verdict (EN + AR).

    Returns insufficient_data=true when review count is below threshold
    or synthesis quality cannot be guaranteed — never silent failure.
    """
    result = synthesize(product_id)
    return result.model_dump()


@app.get("/products", summary="List all available products")
async def list_products():
    return load_products()


@app.get("/reviews/{product_id}", summary="Get raw reviews for a product")
async def get_reviews(product_id: str):
    from synthesizer import load_reviews
    reviews = load_reviews(product_id)
    if not reviews:
        raise HTTPException(status_code=404, detail=f"No reviews found for {product_id}")
    return {"product_id": product_id, "count": len(reviews), "reviews": reviews}


@app.get("/health")
async def health():
    import os
    return {
        "status": "ok",
        "model": "qwen/qwen-2.5-72b-instruct",
        "api_key_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "version": "1.0.0",
    }
