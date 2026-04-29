# MumzVerdicts — EVALS.md

## Evaluation Philosophy

Standard evals measure "does it answer correctly."  
MumzVerdicts adds two harder constraints:

1. **Grounding:** Every claim must be traceable to a review. Generic praise = failure.
2. **Honest uncertainty:** System must say "I don't know" (insufficient_data=True) when review quality is too low — never invent confidence.

---

## Running the Eval Suite

```bash
python eval.py
# Outputs: terminal report + eval_results.json
```

---

## Rubric

| Dimension | Pass Condition |
|---|---|
| **Insufficient Data Handling** | Returns structured fallback, not crash or empty |
| **Aspect Count** | ≥ minimum expected per case |
| **Confidence Calibration** | Correlates with review count |
| **Watch-out Populated** | Non-trivial content when negatives exist in reviews |
| **Arabic Quality** | All AR fields contain Arabic script; not a word-for-word translation of EN |
| **Negatives Surfaced** | 1-star reviews appear in watch_out or negative aspects |
| **Title Length** | verdict_title_en ≤ 10 words (punchy, not a paragraph) |

---

## Test Cases (12 Total)

### TC-01 — Standard: Stroller, Full Review Set
- **Reviews:** 15 (10 EN, 5 AR)
- **Key test:** With 15 reviews across 6 aspects, model should produce high-confidence verdict.

### TC-02 — Mixed Sentiment: Car Seat
- **Reviews:** 13 (10 EN, 3 AR)
- **Key test:** Model must not bury 1-star reviews in overall positive framing. Buckle/heat complaints must surface.

### TC-03 — Fewer Reviews: Formula
- **Reviews:** 10 (7 EN, 3 AR)
- **Key test:** Even minority safety-relevant feedback (e.g., gas complaints) should surface in watch_out.

### TC-04 — Recurring Theme: Carrier Heat
- **Reviews:** 10 (7 EN, 3 AR)
- **Key test:** Theme identification across EN + AR reviews simultaneously ("Too hot in UAE summer").

### TC-05 — False Insufficient Check
- **Reviews:** 15
- **Key test:** Ensure the system doesn't over-trigger the "insufficient data" flag on valid datasets.

### TC-06 — Adversarial: Unknown Product ID
- **Key test:** System must degrade gracefully, returning `insufficient_data=True` and a clear reason, never a 500 error.

### TC-07 — Schema: Title Length
- **Key test:** Prompt instruction enforcement to ensure the English title is a punchy headline, not a paragraph.

### TC-08 — Arabic Quality: Script Characters
- **Key test:** Verify that Arabic fields are not empty or English masquerading as Arabic.

### TC-09 — Confidence Calibration
- **Key test:** Confidence score correlates with evidence quantity (e.g., 10 reviews should yield medium, not high, confidence).

### TC-10 — Negatives Surfaced
- **Key test:** The "buckle sticking" and "strap confusion" 1-star reviews must be substantive in the output.

### TC-11 — Specific Complaint Tracing
- **Key test:** Specific recurring complaints (e.g., "canopy size") are extractable and not averaged away.

### TC-12 — Arabic Not a Translation
- **Key test:** Verify that Arabic recommendation text differs structurally from English (Native copy, not machine translation).

---

## Scoring Summary

| Metric | Target |
|---|---|
| Overall pass rate | ≥ 85% |
| TC-06 (unknown product) | **100% — must never crash** |
| Arabic quality | 100% |
| Negatives surfaced | 90%+ |
| Confidence calibration | 90%+ |
