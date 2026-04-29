"""
MumzVerdicts — Pydantic Schema
All LLM output validated here. Failures are explicit, never silent.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from enum import Enum


class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    MIXED    = "mixed"
    NEGATIVE = "negative"


class AspectVerdict(BaseModel):
    aspect: str                         # e.g. "fold mechanism"
    sentiment: SentimentLabel
    summary_en: str = Field(description="1–2 sentence English summary for this aspect")
    summary_ar: str = Field(description="1–2 sentence Arabic summary (native, not translated)")
    supporting_quote: Optional[str]     # direct short quote from reviews, <15 words
    mention_count: int = Field(ge=0)


class OverallVerdict(BaseModel):
    verdict_title_en: str   = Field(description="Punchy 5–8 word verdict headline in EN")
    verdict_title_ar: str   = Field(description="Punchy headline in Arabic (native)")
    recommendation_en: str  = Field(description="2–3 sentence overall recommendation EN")
    recommendation_ar: str  = Field(description="2–3 sentence overall recommendation AR (native)")
    best_for_en: str        = Field(description="Who this product is best for, EN")
    best_for_ar: str        = Field(description="Who this product is best for, AR")
    watch_out_en: str       = Field(description="Main caveat or concern, EN")
    watch_out_ar: str       = Field(description="Main caveat or concern, AR")
    avg_rating: float       = Field(ge=0.0, le=5.0)
    total_reviews_used: int = Field(ge=0)
    confidence: float       = Field(ge=0.0, le=1.0,
                                    description="Model confidence in this synthesis")
    insufficient_data: bool = Field(
        default=False,
        description="True when review count or quality is too low to synthesize reliably"
    )
    insufficient_reason: Optional[str] = Field(
        default=None,
        description="Why synthesis was not possible — set when insufficient_data=True"
    )

    @model_validator(mode="after")
    def insufficient_reason_required(self):
        if self.insufficient_data and not self.insufficient_reason:
            raise ValueError("insufficient_reason must be set when insufficient_data=True")
        return self


class VerdictResponse(BaseModel):
    product_id: str
    product_name_en: str
    product_name_ar: str
    category: str
    overall: OverallVerdict
    aspects: list[AspectVerdict] = Field(min_length=0)
    star_distribution: dict[str, int]   # {"5": 12, "4": 3, ...}
    language_breakdown: dict[str, int]  # {"en": 20, "ar": 8}
    processing_note: Optional[str] = None
