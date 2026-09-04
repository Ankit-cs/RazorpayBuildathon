import re
from typing import List, Optional, Dict, Any

from .catalog import parse_price_ceiling, search_catalog, Product

def quantity_of(text: str) -> int:
    m = re.search(r'(?:x|qty|quantity)?\s*(\d{1,2})\s*(?:x|qty|pcs|pieces|units)?\b', text, re.IGNORECASE)
    if not m:
        return 1
    n = int(m.group(1))
    return n if 1 <= n <= 10 else 1

def parse_intent(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    lower = text.lower()
    
    if not text:
        return {"kind": "unknown", "query": ""}
        
    atk = re.search(r'^attack[:\s]+([a-z0-9-]+)', lower, re.IGNORECASE)
    if atk:
        return {"kind": "attack", "attackId": atk.group(1)}
        
    greeting_p1 = r'^(whats up|what\'s up|wassup|sup|how are you|how are things|how is it going|thanks|thank you|thx|ty|who are you|what are you|good (night|day))\b'
    greeting_p2 = r'^(hi|hello|hey|namaste|yo|good (morning|evening|afternoon))\b'
    if re.search(greeting_p1, lower) or re.search(greeting_p2, lower):
        return {"kind": "greeting"}
        
    if re.search(r'^(help|what can you do|commands|how does this work)', lower):
        return {"kind": "help"}
        
    if re.search(r'\b(attest\w*|verify me|otp|upgrade (my )?(tier|identity))\b', lower):
        return {"kind": "attest"}
        
    if re.search(r'\b(status|balance|mandate status|my tier|who am i)\b', lower):
        return {"kind": "status"}
        
    if re.search(r'\b(checkout|pay now|buy now|place the order|complete (the )?purchase|bind and pay)\b', lower):
        return {"kind": "checkout"}
        
    if re.search(r'^(yes|y|confirm|go ahead|do it|approve|proceed|continue)\b', lower):
        return {"kind": "confirm"}
        
    remove = re.search(r'(?:remove|drop|delete|take out)\s+(?:the\s+)?([a-z0-9-]+)', lower)
    if remove:
        tok = remove.group(1)
        hits = search_catalog(tok, limit=1)
        return {"kind": "remove", "productId": hits[0].id if hits else tok}
        
    add = re.search(r'(?:add|buy|get|i(?:\'| a)?ll take|i want|i need|order|put in)\s+(.+?)(?:\s+to\s+cart)?$', lower)
    if add:
        rest = add.group(1)
        qty = quantity_of(rest)
        
        id_hits_candidates = re.findall(r'[a-z]+(?:-[a-z0-9]+){1,3}', rest)
        id_hit = None
        for t in id_hits_candidates:
            if any(p.id == t for p in search_catalog(t, limit=1)):
                id_hit = t
                break
                
        if id_hit:
            return {"kind": "add", "productId": id_hit, "query": rest, "quantity": qty}
            
        hits = search_catalog(rest, limit=1)
        return {"kind": "add", "productId": hits[0].id if hits else None, "query": rest, "quantity": qty}
        
    if re.search(r'\b(cart|basket|what am i buying|my items)\b', lower):
        return {"kind": "cart"}
        
    if re.search(r'\b(search|find|show|look(?:ing)? for|browse|list|what.*do you have|any)\b', lower) or parse_price_ceiling(lower) is not None:
        query = re.sub(r'\b(under|below|less than|max|upto|up to)\s*[₹\s]*[\d,.]+k?', '', text, flags=re.IGNORECASE)
        query = re.sub(r'\b(search|find|show|me|for|looking|browse|list|do you have|any|some|good)\b', '', query, flags=re.IGNORECASE)
        query = query.replace("₹", "").strip()
        
        max_price_paise = parse_price_ceiling(lower)
        results = search_catalog(query or lower, limit=3)
        return {"kind": "search", "query": query or text, "maxPricePaise": max_price_paise, "results": results}
        
    results = search_catalog(lower, limit=3, minScore=3)
    if results:
        return {"kind": "search", "query": text, "maxPricePaise": parse_price_ceiling(lower), "results": results}
        
    return {"kind": "unknown", "query": text}
