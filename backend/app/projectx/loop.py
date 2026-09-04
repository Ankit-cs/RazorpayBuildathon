import time
import uuid
import json
import hmac
import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from .runtime import ProjectXRuntime, BuyerSession
from .nlu import parse_intent
from .adapters import adapter_call, ADAPTERS, AdapterContext
from .llm import get_llm_brain, brain_mode, get_chat_voice
from .catalog import search_catalog, parse_price_ceiling
from .types import TRUST_TIERS
from .mandate import build_mandate_body, sign_mandate, IssueMandateInput
from .engine import run_transaction, new_span, TxInput
from .payments import rail_info

import sys
import os
# Add parent dir to path so we can import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.popi import popi_engine
from core.rag_engine import rag_engine
from core.security_guard import security_guard

class ChatEvent(BaseModel):
    id: str
    ts: int
    role: Optional[str] = None
    text: Optional[str] = None
    kind: Optional[str] = None
    tool: Optional[str] = None
    adapter: Optional[str] = None
    summary: Optional[str] = None
    detail: Optional[str] = None
    ms: Optional[int] = None
    products: Optional[List[Any]] = None
    note: Optional[str] = None
    lines: Optional[List[Any]] = None
    totalPaise: Optional[int] = None
    mandate: Optional[Dict[str, Any]] = None
    pendingApproval: Optional[bool] = None
    orderId: Optional[str] = None
    decision: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    rail: Optional[str] = None
    simulated: Optional[bool] = None
    manifestNo: Optional[str] = None
    attackId: Optional[str] = None
    label: Optional[str] = None
    verdict: Optional[str] = None
    code: Optional[str] = None
    checks: Optional[List[Any]] = None
    tier: Optional[str] = None

class TurnResult(BaseModel):
    events: List[ChatEvent]
    session: BuyerSession
    needCheckoutRefresh: bool
    suggestions: List[Dict[str, str]]

_event_counter = 0

def eid() -> str:
    global _event_counter
    _event_counter += 1
    return f"ev_{_event_counter:04x}"

def new_session(rt: ProjectXRuntime, tier: str = "UNVERIFIED") -> BuyerSession:
    session_id = f"ses_{uuid.uuid4().hex[:8]}"
    session = BuyerSession(
        sessionId=session_id,
        buyerId=f"buyer-{session_id[-6:]}",
        tier=tier,
        cart={},
        mandate=None,
        awaitingMandateApproval=False,
        lastOrderId=None,
        createdAtMs=int(time.time() * 1000)
    )
    rt.sessions[session_id] = session
    rt.ledger.append("session.opened", {"sessionId": session_id, "buyerId": session.buyerId, "tier": tier, "adapter": None})
    return session

def rupees(paise: int) -> str:
    return f"₹{paise / 100:,.2f}"

def suggestions_for(lines: List[Dict[str, Any]], tier: str, awaiting_approval: bool, found: Optional[Dict[str, str]] = None) -> List[Dict[str, str]]:
    if awaiting_approval and lines:
        return [{"label": "Approve", "value": "approve"}]
    if lines:
        total = sum(l["unitPricePaise"] * l["quantity"] for l in lines)
        if total > TRUST_TIERS[tier]["maxAmountPaise"]:
            return [{"label": "Raise limit", "value": "attest"}]
        return [{"label": "Checkout", "value": "checkout"}]
    if found:
        return [{"label": f"Add {found['name']}", "value": f"add {found['id']}"}]
    return [{"label": "Keep browsing", "value": "search audio"}]

def cart_lines(rt: ProjectXRuntime, session: BuyerSession) -> List[Dict[str, Any]]:
    return [
        {"productId": pid, "name": rt.catalog.byId[pid].name, "quantity": qty, "unitPricePaise": rt.catalog.byId[pid].pricePaise}
        for pid, qty in session.cart.items()
    ]

def llm_to_intent(parsed: Dict[str, Any], raw: str) -> Dict[str, Any]:
    action = parsed.get("action")
    if action == "search":
        q = parsed.get("query") or raw
        max_p = int(parsed["maxPriceInr"] * 100) if parsed.get("maxPriceInr") else parse_price_ceiling(raw)
        return {"kind": "search", "query": q, "maxPricePaise": max_p, "results": search_catalog(q, limit=3)}
    if action == "add":
        return {"kind": "add", "productId": parsed.get("productId"), "query": parsed.get("query") or raw, "quantity": parsed.get("quantity") or 1}
    if action == "remove":
        return {"kind": "remove", "productId": parsed.get("productId") or ""}
    if action in ["cart", "checkout", "confirm", "status"]:
        return {"kind": action}
    return {"kind": "unknown", "query": raw}

async def agent_turn(rt: ProjectXRuntime, session_id: str, message: str, adapter: str, sessionless: bool = False) -> TurnResult:
    events = []
    def say(text: str):
        events.append(ChatEvent(id=eid(), ts=now(), role="agent", text=text))
        
    first_match = None
    session = rt.sessions.get(session_id)
    if not session:
        if sessionless:
            session = BuyerSession(sessionId="ses_adhoc", buyerId="buyer-adhoc", tier="UNVERIFIED", cart={}, mandate=None, awaitingMandateApproval=False, lastOrderId=None, createdAtMs=int(time.time() * 1000))
        else:
            session = new_session(rt)
            
    now = lambda: int(time.time() * 1000)
    
    events.append(ChatEvent(id=eid(), ts=now(), role="user", text=message))
    
    is_safe, sanitized, alert_reason = security_guard.sanitize_and_check_prompt(message)
    if not is_safe:
        say(f"Security Alert: {alert_reason}. Request blocked.")
        return TurnResult(events=events, session=session, needCheckoutRefresh=False, suggestions=[])
    
    intent = parse_intent(sanitized)
    tokens_in = 0
    tokens_out = 0
    
    llm = get_llm_brain() if brain_mode() == "llm" else None
    voice = get_chat_voice()
    
    async def speak_through_voice(msg: str, fallback: str):
        if not voice:
            say(fallback)
            return
        t0 = time.time()
        res = await voice.chat(msg)
        ms = int((time.time() - t0) * 1000)
        new_span(rt.deps, f"tr_ses_{session.sessionId}", session.lastOrderId or "none", "llm.chat", ms, adapter, {
            "tokensIn": res["usage"]["tokensIn"], "tokensOut": res["usage"]["tokensOut"], "model": res["model"]
        })
        say(res["reply"] or fallback)

    if llm:
        t0 = time.time()
        res = await llm.parse_intent(message)
        ms = int((time.time() - t0) * 1000)
        parsed = res.get("intent")
        usage = res.get("usage")
        tokens_in = usage["tokensIn"]
        tokens_out = usage["tokensOut"]
        if parsed:
            intent = llm_to_intent(parsed.model_dump(), sanitized)
        new_span(rt.deps, f"tr_ses_{session.sessionId}", session.lastOrderId or "none", "llm.parseIntent", ms, adapter, {
            "tokensIn": tokens_in, "tokensOut": tokens_out, "model": llm.name
        })

    tool_log = []
    
    async def call_tool(name: str, args: Dict[str, Any]) -> Any:
        t0 = time.time()
        val = await execute_tool(rt, session, name, args, events, say, adapter)
        ms = max(1, int((time.time() - t0) * 1000))
        est = (len(json.dumps({"name": name, "args": args})) // 4) + (len(json.dumps(val or "")) // 4)
        new_span(rt.deps, f"tr_ses_{session.sessionId}", session.lastOrderId or "none", f"tool:{name}", ms, adapter, {
            "tokensIn": 0 if tokens_in > 0 else (len(json.dumps(args)) // 4),
            "tokensOut": tokens_out if tokens_in > 0 else est
        })
        return val
        
    def sign_ctx(payload: str) -> str:
        return hmac.new(rt.keys.fingerprint.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        
    async def run_tool(name: str, args: Dict[str, Any], summary: str):
        t0 = time.time()
        res = await adapter_call(adapter, name, args, AdapterContext(callTool=call_tool, sign=sign_ctx, sessionId=session.sessionId))
        ms = max(1, int((time.time() - t0) * 1000))
        detail = "\n".join([f"{'→' if w.dir == 'out' else '←'} {w.method or ''} {w.body[:220]}" for w in res.wire])
        tool_log.append({"name": name, "ms": ms, "wire": [{"dir": w.dir, "bytes": w.bytes, "body": w.body} for w in res.wire]})
        events.append(ChatEvent(id=eid(), ts=now(), kind="step", tool=name, adapter=adapter, summary=f"{summary} · {ADAPTERS[adapter]['label']}", detail=detail, ms=ms))
        return res.value

    kind = intent["kind"]
    if kind == "greeting":
        await speak_through_voice(message, f"_projectX desk, open. I'm your buying agent for Fieldnote Supply — {len(rt.catalog.byId)} items in the catalog. Tell me what you need (\"noise cancelling headphones under ₹5,000\") and I'll search, build a cart, and ask the desk for a bounded mandate. Your trust tier is **{TRUST_TIERS[session.tier]['label']}** ({TRUST_TIERS[session.tier]['blurb']}).")
    elif kind == "help":
        say("I can: **search** (\" ANC headphones under 3k\"), **add** (\"add the ridge mouse\"), **cart**, **checkout** (requests a signed mandate and pays within its bounds), **status**. The desk can also red-team itself: type \"attack: overspend-tier\" or use the Red Team panel. Escalation: type \"attest\" to raise your trust tier.")
    elif kind == "status":
        lines = cart_lines(rt, session)
        cart_str = ", ".join([f"{l['name']} ×{l['quantity']}" for l in lines]) if lines else "empty"
        mandate_str = f"Mandate {session.mandate['id']} active." if session.mandate else "No active mandate."
        say(f"Passport: **{TRUST_TIERS[session.tier]['label']}** — cap {rupees(TRUST_TIERS[session.tier]['maxAmountPaise'])} per transaction, {TRUST_TIERS[session.tier]['maxItems']} item(s). Cart: {cart_str}. {mandate_str}")
    elif kind == "attest":
        if session.tier == "MANDATED":
            say(f"You already hold the highest tier — {TRUST_TIERS['MANDATED']['blurb']}")
        else:
            next_tier = "ATTESTED" if session.tier == "UNVERIFIED" else "MANDATED"
            session.tier = next_tier
            rt.ledger.append("tier.raised", {"sessionId": session.sessionId, "buyerId": session.buyerId, "to": next_tier, "via": "attest (OTP-bound in production)"})
            t = TRUST_TIERS[next_tier]
            events.append(ChatEvent(id=eid(), ts=now(), kind="tier", tier=next_tier, note=f"{rupees(t['maxAmountPaise'])} cap · {t['maxItems']} item(s) · {t['mandateTtlMs'] // 60000} min"))
            say("You're verified." if next_tier == "ATTESTED" else "Standing mandate — the highest limits.")
    elif kind == "search":
        res = await run_tool("search_catalog", {"query": intent["query"], "maxPricePaise": intent["maxPricePaise"]}, "Searched the catalog")
        if isinstance(res, list) and len(res) > 0:
            first_match = {"id": res[0]["id"], "name": res[0]["name"]}
    elif kind == "add":
        if not intent.get("productId"):
            say(f"I couldn't find \"{intent['query']}\" in the catalog. Try \"search <what you need>\" first.")
        else:
            await run_tool("add_to_cart", {"productId": intent["productId"], "quantity": intent["quantity"]}, "Added to cart")
    elif kind == "remove":
        pid = intent["productId"]
        if pid in session.cart:
            del session.cart[pid]
        lines = cart_lines(rt, session)
        events.append(ChatEvent(id=eid(), ts=now(), kind="cart", lines=lines, totalPaise=sum(l["unitPricePaise"] * l["quantity"] for l in lines)))
        say(f"Removed. The cart now holds {len(lines)} line(s).")
    elif kind == "cart":
        lines = cart_lines(rt, session)
        events.append(ChatEvent(id=eid(), ts=now(), kind="cart", lines=lines, totalPaise=sum(l["unitPricePaise"] * l["quantity"] for l in lines)))
        say("That's the cart." if lines else "The cart is empty — search for something first.")
    elif kind == "checkout":
        lines = cart_lines(rt, session)
        if not lines:
            say("Nothing to check out yet. Search and add something first.")
        elif sum(l["unitPricePaise"] * l["quantity"] for l in lines) > TRUST_TIERS[session.tier]["maxAmountPaise"]:
            say("That's over your current limit.")
        else:
            await run_tool("request_mandate", {}, "Requested a mandate from the desk")
    elif kind == "confirm":
        if session.awaitingMandateApproval and len(session.cart) > 0:
            session.awaitingMandateApproval = False
            await run_tool("bind_and_pay", {}, "Bound the order and paid")
        else:
            say("Nothing is waiting on your approval right now.")
    elif kind == "attack":
        say(f"Attack {intent['attackId']} requested.")
    else:
        await speak_through_voice(message, "I didn't catch that.")
        
    return TurnResult(
        events=events,
        session=session,
        needCheckoutRefresh=any(t["name"] in ["bind_and_pay", "request_mandate"] for t in tool_log),
        suggestions=suggestions_for(cart_lines(rt, session), session.tier, session.awaitingMandateApproval, first_match)
    )

async def execute_tool(rt: ProjectXRuntime, session: BuyerSession, name: str, args: Dict[str, Any], events: List[ChatEvent], say: callable, adapter: str) -> Any:
    if name == "search_catalog":
        query = args.get("query", "")
        ceiling = args.get("maxPricePaise") or args.get("ceilingPaise")
        if ceiling is None:
            ceiling = parse_price_ceiling(query)
        res = search_catalog(query, 3, ceilingPaise=ceiling)
        
        # Augment with RAG Knowledge
        rag_res = rag_engine.retrieve_context(query, top_k=1)
        rag_note = f" (Knowledge: {rag_res[0].document.title})" if rag_res else ""

        note = f"budget <= {rupees(ceiling)}{rag_note}" if ceiling else f"Knowledge: {rag_note}"
        events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="products", products=[p.model_dump() for p in res], note=note))
        if len(res) == 1:
            say("One match.")
        elif len(res) > 1:
            say(f"{len(res)} matches.")
        else:
            say("Nothing matched — try a broader search.")
        return [{"id": p.id, "name": p.name, "pricePaise": p.pricePaise, "stock": p.stock} for p in res]
        
    elif name == "get_product":
        p = rt.catalog.byId.get(args.get("productId"))
        return {"id": p.id, "name": p.name, "pricePaise": p.pricePaise, "stock": p.stock} if p else None
        
    elif name == "add_to_cart":
        p = rt.catalog.byId.get(args.get("productId"))
        if not p:
            return {"added": False, "reason": "unknown product"}
        qty = max(1, min(10, int(args.get("quantity", 1))))
        session.cart[p.id] = session.cart.get(p.id, 0) + qty
        lines = cart_lines(rt, session)
        total = sum(l["unitPricePaise"] * l["quantity"] for l in lines)
        events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="cart", lines=lines, totalPaise=total))
        say("Added.")
        return {"added": True, "cartLines": len(lines), "totalPaise": total}
        
    elif name == "request_mandate":
        lines = cart_lines(rt, session)
        total = sum(l["unitPricePaise"] * l["quantity"] for l in lines)
        from .types import MandateItem
        m_items = [MandateItem(productId=l["productId"], quantity=l["quantity"], unitPricePaise=l["unitPricePaise"]) for l in lines]
        body = build_mandate_body(IssueMandateInput(
            buyerId=session.buyerId, tier=session.tier, items=m_items, nowMs=int(time.time() * 1000), humanApproved=False, amountCapPaise=total
        ), f"man_{uuid.uuid4().hex[:8]}")
        mandate = sign_mandate(body, rt.deps.private_key_pem)
        session.mandate = {"id": mandate.id, "amountCapPaise": mandate.amountCapPaise, "expiresAtMs": mandate.expiresAtMs}
        session.awaitingMandateApproval = True
        rt.ledger.append("mandate.issued", {
            "mandateId": mandate.id, "buyerId": session.buyerId, "tier": mandate.tier, "amountCapPaise": mandate.amountCapPaise, "liveSession": session.sessionId
        })
        view = {
            "id": mandate.id, "tier": mandate.tier, "amountCapPaise": mandate.amountCapPaise, "items": lines,
            "expiresAtMs": mandate.expiresAtMs, "humanApproved": False, "fingerprint": rt.keys.fingerprint, "signature": mandate.signature[:24] + "…"
        }
        events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="mandate", mandate=view, pendingApproval=True))
        over10k = total >= 1_000_000
        say(f"The desk approved your mandate — it holds for {round((mandate.expiresAtMs - int(time.time() * 1000)) / 60000)} minutes." + (" It's above ₹10,000, so the merchant desk signs off too." if over10k else ""))
        return {"mandateId": mandate.id, "cap": mandate.amountCapPaise, "expiresAtMs": mandate.expiresAtMs}
        
    elif name == "bind_and_pay":
        lines = cart_lines(rt, session)
        if not lines or not session.mandate:
            return {"bound": False, "reason": "no pending mandate"}
        
        from .decide import OrderRequestItem
        o_items = [OrderRequestItem(productId=l["productId"], quantity=l["quantity"]) for l in lines]
        tx = run_transaction(rt.deps, TxInput(
            buyerId=session.buyerId, tier=session.tier, items=o_items, adapter=adapter, nowMs=int(time.time() * 1000)
        ))
        session.lastOrderId = tx.orderId
        events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="gate", orderId=tx.orderId, decision=tx.decision.model_dump(), adapter=adapter))
        
        if tx.decision.kind == "ALLOW" and tx.payment:
            rail = rail_info()
            events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="payment", orderId=tx.orderId, totalPaise=tx.decision.totalPaise, status="captured", rail=rail.id, simulated=rail.simulated))
            manifest_no = f"FN-MA-{str(len(rt.ledger.all())).zfill(6)}"
            events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="receipt", orderId=tx.orderId, manifestNo=manifest_no, lines=lines, totalPaise=tx.decision.totalPaise, rail=rail.id, simulated=rail.simulated))
            say("Paid." + (" (simulated)" if rail.simulated else ""))
            session.cart.clear()
            session.mandate = None
            return {"bound": True, "captured": True, "orderId": tx.orderId, "manifestNo": manifest_no}
            
        if tx.decision.kind == "HOLD_FOR_APPROVAL":
            events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="payment", orderId=tx.orderId, totalPaise=tx.decision.totalPaise, status="held", rail="none", simulated=False))
            say("Above ₹10,000 — the merchant desk holds it. Approve it in the Control Room.")
            return {"bound": True, "held": True, "orderId": tx.orderId}
            
        events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="payment", orderId=tx.orderId, totalPaise=0, status="refused", rail="none", simulated=False))
        say("The gate said no — the card above shows why.")
        return {"bound": False, "refused": True, "code": tx.decision.code, "orderId": tx.orderId}
        
    elif name == "validate_policy":
        # PoPI check
        budget_limit_inr = args.get("budget_limit_inr", 0.0)
        max_shipping_inr = args.get("max_shipping_inr", 0.0)
        popi = popi_engine.generate_policy_commitment(
            order_ref=f"ord_{uuid.uuid4().hex[:8]}",
            budget_limit_inr=budget_limit_inr,
            max_shipping_inr=max_shipping_inr,
            allowed_categories=[]
        )
        events.append(ChatEvent(id=eid(), ts=int(time.time() * 1000), kind="popi", note=f"PoPI Token Generated: {popi.popi_token}"))
        return {"popi_token": popi.popi_token, "budget_commitment_paise": popi.budget_commitment_paise}
        
    elif name == "negotiate_offer":
        item = args.get("item_name", "item")
        target_inr = args.get("target_price_inr", 0)
        say(f"Negotiating A2A price for {item} (target: {rupees(target_inr * 100)})...")
        # Simulate A2A concession
        concession_inr = target_inr * 1.05 # 5% above target
        return {"concession_price_inr": concession_inr, "status": "agreement_reached"}

    return {"error": f"unknown tool {name}"}
