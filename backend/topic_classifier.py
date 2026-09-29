"""Industry-aware topic and sentiment detection for scraped Google Maps data.

The original classifier used fashion/salon keyword lists for every project, so
cafe reviews were labelled "New Collection" (matched the word "drop") or
"Casual & Streetwear" (matched "casual" inside place cards). This module keeps
the same public interface but classifies with:

  * an industry profile inferred from the project field / business profile,
  * whole-word matching (``drop`` never matches inside "drop by" place names),
  * a scored, best-match-wins topic selection instead of first-match-wins,
  * an honest generic profile for any industry we do not know yet.

Used by the scraper (new posts / reviews) and by the repair script that
re-classifies rows captured before the fix.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

CAFE_TOPICS: Dict[str, List[str]] = {
    "Coffee & Beverages": [
        "coffee", "espresso", "cappuccino", "latte", "americano", "mocha",
        "cold brew", "cold coffee", "frappe", "frappuccino", "brew", "beans",
        "roast", "roasted", "chai", "tea", "matcha", "hot chocolate", "cocoa",
        "smoothie", "milkshake", "shake", "mocktail", "lemonade", "juice",
        "beverage", "beverages", "drink", "drinks",
    ],
    "Food & Menu": [
        "food", "menu", "taste", "tasty", "tasted", "delicious", "flavour",
        "flavor", "flavours", "flavors", "dish", "dishes", "cuisine", "dessert",
        "desserts", "cake", "cakes", "pastry", "croissant", "sandwich",
        "sandwiches", "burger", "burgers", "pizza", "pasta", "fries", "wrap",
        "wraps", "salad", "breakfast", "brunch", "lunch", "dinner", "snack",
        "snacks", "appetizer", "starter", "platter", "cheese", "bakery",
        "bake", "baked", "brownie", "waffle", "pancake", "donut", "momos",
        "momo", "noodles", "biryani", "thali", "sizzler", "steak",
    ],
    "Service & Staff": [
        "staff", "service", "server", "waiter", "waitress", "barista",
        "friendly", "polite", "rude", "helpful", "courteous", "hospitality",
        "manager", "owner", "team", "attentive", "welcoming", "behaviour",
        "behavior", "attitude", "served", "quick service",
    ],
    "Ambience & Decor": [
        "ambience", "ambiance", "atmosphere", "vibe", "vibes", "decor",
        "decorated", "interior", "interiors", "music", "seating", "cozy",
        "cosy", "aesthetic", "charming", "beautiful", "peaceful", "calm",
        "garden", "outdoor", "rooftop", "quirky", "instagrammable",
    ],
    "Pricing & Value": [
        "price", "prices", "pricing", "expensive", "cheap", "affordable",
        "value", "worth", "cost", "costly", "overpriced", "bill", "budget",
        "pocket friendly", "money",
    ],
    "Offers & Promotions": [
        "offer", "offers", "discount", "discounts", "deal", "deals", "sale",
        "combo", "happy hour", "promo", "promotion", "coupon", "freebie",
        "buy one get one", "bogo", "flat off",
    ],
    "Location & Access": [
        "location", "located", "parking", "nearby", "near", "road", "street",
        "lane", "walkable", "accessible", "station", "landmark", "directions",
        "address", "commute",
    ],
    "Events & Community": [
        "event", "events", "live music", "workshop", "party", "celebration",
        "birthday", "anniversary", "tasting", "open mic", "gig", "gathering",
        "screening",
    ],
    "Hygiene & Comfort": [
        "clean", "cleanliness", "hygienic", "hygiene", "dirty", "washroom",
        "restroom", "toilet", "tidy", "comfortable", "air conditioning",
    ],
    "Ordering & Delivery": [
        "order", "orders", "ordering", "delivery", "deliver", "zomato",
        "swiggy", "takeaway", "take away", "parcel", "dine in", "dine in",
        "waiting", "wait time", "queue", "reservation", "booked a table",
    ],
}

SALON_TOPICS: Dict[str, List[str]] = {
    "Hair Care & Styling": [
        "hair", "haircut", "hair cut", "hairstyle", "styling", "stylist",
        "keratin", "balayage", "highlights", "blow dry", "blowdry", "colour",
        "color", "salon", "barber", "beard", "shave", "shaving", "fade",
        "trim", "layers", "hair spa",
    ],
    "Skin & Beauty": [
        "facial", "skin", "skincare", "glow", "makeup", "make up", "waxing",
        "wax", "threading", "clean up", "cleanup", "massage", "spa",
        "wellness", "manicure", "pedicure", "nails", "nail art", "bridal",
        "eyebrow", "lashes", "bleach", "detan",
    ],
    "Service & Staff": [
        "staff", "service", "friendly", "polite", "rude", "helpful",
        "courteous", "behaviour", "behavior", "attitude", "attentive",
        "professional", "team", "owner", "manager",
    ],
    "Pricing & Value": [
        "price", "prices", "pricing", "expensive", "cheap", "affordable",
        "value", "worth", "cost", "costly", "overpriced", "bill", "budget",
        "money", "package",
    ],
    "Offers & Promotions": [
        "offer", "offers", "discount", "discounts", "deal", "deals", "sale",
        "combo", "promo", "promotion", "coupon", "festive offer",
        "membership",
    ],
    "Appointments & Booking": [
        "appointment", "appointments", "booking", "booked", "book", "slot",
        "walk in", "waiting", "wait time", "queue", "reservation", "schedule",
        "availability",
    ],
    "Ambience & Hygiene": [
        "ambience", "ambiance", "atmosphere", "interior", "interiors", "clean",
        "cleanliness", "hygienic", "hygiene", "dirty", "tidy", "washroom",
        "relaxing", "relax", "comfortable", "cozy", "cosy",
    ],
    "Products & Brands": [
        "product", "products", "brand", "brands", "shampoo", "serum",
        "treatment", "treatments", "hair spa", "gel", "polish", "tools",
    ],
}


FASHION_TOPICS: Dict[str, List[str]] = {
    "New Collection": [
        "collection", "launch", "launched", "new arrival", "new arrivals",
        "arrival", "arrived", "latest", "new in", "drop", "line up",
        "spring summer", "autumn winter", "fresh stock",
    ],
    "Offers & Discounts": [
        "offer", "offers", "discount", "discounts", "sale", "save", "flat off",
        "deal", "deals", "price", "affordable", "pocket friendly",
        "festive offer", "special price", "clearance", "end of season",
        "buy one get one", "bogo",
    ],
    "Occasion & Party Wear": [
        "wedding", "party", "occasion", "festive", "celebration", "glam",
        "lehenga", "gown", "sherwani", "ethnic", "saree", "kurta", "bridal",
    ],
    "Workwear & Formals": [
        "workwear", "formal", "formals", "office", "professional", "blazer",
        "blazers", "trousers", "shirt", "shirts", "suit", "suits", "smart",
        "business", "corporate",
    ],
    "Casual & Streetwear": [
        "casual", "casuals", "t-shirt", "tshirt", "tees", "jeans", "denim",
        "hoodie", "hoodies", "sneakers", "streetwear", "street style",
        "everyday", "trendy", "oversized", "polo",
    ],
    "Store & Visit": [
        "store", "stores", "outlet", "showroom", "shop", "visited", "visit",
        "walk in", "located", "location", "shopping experience", "mall",
    ],
    "Quality & Fit": [
        "quality", "fit", "fits", "fabric", "material", "stitching",
        "tailoring", "size", "sizing", "comfortable", "durable", "finish",
    ],
    "Service & Staff": [
        "staff", "service", "friendly", "polite", "rude", "helpful",
        "courteous", "behaviour", "behavior", "attitude", "salesman",
        "sales executive", "team", "manager", "exchange", "return",
    ],
}

ECOMMERCE_TOPICS: Dict[str, List[str]] = {
    "Delivery & Speed": [
        "delivery", "deliver", "delivered", "shipping", "courier", "fast",
        "late delivery", "delayed", "express", "same day", "quick",
        "quick commerce", "instant",
    ],
    "Offers & Discounts": [
        "offer", "offers", "discount", "discounts", "sale", "coupon", "deal",
        "deals", "cashback", "promo", "promotion", "freebie", "price drop",
    ],
    "Product Range & Stock": [
        "product", "products", "range", "variety", "stock", "out of stock",
        "availability", "catalog", "catalogue", "options", "assortment",
    ],
    "App & Ordering Experience": [
        "app", "application", "interface", "checkout", "cart", "ordering",
        "order", "orders", "payment", "upi", "search", "filter", "bug",
        "glitch", "crash",
    ],
    "Packaging & Quality": [
        "packaging", "package", "packed", "leak", "leaked", "damaged",
        "fresh", "freshness", "quality", "expiry", "expired", "sealed",
    ],
    "Customer Support": [
        "support", "customer care", "helpline", "refund", "return",
        "replacement", "complaint", "chat support", "executive", "response",
    ],
}

GENERIC_TOPICS: Dict[str, List[str]] = {
    "Offers & Promotions": [
        "offer", "offers", "discount", "discounts", "deal", "deals", "sale",
        "combo", "promo", "promotion", "coupon", "festive offer", "save",
    ],
    "Service & Staff": [
        "staff", "service", "friendly", "polite", "rude", "helpful",
        "courteous", "behaviour", "behavior", "attitude", "team", "manager",
        "owner",
    ],
    "Quality & Experience": [
        "quality", "experience", "amazing", "excellent", "awesome", "great",
        "good", "wonderful", "perfect", "disappointing", "worst", "average",
    ],
    "Pricing & Value": [
        "price", "prices", "pricing", "expensive", "cheap", "affordable",
        "value", "worth", "cost", "costly", "overpriced", "bill", "budget",
    ],
    "Location & Access": [
        "location", "located", "parking", "nearby", "near", "road", "street",
        "lane", "accessible", "station", "directions", "address",
    ],
    "Updates & Announcements": [
        "update", "updates", "announcement", "announce", "new", "launch",
        "launched", "opening", "now open", "hours", "timing", "holiday",
        "closed",
    ],
}

INDUSTRY_TOPICS: Dict[str, Dict[str, List[str]]] = {
    "cafe": CAFE_TOPICS,
    "salon": SALON_TOPICS,
    "fashion": FASHION_TOPICS,
    "ecommerce": ECOMMERCE_TOPICS,
    "generic": GENERIC_TOPICS,
}

# Hints used to infer the industry from project field / profile / categories.
INDUSTRY_HINTS: Dict[str, List[str]] = {
    "cafe": [
        "cafe", "caf", "coffee", "coffee shop", "coffeeshop", "restaurant",
        "food", "foods", "food destination", "eatery", "diner", "bistro",
        "bakery", "sweets", "sweet shop", "fast food", "momos", "momo",
        "burger", "pizza", "fries", "juice", "tea", "bar", "buffet",
        "eateries", "kitchen", "cafe food", "brunch", "dessert",
    ],
    "salon": [
        "salon", "saloon", "hair", "hair styling", "beauty",
        "beauty parlour", "beauty parlor", "spa", "wellness", "grooming",
        "barber", "nails", "makeup", "skincare", "unisex salon",
    ],
    "fashion": [
        "fashion", "clothing", "clothing and accessories", "clothes", "cloth",
        "clothig", "apparel", "garment", "garments", "accessories",
        "accessoris", "accesories", "accesoris", "retail", "wear", "footwear",
        "shoes", "boutique", "jewellery", "jewelry",
    ],
    "ecommerce": [
        "e-commerce", "ecommerce", "quick commerce", "online", "marketplace",
        "online store", "online brand", "delivery app", "d2c",
    ],
}

# Topic used when nothing matches.
FALLBACK_TOPIC = "General Update"


def _normalize(text: Optional[str]) -> str:
    return (text or "").strip().lower()


def infer_industry(*hints: Optional[str]) -> str:
    """Infer the industry profile from free-text hints (project field/profile).

    Returns one of ``cafe``, ``salon``, ``fashion``, ``ecommerce`` or
    ``generic``. The industry with the most hint matches wins.
    """
    haystack = " ".join(_normalize(hint) for hint in hints if hint)
    if not haystack:
        return "generic"

    scores: Dict[str, int] = {}
    for industry, keywords in INDUSTRY_HINTS.items():
        score = 0
        for keyword in keywords:
            if re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", haystack):
                score += 1
        if score:
            scores[industry] = score

    if not scores:
        return "generic"
    # ``max`` keeps the first industry in insertion order on ties, so the
    # order of INDUSTRY_HINTS doubles as the tie-breaker priority.
    return max(scores, key=lambda industry: scores[industry])


def _match_keywords(text: str, keywords: List[str]) -> List[str]:
    """Whole-word matches of ``keywords`` inside ``text`` (lowercase)."""
    matched: List[str] = []
    for keyword in keywords:
        pattern = re.escape(keyword).replace(r"\ ", r"\s+")
        if re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", text):
            matched.append(keyword)
    return matched


def classify_topic(text: Optional[str], industry: Optional[str] = None) -> Tuple[str, List[str]]:
    """Classify ``text`` into an industry-appropriate topic.

    Returns ``(topic, keywords)`` where keywords are the matched domain terms
    (used by the keyword cloud / frequency charts).
    """
    if not text:
        return FALLBACK_TOPIC, []

    # Scraped text often concatenates labels; normalise whitespace for matching.
    haystack = re.sub(r"\s+", " ", _normalize(text))

    profile = INDUSTRY_TOPICS.get((industry or "").strip().lower()) or GENERIC_TOPICS

    best_topic = FALLBACK_TOPIC
    best_matches: List[str] = []
    for topic, keywords in profile.items():
        matches = _match_keywords(haystack, keywords)
        if len(matches) > len(best_matches):
            best_topic = topic
            best_matches = matches

    # Nothing matched in the industry profile: try the generic profile so a
    # cafe project can still surface "Offers & Promotions" etc.
    if not best_matches and profile is not GENERIC_TOPICS:
        for topic, keywords in GENERIC_TOPICS.items():
            matches = _match_keywords(haystack, keywords)
            if len(matches) > len(best_matches):
                best_topic = topic
                best_matches = matches

    return best_topic, best_matches[:8]




_STOPWORDS = {
    "this", "that", "with", "from", "your", "have", "more", "still", "cause",
    "what", "stay", "built", "next", "into", "they", "them", "their", "about",
    "just", "very", "here", "there", "which", "when", "where", "were", "will",
    "would", "could", "should", "been", "over", "also", "some", "such", "only",
    "than", "then", "these", "those", "much", "many", "most", "after", "before",
    "again", "because", "while", "does", "did", "doing", "made", "make",
}

# Tokens that come from Google Maps review chrome ("Local Guide · 190 reviews
# · 1,609 photos · 2 months ago") and must never become keywords.
_SCRAPE_NOISE = {
    "local", "guide", "reviews", "review", "photos", "photo", "months",
    "month", "years", "year", "weeks", "week", "days", "day", "ago", "like",
    "share", "edited", "response", "owner", "rated", "stars", "user",
}


def extract_keywords(text: Optional[str], extra_blocklist=None, limit: int = 8) -> List[str]:
    """Meaningful lowercase tokens from scraped text (no review chrome)."""
    if not text:
        return []
    blocked = set(_STOPWORDS) | set(_SCRAPE_NOISE)
    if extra_blocklist:
        blocked |= {_normalize(word) for word in extra_blocklist if word}
    words = re.findall(r"\b[a-zA-Z]{4,}\b", _normalize(text))
    keywords: List[str] = []
    for word in words:
        if word in blocked or word in keywords:
            continue
        keywords.append(word)
        if len(keywords) >= limit:
            break
    return keywords


POSITIVE_WORDS = (
    "amazing", "awesome", "excellent", "great", "good", "best", "loved",
    "love", "delicious", "tasty", "friendly", "helpful", "polite", "clean",
    "beautiful", "cozy", "cosy", "worth", "perfect", "wonderful", "fantastic",
    "recommend", "pleasant", "comfortable", "affordable", "fresh", "quick",
)
NEGATIVE_WORDS = (
    "worst", "rude", "terrible", "bad", "poor", "dirty", "expensive",
    "overpriced", "disappointing", "disappointed", "slow", "late", "stale",
    "cold", "awful", "horrible", "harassing", "complaint", "unhygienic",
    "delay", "delayed", "refund",
)


def classify_sentiment(text: Optional[str], rating: Optional[int] = None) -> Tuple[str, float]:
    """Sentiment label + score.

    A star rating (when the scraper captured one) is authoritative: 4-5 stars
    are positive, 3 stars neutral, 1-2 stars negative. Text keywords are the
    fallback for records without ratings.
    """
    if rating is not None:
        try:
            value = int(rating)
        except (TypeError, ValueError):
            value = None
        if value is not None:
            if value >= 4:
                return "Positive", 0.8
            if value == 3:
                return "Neutral", 0.0
            return "Negative", -0.8

    haystack = _normalize(text)
    if not haystack:
        return "Neutral", 0.0

    positives = sum(1 for word in POSITIVE_WORDS if re.search(rf"\b{word}\b", haystack))
    negatives = sum(1 for word in NEGATIVE_WORDS if re.search(rf"\b{word}\b", haystack))

    if positives > negatives:
        return "Positive", round(min(0.9, 0.4 + 0.1 * positives), 2)
    if negatives > positives:
        return "Negative", round(max(-0.9, -0.4 - 0.1 * negatives), 2)
    return "Neutral", 0.0

# ---------------------------------------------------------------------------
# Product-level vocabulary: WHICH exact product is trending inside a topic
# ---------------------------------------------------------------------------
# Each entry is ``(group, product, [aliases])``. Aliases are matched as whole
# words/phrases, so "cold coffee" counts as Cold Coffee while "coffee" alone
# stays a topic keyword. The group name doubles as the topic the product
# belongs to, letting the UI filter "Coffee & Beverages" -> espresso, latte…

CAFE_PRODUCTS: List[Tuple[str, str, List[str]]] = [
    # --- drinks ---------------------------------------------------------
    ("Coffee & Beverages", "Espresso", ["espresso", "espressos", "double shot"]),
    ("Coffee & Beverages", "Americano", ["americano", "americans"]),
    ("Coffee & Beverages", "Cappuccino", ["cappuccino", "cappuccinos", "capuccino"]),
    ("Coffee & Beverages", "Latte", ["latte", "lattes", "cafe latte", "caffè latte", "flat white"]),
    ("Coffee & Beverages", "Mocha", ["mocha", "mochas", "cafe mocha", "café mocha"]),
    ("Coffee & Beverages", "Macchiato", ["macchiato", "macchiatos"]),
    ("Coffee & Beverages", "Frappe", ["frappe", "frappes", "frappuccino", "frappuccinos", "frappe cold coffee"]),
    ("Coffee & Beverages", "Cold Brew", ["cold brew", "cold brews"]),
    ("Coffee & Beverages", "Cold Coffee", ["cold coffee", "iced coffee", "iced latte", "cold latte", "cold coffees"]),
    ("Coffee & Beverages", "Filter Coffee", ["filter coffee", "south indian coffee", "degree coffee"]),
    ("Coffee & Beverages", "Affogato", ["affogato"]),
    ("Coffee & Beverages", "Tea & Chai", ["tea", "teas", "chai", "masala chai", "cutting chai", "kadak chai", "green tea", "iced tea"]),
    ("Coffee & Beverages", "Matcha", ["matcha", "matcha latte"]),
    ("Coffee & Beverages", "Hot Chocolate", ["hot chocolate", "cocoa"]),
    ("Coffee & Beverages", "Milkshake", ["milkshake", "milkshakes", "thick shake", "shakes", "shake"]),
    ("Coffee & Beverages", "Protein Shake", ["protein shake", "dry fruit shake", "protein shakes"]),
    ("Coffee & Beverages", "Smoothie", ["smoothie", "smoothies"]),
    ("Coffee & Beverages", "Fresh Juice", ["juice", "juices", "fresh juice", "orange juice", "watermelon juice"]),
    ("Coffee & Beverages", "Mocktail & Mojito", ["mojito", "mojitos", "mocktail", "mocktails", "cooler"]),
    ("Coffee & Beverages", "Lemonade", ["lemonade", "nimbu pani", "lemon iced tea"]),
    ("Coffee & Beverages", "Boba", ["boba", "bubble tea", "tapioca"]),
    # --- food -----------------------------------------------------------
    ("Food & Menu", "Pizza", ["pizza", "pizzas"]),
    ("Food & Menu", "Pasta", ["pasta", "pastas", "spaghetti", "penne", "alfredo"]),
    ("Food & Menu", "Burger", ["burger", "burgers", "cheeseburger", "veg burger"]),
    ("Food & Menu", "Sandwich", ["sandwich", "sandwiches", "grilled sandwich", "club sandwich"]),
    ("Food & Menu", "Fries", ["fries", "french fries", "peri peri fries", "wedges"]),
    ("Food & Menu", "Momos", ["momos", "momo", "dumplings"]),
    ("Food & Menu", "Biryani", ["biryani", "biriyani"]),
    ("Food & Menu", "Noodles", ["noodles", "hakka noodles", "ramen", "maggi"]),
    ("Food & Menu", "Wrap & Roll", ["wrap", "wraps", "roll", "rolls", "shawarma", "kathi roll"]),
    ("Food & Menu", "Salad", ["salad", "salads"]),
    ("Food & Menu", "Breakfast & Brunch", ["breakfast", "brunch", "omelette", "omelet", "avocado toast"]),
    ("Food & Menu", "Pancakes & Waffles", ["pancake", "pancakes", "waffle", "waffles"]),
    ("Food & Menu", "Croissant", ["croissant", "croissants"]),
    ("Food & Menu", "Cake", ["cake", "cakes", "cheesecake", "cheese cake", "red velvet", "black forest"]),
    ("Food & Menu", "Brownie", ["brownie", "brownies"]),
    ("Food & Menu", "Cookie", ["cookie", "cookies"]),
    ("Food & Menu", "Pastry & Muffin", ["pastry", "pastries", "muffin", "muffins", "danish"]),
    ("Food & Menu", "Donut", ["donut", "donuts", "doughnut", "doughnuts"]),
    ("Food & Menu", "Sizzler", ["sizzler", "sizzlers"]),
    ("Food & Menu", "Steak", ["steak", "steaks"]),
    # --- flavours & specials -------------------------------------------
    ("Flavours & Specials", "Hazelnut", ["hazelnut", "hazelnuts"]),
    ("Flavours & Specials", "Caramel", ["caramel"]),
    ("Flavours & Specials", "Chocolate", ["chocolate", "dark chocolate", "choco"]),
    ("Flavours & Specials", "Vanilla", ["vanilla"]),
    ("Flavours & Specials", "Oreo", ["oreo", "oreos"]),
    ("Flavours & Specials", "Nutella", ["nutella"]),
    ("Flavours & Specials", "Biscoff & Lotus", ["biscoff", "lotus"]),
    ("Flavours & Specials", "Tiramisu", ["tiramisu"]),
    ("Flavours & Specials", "Pistachio", ["pistachio", "pistachios"]),
    ("Flavours & Specials", "Blueberry", ["blueberry", "blueberries"]),
    ("Flavours & Specials", "Strawberry", ["strawberry", "strawberries"]),
    ("Flavours & Specials", "Mango", ["mango", "mangoes"]),
    # --- momo shop variants --------------------------------------------
    ("Food & Menu", "Steamed Momos", ["steamed momo", "steamed momos", "steam momos"]),
    ("Food & Menu", "Fried Momos", ["fried momo", "fried momos", "kurkure momos"]),
    ("Food & Menu", "Tandoori Momos", ["tandoori momo", "tandoori momos", "gravy momos"]),
    ("Food & Menu", "Chicken Momos", ["chicken momo", "chicken momos"]),
    ("Food & Menu", "Paneer & Cheese Momos", ["paneer momo", "paneer momos", "cheese momo", "cheese momos"]),
    # --- indian sweets (sweet shop projects) ----------------------------
    ("Sweets & Mithai", "Gulab Jamun", ["gulab jamun", "gulab jamuns"]),
    ("Sweets & Mithai", "Rasgulla", ["rasgulla", "rasgullas", "rasmalai"]),
    ("Sweets & Mithai", "Kaju Katli", ["kaju katli", "kaju barfi"]),
    ("Sweets & Mithai", "Barfi", ["barfi", "burfi"]),
    ("Sweets & Mithai", "Laddoo", ["laddoo", "laddu", "ladoo"]),
    ("Sweets & Mithai", "Jalebi", ["jalebi", "jalebis", "imarti"]),
    ("Sweets & Mithai", "Peda", ["peda", "pedas", "malai peda"]),
    ("Sweets & Mithai", "Halwa", ["halwa", "gajar halwa", "sooji halwa"]),
    ("Sweets & Mithai", "Kulfi & Ice Cream", ["kulfi", "ice cream", "icecream", "sundae"]),
    ("Sweets & Mithai", "Soan Papdi", ["soan papdi", "son papdi"]),
    ("Sweets & Mithai", "Mysore Pak", ["mysore pak"]),
    # --- chinese restaurants --------------------------------------------
    ("Chinese & Asian", "Fried Rice", ["fried rice", "schezwan rice", "burnt garlic rice"]),
    ("Chinese & Asian", "Manchurian", ["manchurian", "manchurians", "gobi manchurian"]),
    ("Chinese & Asian", "Chowmein", ["chowmein", "chow mein", "hakka noodles", "schezwan noodles"]),
    ("Chinese & Asian", "Spring Rolls", ["spring roll", "spring rolls"]),
    ("Chinese & Asian", "Soup", ["soup", "soups", "manchow soup", "hot and sour soup"]),
    # --- street food & snacks -------------------------------------------
    ("Street Food & Snacks", "Samosa", ["samosa", "samosas", "punjabi samosa"]),
    ("Street Food & Snacks", "Kachori", ["kachori", "kachoris", "pyaaz kachori"]),
    ("Street Food & Snacks", "Chaat & Pani Puri", ["chaat", "pani puri", "golgappa", "bhel", "sevpuri", "dahi puri"]),
    ("Street Food & Snacks", "Vada Pav", ["vada pav", "vada pao", "misal pav"]),
    ("Street Food & Snacks", "Pav Bhaji", ["pav bhaji", "bhaji"]),
    ("Street Food & Snacks", "Dosa", ["dosa", "dosas", "masala dosa", "uttapam", "uttapa"]),
    ("Street Food & Snacks", "Idli & Vada", ["idli", "idlis", "medu vada", "vada"]),
    ("Street Food & Snacks", "Puffs & Patties", ["puff", "puffs", "patty", "patties", "veg puff"]),
    # --- indian beverages -------------------------------------------------
    ("Coffee & Beverages", "Lassi & Buttermilk", ["lassi", "buttermilk", "chaas", "sweet lassi", "mango lassi"]),
    ("Coffee & Beverages", "Falooda", ["falooda", "faluda"]),

]


SALON_PRODUCTS: List[Tuple[str, str, List[str]]] = [
    ("Hair Care & Styling", "Haircut", ["haircut", "hair cut", "haircuts", "trim"]),
    ("Hair Care & Styling", "Keratin & Smoothening", ["keratin", "smoothening", "smoothing", "rebonding", "botox"]),
    ("Hair Care & Styling", "Hair Colour", ["hair colour", "hair color", "global colour", "global color", "root touch up", "highlights", "balayage"]),
    ("Hair Care & Styling", "Blow Dry & Styling", ["blow dry", "blowdry", "hair styling", "curls", "straightening"]),
    ("Hair Care & Styling", "Hair Spa", ["hair spa", "hair treatment", "hair mask"]),
    ("Hair Care & Styling", "Beard & Shave", ["beard", "shave", "shaving", "fade", "beard trim"]),
    ("Skin & Beauty", "Facial", ["facial", "facials", "hydra facial", "hydrafacial", "clean up", "cleanup"]),
    ("Skin & Beauty", "Waxing & Threading", ["waxing", "wax", "threading", "eyebrow"]),
    ("Skin & Beauty", "Manicure & Pedicure", ["manicure", "pedicure", "nail art", "gel polish", "nails"]),
    ("Skin & Beauty", "Massage & Spa", ["massage", "body spa", "body massage", "aroma therapy"]),
    ("Skin & Beauty", "Makeup & Bridal", ["makeup", "make up", "bridal", "bridal makeup", "party makeup"]),
    ("Skin & Beauty", "Skin Treatments", ["skin treatment", "chemical peel", "detan", "de tan", "bleach"]),
]

FASHION_PRODUCTS: List[Tuple[str, str, List[str]]] = [
    ("New Collection", "Shirts", ["shirt", "shirts", "formal shirt", "casual shirt"]),
    ("New Collection", "T-Shirts", ["t-shirt", "t-shirts", "tshirt", "tshirts", "tees", "polo"]),
    ("New Collection", "Jeans & Denim", ["jeans", "denim", "jean"]),
    ("New Collection", "Trousers & Chinos", ["trousers", "trouser", "chinos", "pants", "formal pants"]),
    ("New Collection", "Blazers & Suits", ["blazer", "blazers", "suit", "suits", "two piece"]),
    ("New Collection", "Kurta & Ethnic", ["kurta", "kurtas", "saree", "lehenga", "ethnic wear", "sherwani"]),
    ("New Collection", "Dresses & Gowns", ["dress", "dresses", "gown", "gowns", "frock"]),
    ("New Collection", "Hoodies & Sweatshirts", ["hoodie", "hoodies", "sweatshirt", "sweatshirts", "sweater"]),
    ("New Collection", "Jackets", ["jacket", "jackets", "windcheater"]),
    ("New Collection", "Footwear", ["sneakers", "shoes", "footwear", "loafers", "sandals", "heels"]),
    ("New Collection", "Accessories", ["handbag", "wallet", "belt", "tie", "watch", "sunglasses", "accessories"]),
    ("New Collection", "Kurtis & Leggings", ["kurti", "kurtis", "leggings", "legging", "churidar"]),
    ("New Collection", "Co-ord Sets", ["co-ord", "coord set", "co ord set", "co-ord set", "matching set"]),
    ("New Collection", "Track & Activewear", ["track pants", "tracksuit", "joggers", "activewear", "gym wear"]),
    ("New Collection", "Night & Loungewear", ["nightwear", "pyjama", "pajama", "loungewear", "night suit"]),
]

ECOMMERCE_PRODUCTS: List[Tuple[str, str, List[str]]] = [
    ("Product Range & Stock", "Grocery Staples", ["atta", "rice", "dal", "oil", "sugar", "flour", "masala"]),
    ("Product Range & Stock", "Dairy & Eggs", ["milk", "eggs", "curd", "paneer", "butter", "cheese"]),
    ("Product Range & Stock", "Fruits & Vegetables", ["vegetables", "fruits", "onion", "tomato", "potato", "banana"]),
    ("Product Range & Stock", "Snacks & Beverages", ["snacks", "chips", "biscuits", "cold drinks", "ice cream", "chocolate"]),
    ("Product Range & Stock", "Home Care", ["detergent", "soap", "shampoo", "floor cleaner", "dishwash"]),
    ("Product Range & Stock", "Personal Care", ["toothpaste", "sanitary pads", "diapers", "face wash", "body lotion"]),
]

# Industry -> product library. Unknown industries see the cafe library because
# coffee/food terms are the most widely shared vocabulary in this app.
PRODUCT_LIBRARY: Dict[str, List[Tuple[str, str, List[str]]]] = {
    "cafe": CAFE_PRODUCTS,
    "salon": SALON_PRODUCTS,
    "fashion": FASHION_PRODUCTS,
    "ecommerce": ECOMMERCE_PRODUCTS,
    "generic": CAFE_PRODUCTS,
}


def extract_products(text: Optional[str], industry: Optional[str] = None) -> List[Tuple[str, str]]:
    """Return the ``(group, product)`` pairs mentioned in ``text``.

    Whole-word matching against the industry product library, so
    "Which coffee is trending?" becomes measurable: espresso, latte, frappe,
    cold brew, matcha … each counted per month by the trend analysis.
    """
    if not text:
        return []
    haystack = re.sub(r"\s+", " ", _normalize(text))
    library = PRODUCT_LIBRARY.get((industry or "").strip().lower()) or PRODUCT_LIBRARY["generic"]

    found: List[Tuple[str, str]] = []
    seen = set()
    for group, product, aliases in library:
        if product in seen:
            continue
        if _match_keywords(haystack, aliases):
            seen.add(product)
            found.append((group, product))
    return found

