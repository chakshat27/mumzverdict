"""
MumzVerdicts — Synthetic Review Generator
Generates realistic Mumzworld-style product reviews in EN and AR.
No scraping. All synthetic. Run: python data/generate_reviews.py
"""
import json, random
random.seed(42)

PRODUCTS = [
    {
        "product_id": "MW-STROLLER-001",
        "name_en": "Maclaren Quest Stroller – Black",
        "name_ar": "عربة ماكلارين كويست – أسود",
        "category": "strollers",
        "price_aed": 1499,
    },
    {
        "product_id": "MW-CARSEAT-002",
        "name_en": "Graco 4Ever DLX 4-in-1 Car Seat",
        "name_ar": "كرسي سيارة جراكو 4 في 1 ديلوكس",
        "category": "car_seats",
        "price_aed": 1899,
    },
    {
        "product_id": "MW-FORMULA-003",
        "name_en": "Aptamil Profutura Stage 1 Formula 800g",
        "name_ar": "حليب أبتاميل برو فوتورا مرحلة 1 – 800 جرام",
        "category": "formula",
        "price_aed": 220,
    },
    {
        "product_id": "MW-CARRIER-004",
        "name_en": "Ergobaby Omni 360 Baby Carrier – Grey",
        "name_ar": "حمالة إرغوبيبي أومني 360 – رمادي",
        "category": "carriers",
        "price_aed": 899,
    },
]

# ── Review templates per product ──────────────────────────────────────────────
REVIEW_POOL = {
    "MW-STROLLER-001": {
        "en": [
            {"rating": 5, "text": "Best stroller I've ever used. Folds in one hand while holding my baby — game changer for a mum on the go. The seat reclines fully so my newborn naps comfortably during our morning walks.", "age": "3 months", "aspect": "fold"},
            {"rating": 5, "text": "Used this stroller through two kids now. The suspension handles Dubai pavements beautifully. Basket underneath is huge — fits my whole grocery run. Worth every dirham.", "age": "14 months", "aspect": "durability"},
            {"rating": 4, "text": "Lightweight and easy to push. Canopy could be bigger for our harsh UAE sun but overall very happy. Delivery from Mumzworld was super fast — arrived next day!", "age": "6 months", "aspect": "canopy"},
            {"rating": 5, "text": "Love how compact it is for travel. Fits in the overhead bin on flydubai. My daughter loves the roomy seat and the five-point harness feels very secure.", "age": "18 months", "aspect": "travel"},
            {"rating": 3, "text": "Good quality but the front wheel wobbles a bit on uneven surfaces. Also took some time to figure out the fold mechanism. Customer service was helpful when I called though.", "age": "9 months", "aspect": "wheels"},
            {"rating": 2, "text": "Disappointed — the canopy stitching started fraying after 4 months of regular use. Maclaren UK sent a replacement part but the process took 3 weeks. For this price I expected better.", "age": "4 months", "aspect": "quality"},
            {"rating": 5, "text": "Perfect for Brunch Friday walks in JBR. Pushes smoothly on the boardwalk, folds quickly when we jump in a taxi. My 2-year-old falls asleep in it every time.", "age": "24 months", "aspect": "smooth ride"},
            {"rating": 4, "text": "Sturdy and well made. The harness adjustment is a bit fiddly but once set it stays. Rain cover included was a pleasant surprise — used it on our London trip.", "age": "11 months", "aspect": "harness"},
            {"rating": 5, "text": "أفضل عربة استخدمتها. الطي سهل جداً وأنا أحمل طفلتي بيدي الثانية. خفيفة الوزن ومناسبة لأسفارنا الكثيرة.", "age": "5 months", "aspect": "ease of use", "lang": "ar"},
            {"rating": 4, "text": "جودة ممتازة والمقعد مريح جداً لطفلي. المظلة صغيرة نوعاً ما لشمس الإمارات القوية لكن بشكل عام أنا راضية. التوصيل من ممزورلد كان في اليوم التالي.", "age": "8 months", "aspect": "canopy", "lang": "ar"},
            {"rating": 5, "text": "اشتريتها لطفلي الثاني وهي أفضل من العربة الأولى التي اشتريتها بسعر أعلى. خفيفة، متينة، والسلة من تحت واسعة جداً.", "age": "2 months", "aspect": "value", "lang": "ar"},
            {"rating": 3, "text": "المنتج جيد لكن العجلة الأمامية تتذبذب أحياناً على الأرصفة. كنت أتوقع أفضل لهذا السعر.", "age": "7 months", "aspect": "wheels", "lang": "ar"},
            {"rating": 5, "text": "Our third Maclaren. Never going back to any other brand. The seat holds up to 25kg so she'll use it for years. The UPF50 canopy is important in the GCC heat.", "age": "36 months", "aspect": "longevity"},
            {"rating": 1, "text": "Broke after 6 months. The recline button stopped working and one wheel cracked. Returned it but the process took 2 weeks. Very let down.", "age": "6 months", "aspect": "durability"},
            {"rating": 5, "text": "My physio recommended this for my back — the handlebar height is perfect and I don't have to hunch. Major plus when you're pushing a stroller for hours at the mall.", "age": "10 months", "aspect": "ergonomics"},
        ],
        "summary_aspects": ["fold mechanism", "canopy size", "wheel stability", "weight", "durability", "travel suitability"],
    },
    "MW-CARSEAT-002": {
        "en": [
            {"rating": 5, "text": "Installed it in under 20 minutes with the ISOFIX. My newborn looks so secure and comfortable. The no-rethread harness is brilliant — adjusted it in seconds as she grew.", "age": "0 months", "aspect": "installation"},
            {"rating": 5, "text": "Now using it in the third configuration for my 3-year-old. Incredible value — one seat from birth to booster. The steel frame makes me feel confident in safety.", "age": "36 months", "aspect": "longevity"},
            {"rating": 4, "text": "Great seat, very solid. Bit heavy to move between cars but we don't do that often. The Simply Safe Adjust harness is so easy — no rethreading ever.", "age": "12 months", "aspect": "weight"},
            {"rating": 3, "text": "Good safety features but the cupholder is poorly placed — my toddler can't reach it. Also fabric stains easily even with the cover on.", "age": "18 months", "aspect": "fabric"},
            {"rating": 5, "text": "حمدالله على هذا المقعد. التركيب كان سهلاً جداً مع ISOFIX. ابني يرتاح فيه خلال رحلاتنا الطويلة من دبي لأبوظبي.", "age": "4 months", "aspect": "comfort", "lang": "ar"},
            {"rating": 5, "text": "أفضل استثمار لسلامة طفلتي. استخدمناه من المولد وعمرها الآن سنتان ونصف وما زلنا نستخدمه. جودة عالية جداً.", "age": "30 months", "aspect": "safety", "lang": "ar"},
            {"rating": 2, "text": "The straps twisted constantly on our newborn. We had to call Graco support twice to figure out the correct routing. Instructions could be much clearer.", "age": "1 month", "aspect": "straps"},
            {"rating": 5, "text": "My husband installed it watching one YouTube video. No experience with car seats and he got it done correctly first try. That's how intuitive the design is.", "age": "2 months", "aspect": "installation"},
            {"rating": 4, "text": "Side impact protection is reassuring. The seat feels very premium and solid. Took off one star because it's heavy and the UAE heat makes the fabric uncomfortable in summer.", "age": "9 months", "aspect": "heat"},
            {"rating": 3, "text": "المقعد جيد من ناحية السلامة لكنه ثقيل جداً إذا احتجت نقله بين سيارتين. النسيج يمتص الحرارة في الصيف وهذا غير مريح لطفلي.", "age": "15 months", "aspect": "weight", "lang": "ar"},
            {"rating": 5, "text": "Pediatrician recommended this brand specifically. The rear-facing up to 40lbs is so important for extended rear-facing. My 18-month-old still rear-faces comfortably.", "age": "18 months", "aspect": "safety"},
            {"rating": 1, "text": "Buckle started sticking at 8 months. Very dangerous — sometimes took 30 seconds to unbuckle in an emergency. Returned immediately.", "age": "8 months", "aspect": "buckle"},
            {"rating": 5, "text": "The recline positions are great. My baby sleeps in the fully reclined rear-facing position and wakes up happy. We've done 4-hour drives without a single complaint from her.", "age": "5 months", "aspect": "recline"},
        ],
        "summary_aspects": ["installation ease", "safety rating", "longevity", "heat management", "harness system", "weight"],
    },
    "MW-FORMULA-003": {
        "en": [
            {"rating": 5, "text": "My LC recommended Aptamil when I had to supplement breastfeeding. My son took to it immediately with zero digestive issues. So relieved to find something that works.", "age": "6 weeks", "aspect": "digestion"},
            {"rating": 5, "text": "تحولنا لهذا الحليب بعد نصيحة طبيب الأطفال. طفلتي تحبه ولا يسبب لها أي مغص. شكراً ممزورلد على التوصيل السريع.", "age": "2 months", "aspect": "digestion", "lang": "ar"},
            {"rating": 4, "text": "Good formula, mixes well without clumps. Slightly pricey but you can't compromise on nutrition. Subscribe and save option on Mumzworld makes it affordable.", "age": "3 months", "aspect": "value"},
            {"rating": 5, "text": "My paediatrician specifically recommended Profutura for its HMO content. No colic, no reflux, no constipation. My baby thrives on it.", "age": "1 month", "aspect": "nutrition"},
            {"rating": 3, "text": "Formula is good quality but the lid mechanism broke on our second tin. Had to transfer to a separate container. Aptamil should improve the packaging.", "age": "4 months", "aspect": "packaging"},
            {"rating": 5, "text": "الحمد لله هذا الحليب حل مشكلة المغص عند طفلي تماماً. جربنا ثلاثة أنواع قبله وهذا هو الأفضل.", "age": "6 weeks", "aspect": "colic", "lang": "ar"},
            {"rating": 5, "text": "Transitioned from breastfeeding at 6 months. Baby accepted it without fussing — big relief. The scoop fits perfectly in the tin unlike some other brands.", "age": "6 months", "aspect": "transition"},
            {"rating": 4, "text": "Excellent formula with probiotics. Baby's stools are healthy and she's gaining weight beautifully. A little pricey but worth every fils for her health.", "age": "2 months", "aspect": "nutrition"},
            {"rating": 2, "text": "Made my baby very gassy. Tried it for 2 weeks hoping she'd adjust but the discomfort continued. Switched to another brand and she's much happier.", "age": "3 months", "aspect": "gas"},
            {"rating": 5, "text": "Dissolves instantly in warm water — no lumps at all. This matters at 3am when you're exhausted and need to make a bottle fast. Highly recommend.", "age": "1 month", "aspect": "mixing"},
        ],
        "summary_aspects": ["digestion tolerance", "mixing quality", "nutrition profile", "colic relief", "value for money", "packaging"],
    },
    "MW-CARRIER-004": {
        "en": [
            {"rating": 5, "text": "Life changing. My colicky baby only settles when held upright — this carrier lets me do laundry, cook, and work while she sleeps on my chest. The lumbar support saved my back.", "age": "6 weeks", "aspect": "lumbar support"},
            {"rating": 5, "text": "Used in all four positions — newborn, infant, toddler back carry. Now my 2.5 year old goes back carry on our hiking trips. Best investment I made as a mum.", "age": "30 months", "aspect": "longevity"},
            {"rating": 4, "text": "Very comfortable and baby is happy. A bit warm in UAE summer but that's expected with any carrier. The hip-healthy seat position is reassuring for our orthopedic check-ups.", "age": "4 months", "aspect": "heat"},
            {"rating": 3, "text": "Took me 45 minutes and three YouTube videos to figure out the buckles the first time. Once you get it it's fine but the learning curve is steep.", "age": "2 months", "aspect": "learning curve"},
            {"rating": 5, "text": "حمالة رائعة. طفلتي تنام فيها فوراً. الدعم للظهر والخصر ممتاز وأنا أستطيع حمل أغراض التسوق وهي نائمة.", "age": "3 months", "aspect": "back support", "lang": "ar"},
            {"rating": 4, "text": "ممتازة لكن تسخن كثيراً في الصيف. استخدمتها في الشتاء بشكل أساسي وهي رائعة. طفلي مرتاح جداً في وضعية الجلوس الطبيعية.", "age": "5 months", "aspect": "heat", "lang": "ar"},
            {"rating": 5, "text": "My physio cleared me to babywear at 8 weeks postpartum and specifically recommended Ergobaby for the weight distribution. No back pain after hours of wearing.", "age": "8 weeks", "aspect": "back support"},
            {"rating": 2, "text": "The chest clip pinches my neck in the front carry position. My husband can wear it comfortably but I can't due to my narrow shoulders. Size S would help but isn't sold here.", "age": "3 months", "aspect": "fit"},
            {"rating": 5, "text": "Wore my daughter in this for her whole first year. She had hip dysplasia and the wide knee-to-knee seat was doctor-approved for her treatment period.", "age": "12 months", "aspect": "hip health"},
            {"rating": 4, "text": "الجودة ممتازة وطفلي يحب أن يكون قريباً مني. فقط أتمنى لو كان هناك تهوية أفضل للصيف. بخلاف ذلك هي حمالة رائعة للاستخدام اليومي.", "age": "4 months", "aspect": "ventilation", "lang": "ar"},
        ],
        "summary_aspects": ["back/lumbar support", "heat management", "learning curve", "hip health", "longevity", "fit for body type"],
    },
}

def build_dataset():
    all_reviews = []
    review_id = 1000
    for product in PRODUCTS:
        pid = product["product_id"]
        pool = REVIEW_POOL[pid]["en"]
        for rev in pool:
            lang = rev.get("lang", "en")
            all_reviews.append({
                "review_id": f"RV-{review_id}",
                "product_id": pid,
                "product_name_en": product["name_en"],
                "product_name_ar": product["name_ar"],
                "category": product["category"],
                "rating": rev["rating"],
                "review_text": rev["text"],
                "language": lang,
                "child_age_at_review": rev["age"],
                "review_aspect": rev["aspect"],
                "verified_purchase": True,
            })
            review_id += 1

    with open("data/reviews.json", "w", encoding="utf-8") as f:
        json.dump(all_reviews, f, indent=2, ensure_ascii=False)

    with open("data/products.json", "w", encoding="utf-8") as f:
        json.dump(PRODUCTS, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(all_reviews)} reviews across {len(PRODUCTS)} products.")
    for p in PRODUCTS:
        pid = p["product_id"]
        count = sum(1 for r in all_reviews if r["product_id"] == pid)
        print(f"  {pid}: {count} reviews")

if __name__ == "__main__":
    build_dataset()
