import re
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class Product(BaseModel):
    id: str
    name: str
    tagline: str
    category: str
    pricePaise: int
    image: str
    tags: List[str]
    stock: int

CATALOG_RAW = [
  { "id": "trail-anc-headphones", "name": "Trail ANC Headphones", "tagline": "Over-ear, 40h, adaptive noise cancelling", "category": "audio", "pricePaise": 1899900, "image": "/products/trail-anc-headphones.jpg", "tags": ["headphones", "anc", "audio", "over-ear", "music", "travel"], "stock": 14 },
  { "id": "field-mech-65", "name": "Field Mech 65", "tagline": "65% hot-swap keyboard, gasket mount", "category": "desk", "pricePaise": 749900, "image": "/products/field-mech-65.jpg", "tags": ["keyboard", "mechanical", "typing", "desk", "hotswap"], "stock": 22 },
  { "id": "ridge-mouse", "name": "Ridge Mouse", "tagline": "8k sensor, 78g, silent switches", "category": "desk", "pricePaise": 219900, "image": "/products/ridge-mouse.jpg", "tags": ["mouse", "pointing", "desk", "silent", "lightweight"], "stock": 40 },
  { "id": "arc-light-bar", "name": "Arc Light Bar", "tagline": "Asymmetric desk light, zero glare", "category": "desk", "pricePaise": 349900, "image": "/products/arc-light-bar.jpg", "tags": ["light", "lamp", "desk", "screen", "bar"], "stock": 18 },
  { "id": "vault-ssd-1tb", "name": "Core GPU 8GB", "tagline": "8GB GDDR6, dual-fan, rendering-ready", "category": "power", "pricePaise": 3499900, "image": "/products/vault-ssd-1tb.jpg", "tags": ["gpu", "graphics", "gaming", "rendering", "pc", "video"], "stock": 6 },
  { "id": "cell-powerbank-20k", "name": "Cell Power Bank 20K", "tagline": "20,000mAh, 100W PD, airline-legal", "category": "power", "pricePaise": 299900, "image": "/products/cell-powerbank-20k.jpg", "tags": ["powerbank", "battery", "charging", "power", "usb-c", "travel"], "stock": 30 },
  { "id": "junction-hub-7", "name": "Junction Hub 7-in-1", "tagline": "USB-C dock: 4k HDMI, 100W passthrough", "category": "power", "pricePaise": 429900, "image": "/products/junction-hub-7.jpg", "tags": ["hub", "dock", "usb-c", "adapter", "hdmi", "ports"], "stock": 27 },
  { "id": "slate-desk-mat", "name": "Slate Desk Mat", "tagline": "900×400 wool felt, charcoal", "category": "desk", "pricePaise": 129900, "image": "/products/slate-desk-mat.jpg", "tags": ["mat", "desk", "felt", "pad", "wool"], "stock": 35 },
  { "id": "riser-stand", "name": "Riser Laptop Stand", "tagline": "Machined alloy, folds to 9mm", "category": "desk", "pricePaise": 289900, "image": "/products/riser-stand.jpg", "tags": ["stand", "laptop", "riser", "ergonomics", "desk"], "stock": 21 },
  { "id": "paper-ereader", "name": "Psychology of Money — Hardcover", "tagline": "Timeless lessons on wealth, greed and happiness", "category": "desk", "pricePaise": 49900, "image": "/products/paper-ereader.jpg", "tags": ["book", "money", "finance", "reading", "hardcover", "wealth", "gift"], "stock": 50 },
  { "id": "bud-pro-earbuds", "name": "Bud Pro Earbuds", "tagline": "ANC, wireless case, multipoint", "category": "audio", "pricePaise": 499900, "image": "/products/bud-pro-earbuds.jpg", "tags": ["earbuds", "buds", "audio", "anc", "music", "wireless"], "stock": 44 },
  { "id": "beacon-speaker", "name": "Beacon Speaker", "tagline": "Room-filling, 24h, aux-in", "category": "audio", "pricePaise": 699900, "image": "/products/beacon-speaker.jpg", "tags": ["speaker", "audio", "bluetooth", "music", "sound"], "stock": 15 },
  { "id": "dial-field-watch", "name": "Dial Field Watch", "tagline": "Sapphire glass, 100m, titanium case", "category": "field", "pricePaise": 1299900, "image": "/products/dial-field-watch.jpg", "tags": ["watch", "timepiece", "field", "titanium", "gift"], "stock": 11 },
  { "id": "shade-sunglasses", "name": "Shade Sunglasses", "tagline": "Polarized, UV400, acetate frame", "category": "vision", "pricePaise": 349900, "image": "/products/shade-sunglasses.jpg", "tags": ["sunglasses", "eyewear", "polarized", "summer", "gift"], "stock": 28 },
  { "id": "lens-camera-r2", "name": "Lens R2 Camera", "tagline": "26MP APS-C, hybrid viewfinder", "category": "vision", "pricePaise": 2499900, "image": "/products/lens-camera-r2.jpg", "tags": ["camera", "photography", "26mp", "viewfinder"], "stock": 7 },
  { "id": "pocket-multitool", "name": "Pocket Multitool 12", "tagline": "12 tools, aircraft steel, pocket clip", "category": "field", "pricePaise": 189900, "image": "/products/pocket-multitool.jpg", "tags": ["multitool", "tool", "edc", "knife", "pliers", "pocket"], "stock": 33 },
  { "id": "traverse-backpack-22", "name": "Traverse Backpack 22L", "tagline": "Weatherproof, luggage pass-through", "category": "carry", "pricePaise": 599900, "image": "/products/traverse-backpack-22.jpg", "tags": ["backpack", "bag", "carry", "travel", "laptop", "commute"], "stock": 17 },
  { "id": "globe-adapter", "name": "Globe Travel Adapter", "tagline": "70W, 4 plugs, one brick", "category": "field", "pricePaise": 44900, "image": "/products/globe-adapter.jpg", "tags": ["adapter", "travel", "charger", "plug", "international", "power"], "stock": 60 },
  { "id": "temp-ir-thermometer", "name": "Heritage Monitor", "tagline": "Over-ear, 40mm drivers, leather-and-steel", "category": "audio", "pricePaise": 799900, "image": "/products/temp-ir-thermometer.jpg", "tags": ["headphones", "over-ear", "audio", "music", "heritage", "leather"], "stock": 20 },
  { "id": "signal-router", "name": "Signal Router", "tagline": "WiFi 6, mesh-ready, 2.5GbE WAN", "category": "power", "pricePaise": 329900, "image": "/products/signal-router.jpg", "tags": ["router", "wifi", "network", "mesh", "internet"], "stock": 19 },
  { "id": "summit-drone-4k", "name": "Summit Drone 4K", "tagline": "3-axis gimbal, 34-min flights, sub-249g", "category": "vision", "pricePaise": 5499900, "image": "/products/summit-drone-4k.jpg", "tags": ["drone", "camera", "aerial", "4k", "video", "flight"], "stock": 4 },
]

CATALOG = [Product(**p) for p in CATALOG_RAW]

class CatalogSnapshot(BaseModel):
    byId: Dict[str, Product]
    all: List[Product]
    merchantPublicKeyPem: str
    merchantFingerprint: str

def catalog_snapshot(merchantPublicKeyPem: str, merchantFingerprint: str) -> CatalogSnapshot:
    return CatalogSnapshot(
        byId={p.id: p for p in CATALOG},
        all=CATALOG,
        merchantPublicKeyPem=merchantPublicKeyPem,
        merchantFingerprint=merchantFingerprint
    )

SYNONYMS = {
  "headphones": ["earbuds", "buds", "earphones"],
  "earbuds": ["headphones", "buds", "earphones"],
  "earphones": ["headphones", "earbuds", "buds"],
  "buds": ["earbuds", "headphones"],
  "headset": ["headphones", "earbuds"],
  "speaker": ["audio", "sound"],
}

def search_catalog(query: str, limit: int = 3, ceilingPaise: Optional[int] = None, minScore: int = 1) -> List[Product]:
    q = query.lower().strip()
    if not q:
        return []
    
    tokens = list(set([t for t in re.split(r'[^a-z0-9]+', q) if len(t) > 1]))
    
    scored = []
    for p in CATALOG:
        name = p.name.lower()
        haystack = f"{name} {p.tagline} {p.category} {' '.join(p.tags)}".lower()
        score = 0
        for t in tokens:
            if t in haystack:
                score += 2
            if t in name:
                score += 3
            for tag in p.tags:
                if tag == t:
                    score += 2
            for s in SYNONYMS.get(t, []):
                if s in haystack:
                    score += 1
        scored.append({"p": p, "score": score})
        
    scored = [s for s in scored if s["score"] >= minScore]
    
    # Sort descending by score, then ascending by price if ceiling is set, then ascending by id
    def sort_key(s):
        return (
            -s["score"],
            s["p"].pricePaise if ceilingPaise is not None else 0,
            s["p"].id
        )
        
    scored.sort(key=sort_key)
    
    if ceilingPaise is None:
        return [s["p"] for s in scored[:limit]]
        
    affordable = [s for s in scored if s["p"].pricePaise <= ceilingPaise]
    if affordable:
        return [s["p"] for s in affordable[:limit]]
        
    category = scored[0]["p"].category if scored else None
    if category:
        fallback = [p for p in CATALOG if p.category == category and p.pricePaise <= ceilingPaise]
        fallback.sort(key=lambda p: (p.pricePaise, p.id))
        return fallback[:limit]
        
    return []

def parse_price_ceiling(text: str) -> Optional[int]:
    # Parse "under ₹3,000" / "below 3k" / "max 3000" → paise; null when absent.
    pattern1 = r"(?:under|below|less than|max|upto|up to|≤)\s*[₹\s]*([\d,]+(?:\.\d+)?)\s*(k)?"
    pattern2 = r"[₹\s]([\d,]+(?:\.\d+)?)\s*(k)?\s*(?:or less|max|budget)"
    
    m1 = re.search(pattern1, text, re.IGNORECASE)
    m2 = re.search(pattern2, text, re.IGNORECASE) if not m1 else None
    
    m = m1 or m2
    if not m:
        return None
        
    base_str = m.group(1).replace(",", "")
    try:
        base = float(base_str)
    except ValueError:
        return None
        
    if base <= 0:
        return None
        
    is_k = bool(m.group(2))
    paise = base * 1000 * 100 if is_k else base * 100
    return int(round(paise))
