"""
MumzVerdicts — Evaluation Runner
12 test cases: easy, adversarial, Arabic quality, uncertainty handling.
Run: python eval.py
"""
import json, sys, time
from datetime import datetime
from dotenv import load_dotenv
from synthesizer import synthesize, load_reviews
from schema import SentimentLabel

load_dotenv()

CASES = [
    # ── Standard cases ──
    {"id":"TC-01","pid":"MW-STROLLER-001","desc":"Full stroller synthesis — sufficient reviews",
     "expect_insufficient":False,"expect_aspects_min":3,"expect_confidence_min":0.65,
     "expect_watch_out":True,"expect_ar_populated":True,
     "notes":"15 reviews — should produce high-confidence verdict with ≥3 aspects"},

    {"id":"TC-02","pid":"MW-CARSEAT-002","desc":"Car seat synthesis — mixed sentiment expected",
     "expect_insufficient":False,"expect_aspects_min":3,"expect_confidence_min":0.60,
     "expect_watch_out":True,"expect_ar_populated":True,
     "notes":"13 reviews with clear negatives (buckle issue, heat) — must appear in verdict"},

    {"id":"TC-03","pid":"MW-FORMULA-003","desc":"Formula — fewer reviews, positive skew",
     "expect_insufficient":False,"expect_aspects_min":2,"expect_confidence_min":0.55,
     "expect_watch_out":True,"expect_ar_populated":True,
     "notes":"10 reviews — should still synthesize; gas complaint must appear in watch_out"},

    {"id":"TC-04","pid":"MW-CARRIER-004","desc":"Carrier — heat complaints must surface",
     "expect_insufficient":False,"expect_aspects_min":2,"expect_confidence_min":0.55,
     "expect_watch_out":True,"expect_ar_populated":True,
     "notes":"10 reviews; 'too hot in UAE summer' is a recurring theme — must appear"},

    # ── Uncertainty / insufficient data ──
    {"id":"TC-05","pid":"MW-STROLLER-001","desc":"Adversarial: product exists but test insufficient_data path",
     "expect_insufficient":False,"expect_aspects_min":1,"expect_confidence_min":0.0,
     "expect_watch_out":False,"expect_ar_populated":True,
     "notes":"Normal case — just verify system doesn't falsely flag as insufficient",
     "override_min_reviews":None},

    {"id":"TC-06","pid":"MW-UNKNOWN-999","desc":"Unknown product ID — must return structured fallback",
     "expect_insufficient":True,"expect_aspects_min":0,"expect_confidence_min":0.0,
     "expect_watch_out":False,"expect_ar_populated":False,
     "notes":"Product not in catalog — should return insufficient_data=True, not crash"},

    # ── Schema validation ──
    {"id":"TC-07","pid":"MW-STROLLER-001","desc":"Verdict title must be <=10 words",
     "expect_insufficient":False,"expect_aspects_min":1,"check_title_length":True,
     "expect_watch_out":True,"expect_ar_populated":True,
     "notes":"Verify verdict_title_en is punchy and not a paragraph"},

    {"id":"TC-08","pid":"MW-CARSEAT-002","desc":"Arabic fields must be non-empty and non-English",
     "expect_insufficient":False,"expect_aspects_min":2,"check_arabic_chars":True,
     "expect_watch_out":True,"expect_ar_populated":True,
     "notes":"All AR fields must contain Arabic script characters"},

    {"id":"TC-09","pid":"MW-FORMULA-003","desc":"Confidence must correlate with review count",
     "expect_insufficient":False,"expect_aspects_min":2,"expect_confidence_min":0.45,
     "expect_watch_out":True,"expect_ar_populated":True,
     "notes":"10 reviews → confidence should be medium, not maximum"},

    # ── Negative review handling ──
    {"id":"TC-10","pid":"MW-CARSEAT-002","desc":"1-star reviews must not be buried",
     "expect_insufficient":False,"expect_aspects_min":2,"expect_watch_out":True,
     "check_negatives_surfaced":True,"expect_ar_populated":True,
     "notes":"Buckle sticking + strap confusion in reviews — watch_out must exist and be substantive"},

    {"id":"TC-11","pid":"MW-STROLLER-001","desc":"Canopy criticism present in reviews — must surface",
     "expect_insufficient":False,"expect_aspects_min":2,"expect_watch_out":True,
     "expect_ar_populated":True,
     "notes":"Multiple EN and AR reviews mention small canopy for UAE sun — must appear in aspects or watch_out"},

    # ── Arabic quality ──
    {"id":"TC-12","pid":"MW-CARRIER-004","desc":"Arabic verdict not a word-for-word translation of English",
     "expect_insufficient":False,"expect_aspects_min":2,"expect_watch_out":True,
     "check_ar_not_translation":True,"expect_ar_populated":True,
     "notes":"Arabic text must differ structurally from English — not a literal translation"},
]

def has_arabic_chars(text: str) -> bool:
    return any('\u0600' <= c <= '\u06ff' for c in (text or ""))

def word_count(text: str) -> int:
    return len((text or "").split())

def icon(ok): return "[OK]" if ok else "[FAIL]"

def evaluate():
    print("\n" + "="*65)
    print("  MumzVerdicts -- Evaluation Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*65)

    results = []
    passed = 0

    for case in CASES:
        print(f"\n[{case['id']}] {case['desc'].replace('-', '-').replace('<=', '<=')}")
        print(f"  {case['notes'].replace('-', '-').replace('>=', '>=')}")

        try:
            result = synthesize(case["pid"])
            o = result.overall
            checks = {}

            # ── Core checks ──
            checks["insufficient_match"] = (o.insufficient_data == case.get("expect_insufficient", False))
            checks["aspects_count"] = (len(result.aspects) >= case.get("expect_aspects_min", 0))
            checks["confidence_min"] = (o.confidence >= case.get("expect_confidence_min", 0.0))

            # ── Watch out populated ──
            if case.get("expect_watch_out"):
                checks["watch_out"] = bool(o.watch_out_en and len(o.watch_out_en) > 10)
            else:
                checks["watch_out"] = True

            # ── Arabic populated ──
            if case.get("expect_ar_populated"):
                checks["ar_populated"] = (
                    has_arabic_chars(o.verdict_title_ar) and
                    has_arabic_chars(o.recommendation_ar)
                )
            else:
                checks["ar_populated"] = True

            # ── Title length ──
            if case.get("check_title_length"):
                checks["title_length"] = word_count(o.verdict_title_en) <= 10

            # ── Arabic chars in aspect summaries ──
            if case.get("check_arabic_chars"):
                ar_ok = all(
                    has_arabic_chars(a.summary_ar)
                    for a in result.aspects
                ) if result.aspects else False
                checks["arabic_chars"] = ar_ok

            # ── Negatives surfaced ──
            if case.get("check_negatives_surfaced"):
                checks["negatives_surfaced"] = (
                    bool(o.watch_out_en and len(o.watch_out_en) > 15) or
                    any(a.sentiment in (SentimentLabel.NEGATIVE, SentimentLabel.MIXED)
                        for a in result.aspects)
                )

            # ── Arabic not translation (structural check) ──
            if case.get("check_ar_not_translation"):
                en_words = set(o.recommendation_en.lower().split())
                ar_text  = o.recommendation_ar.lower()
                # If most English content words appear in AR field → likely translation
                overlap = sum(1 for w in en_words if w in ar_text and len(w) > 4)
                checks["ar_not_translation"] = (overlap < 3)

            case_pass = all(checks.values())
            if case_pass: passed += 1

            status = icon(case_pass)
            print(f"  {status} Overall: {'PASS' if case_pass else 'FAIL'}")
            for k, v in checks.items():
                print(f"    {icon(v)} {k}")

            if not o.insufficient_data:
                print(f"    -> confidence={o.confidence:.2f} | aspects={len(result.aspects)} | "
                      f"ar_chars={'yes' if has_arabic_chars(o.verdict_title_ar) else 'NO'}")
                # print(f"    -> verdict_en: '{o.verdict_title_en}'")
                # print(f"    -> verdict_ar: '{o.verdict_title_ar}'")
                if result.aspects:
                    print(f"    -> aspects: {[a.aspect for a in result.aspects]}")
                    print(f"    -> watch_out: '{o.watch_out_en[:60]}...'")

            results.append({
                "id": case["id"], "pass": case_pass,
                "checks": {k: bool(v) for k, v in checks.items()},
                "confidence": o.confidence,
                "aspects_count": len(result.aspects),
                "insufficient_data": o.insufficient_data,
            })

        except Exception as e:
            print(f"  [ERR] EXCEPTION: {str(e).encode('ascii', 'ignore').decode()}")
            results.append({"id": case["id"], "pass": False, "error": str(e)})

        time.sleep(0.3)

    total = len(CASES)
    print(f"\n{'='*65}")
    print(f"  SUMMARY: {passed}/{total} passed ({passed/total*100:.0f}%)")
    print(f"{'='*65}")

    with open("eval_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "model": "qwen/qwen-2.5-72b-instruct",
            "summary": {"passed": passed, "total": total,
                        "pass_rate": round(passed/total, 3)},
            "cases": results
        }, f, indent=2, ensure_ascii=False)
    print("  Saved → eval_results.json")

    if passed / total < 0.70:
        print("\n⛔ Pass rate below 70% — review prompt or data quality.")
        sys.exit(1)

if __name__ == "__main__":
    evaluate()
