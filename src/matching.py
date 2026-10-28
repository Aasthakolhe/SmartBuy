"""
Product matching and comparison engine.

Stores describe the same product differently, for example:
    Amazon   : "Apple iPhone 17 (256 GB) - Lavender: 6.3-inch Display with ProMotion, A19 Chip ..."
    Flipkart : "APPLE iPhone 17 (Lavender, 256 GB)"
    Croma    : "Apple iPhone 17 256GB Lavender"

Pipeline
  1. core title: drop marketing text after ':' '|' ';' (Amazon-style long titles)
  2. normalise (case, punctuation, "256 GB" -> "256gb", "1.5 Ton", colours/filler removed)
  3. relevance vs. the query: RapidFuzz token_set_ratio + typo-tolerant token recall
  4. hard filters: accessories/refurbished, wrong variant (Pro/Plus/FE/Edge...),
     wrong model number, wrong storage
  5. group offers into "same product" clusters:
       - catalogue offers carry a product_id -> exact grouping
       - live offers: canonical key (line word + model numbers + variants + sizes),
         then a merge pass that joins clusters whose key is a subset of another
         (e.g. a title that omits the RAM joins the one that states it)
  6. keep the cheapest offer per store inside each cluster
"""
from __future__ import annotations

import re
from collections import defaultdict

from src.catalog import BRANDS

try:
    from rapidfuzz import fuzz

    def _similarity(a: str, b: str) -> float:
        return float(fuzz.token_set_ratio(a, b))
except ImportError:  # graceful fallback
    from difflib import SequenceMatcher

    def _similarity(a: str, b: str) -> float:
        sa, sb = set(a.split()), set(b.split())
        if sa and sa <= sb:
            return 100.0
        return SequenceMatcher(None, " ".join(sorted(sa)), " ".join(sorted(sb))).ratio() * 100

COLORS = {
    "black", "white", "blue", "green", "red", "silver", "grey", "gray", "gold", "midnight",
    "starlight", "graphite", "navy", "titan", "nebula", "noir", "obsidian", "mica", "arctic",
    "bold", "purple", "pink", "yellow", "orange", "violet", "lavender", "mint", "cream",
    "titanium", "natural", "desert", "space", "jet", "porcelain", "rose", "teal", "ultramarine",
    "mist", "sage", "sky", "cosmic", "deep", "light", "dark", "jetblack", "icyblue", "coralred",
    "phantom", "shadow", "charcoal", "beige", "brown", "bronze", "copper", "aqua", "cyan", "lime",
    "coral", "peach", "ivory", "pearl", "frost", "moonstone", "hazel", "lilac", "magenta", "maroon",
}
FILLER = {"with", "and", "the", "of", "for", "by", "in", "new", "latest", "edition", "version",
          "a", "an", "to", "ram", "rom", "storage", "ssd", "inch", "inches", "cm", "generation",
          "gen", "unlocked", "smartphone", "mobile", "phone", "india", "dual", "sim"}
VARIANTS = {"pro", "max", "plus", "ultra", "mini", "lite", "fe", "se", "neo", "prime", "edge",
            "air", "fusion", "stylus", "xl", "fold", "classic", "turbo"}
ACCESSORIES = {"case", "cover", "tempered", "protector", "charger", "cable", "adapter", "skin",
               "strap", "stand", "holder", "mount", "pouch", "sleeve", "guard", "refurbished",
               "renewed", "replacement", "decal", "sticker", "dummy", "compatible", "back"}
GENERIC_NUMERIC = {"5g", "4g", "2nd", "3rd", "1st", "4th", "5th", "10th", "11th", "12th", "13th",
                   "14th", "2024", "2025", "2026"}
_BRAND_STOP = {"star", "audio", "ears", "ultimate", "blue", "by", "home", "digital"}
BRAND_WORDS = {w for b in BRANDS for w in re.sub(r"[^a-z0-9 ]", " ", b.lower()).split()} - _BRAND_STOP
BRAND_WORDS |= {"bluestar", "mi", "redmi", "poco", "iqoo", "jbl", "boat", "apple", "samsung"}
MATCH_THRESHOLD = 70
SYNONYMS = [("blue star", "bluestar"), ("playstation 5", "ps5"), ("playstation", "ps"), ("television", "tv"),
            ("refrigerator", "fridge"), ("air conditioner", "ac"), ("earphones?", "earphone"),
            ("ear buds", "earbuds"), ("note book", "notebook"), ("i phone", "iphone")]


def core_title(title: str) -> str:
    """Strip marketing text: 'Apple iPhone 17 (256 GB) - Black: 6.3-inch Display ...' -> before ':'."""
    core = re.split(r"[:|;]|\.\s|\s[–—]\s", title or "", maxsplit=1)[0]
    return core if len(core.split()) >= 2 else (title or "")


def normalize(text: str) -> str:
    t = (text or "").lower()
    t = (t.replace("+ cellular", " cellular").replace("wi-fi", "wifi")
          .replace("+", " plus ").replace("ultra hd", "uhd").replace("full hd", "fhd"))
    t = re.sub(r"(\d+(?:\.\d+)?)\s*(gb|tb|mm|mp|hz|w|l|litres?|kg|mah)\b", r"\1\2", t)
    t = re.sub(r"[^a-z0-9.\s]", " ", t)
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)
    for a, b in SYNONYMS:
        t = re.sub(rf"\b{a}\b", b, t)
    out = []
    for w in t.split():
        if w in COLORS or w in FILLER:
            continue
        if len(w) > 4 and w.isalpha() and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]  # plural -> singular (headphones -> headphone)
        out.append(w)
    return " ".join(out)


def _gb(tok: str) -> float | None:
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(gb|tb)", tok)
    return float(m.group(1)) * (1024 if m.group(2) == "tb" else 1) if m else None


def attributes(norm: str) -> dict:
    tokens = norm.split()
    sizes = sorted({t for t in tokens if _gb(t)}, key=_gb)
    storage = sizes[-1] if sizes and _gb(sizes[-1]) >= 32 else None
    model_nums = {t for t in tokens if re.search(r"\d", t) and _gb(t) is None and t not in GENERIC_NUMERIC}
    words = [t for t in tokens if not re.search(r"\d", t)]
    line = next((w for w in words if w not in BRAND_WORDS and w not in VARIANTS), "")
    return {
        "tokens": set(tokens), "sizes": set(sizes), "storage": storage, "model_nums": model_nums,
        "variants": {t for t in tokens if t in VARIANTS}, "line": line,
        "accessory": bool(set(tokens) & ACCESSORIES),
    }


def _key_parts(title: str) -> tuple:
    a = attributes(normalize(core_title(title)))
    return a["line"], frozenset(a["model_nums"]), frozenset(a["variants"]), frozenset(a["sizes"]), a["storage"]


def product_key(title: str) -> str:
    """Canonical key used to group live offers and to look up logged price history."""
    line, nums, variants, sizes, _ = _key_parts(title)
    return " ".join([line, *sorted(nums), *sorted(variants), *sorted(sizes, key=_gb)]).strip()


def relevance(query: str, title: str) -> tuple[float, str | None]:
    """Score 0-100 and a rejection reason (None if the offer is a valid match)."""
    q, t = normalize(query), normalize(core_title(title))
    qa, ta = attributes(q), attributes(t)
    score = _similarity(q, t)
    if qa["tokens"]:  # token recall: most query words must appear in the title (typo-tolerant)
        found = sum(1 for w in qa["tokens"]
                    if w in ta["tokens"] or any(x[0] == w[0] and _similarity(w, x) >= 85
                                                for x in ta["tokens"] if len(w) > 3))
        recall = found / len(qa["tokens"])
        score = max(score, 100 * recall)
        if recall < 0.6:
            return score, "missing search words"
    q_brands, t_brands = qa["tokens"] & BRAND_WORDS, ta["tokens"] & BRAND_WORDS
    if q_brands and t_brands and not (q_brands & t_brands):
        return score, "different brand"
    if ta["accessory"] and not qa["accessory"]:
        return score, "accessory / refurbished"
    if ta["variants"] != qa["variants"]:
        return score, "different variant"
    if qa["storage"] and ta["storage"] and qa["storage"] != ta["storage"]:
        return score, "different storage"
    missing = {n for n in qa["model_nums"]
               if n not in ta["tokens"] and not (len(n) >= 3 and any(n in tok for tok in ta["tokens"]))}
    if missing:
        return score, "different model"
    if score < MATCH_THRESHOLD:
        return score, "low similarity"
    if re.search(r"\bfor\b", core_title(title).lower()) and not re.search(r"\bfor\b", query.lower()):
        score -= 15  # "Controller for PS5", "Keyboard for iPad": rank below the product itself
    return score, None


def _merge_live_groups(groups: dict[str, list], parts: dict[str, tuple]) -> dict[str, list]:
    """Merge a cluster into the unique cluster whose key is a superset (same line/variant/storage)."""
    keys = sorted(groups, key=lambda k: len(parts[k][1]) + len(parts[k][3]))
    for k in keys:
        line, nums, var, sizes, storage = parts[k]
        supers = [o for o in groups if o != k and parts[o][0] == line and parts[o][2] == var
                  and parts[o][4] == storage and nums <= parts[o][1] and sizes <= parts[o][3]
                  and (nums, sizes) != (parts[o][1], parts[o][3])]
        if len(supers) == 1:
            groups[supers[0]].extend(groups.pop(k))
    return groups


def match_offers(query: str, offers: list[dict]) -> dict:
    """
    Returns {"groups": [...], "rejected": [...]}.
    Each group: {"key", "name", "offers" (cheapest per store), "stores", "score", "min_price"}.
    Groups are sorted best-first (most stores, then most relevant, then cheapest).
    """
    groups: dict[str, list] = defaultdict(list)
    parts: dict[str, tuple] = {}
    names: dict[str, str] = {}
    rejected = []
    for o in offers:
        score, reason = relevance(query, o["title"])
        o = {**o, "match_score": round(score, 1)}
        if reason:
            rejected.append({**o, "reason": reason})
            continue
        if o.get("product_id"):
            key = o["product_id"]
            names[key] = o.get("display_name") or o["title"]
        else:
            key = product_key(o["title"])
            parts[key] = _key_parts(o["title"])
        o["product_key"] = key
        groups[key].append(o)

    live = {k: v for k, v in groups.items() if k in parts}
    if len(live) > 1:
        merged = _merge_live_groups(dict(live), parts)
        groups = {**{k: v for k, v in groups.items() if k not in parts}, **merged}

    result = []
    for key, items in groups.items():
        best: dict[str, dict] = {}
        for o in items:
            o["product_key"] = key
            if o["store"] not in best or o["price"] < best[o["store"]]["price"]:
                best[o["store"]] = o
        chosen = sorted(best.values(), key=lambda o: o["price"])
        name = names.get(key) or core_title(max(chosen, key=lambda o: o["match_score"])["title"])
        result.append({"key": key, "name": name, "offers": chosen, "stores": len(chosen),
                       "score": sum(o["match_score"] for o in chosen) / len(chosen),
                       "min_price": chosen[0]["price"]})
    result.sort(key=lambda g: (-g["stores"], -g["score"], g["min_price"]))
    return {"groups": result, "rejected": rejected}
