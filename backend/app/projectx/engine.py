import uuid
import json
from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel

from .ledger import Ledger, TraceSpan
from .mandate import build_mandate_body, sign_mandate, IssueMandateInput
from .decide import decide_order, OrderRequest, OrderRequestItem
from .types import Mandate, TrustTier, GateDecision, TRUST_TIERS
from .catalog import CATALOG, catalog_snapshot, Product, CatalogSnapshot
from .payments import simulated_capture, simulated_order, PaymentCapture, rail_info

import sys
import os
# Add parent dir to path so we can import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.smart_cart import smart_cart_engine, CartItem
from core.split_settlement import split_settlement_engine
from core.vulcan import vulcan_engine

class EngineDeps:
    def __init__(self, ledger: Ledger, private_key_pem: str, public_key_pem: str, merchant_fingerprint: str):
        self.ledger = ledger
        self.private_key_pem = private_key_pem
        self.public_key_pem = public_key_pem
        self.merchant_fingerprint = merchant_fingerprint

class TxInput(BaseModel):
    buyerId: str
    tier: TrustTier
    items: List[OrderRequestItem]
    mandateItems: Optional[List[OrderRequestItem]] = None
    adapter: str
    nowMs: int
    priceOverrides: Optional[Dict[str, int]] = None
    forge: Optional[Callable[[Mandate], Mandate]] = None
    expired: Optional[bool] = None
    humanApproved: Optional[bool] = None
    orderId: Optional[str] = None
    amountCapPaise: Optional[int] = None
    buyerPrefix: Optional[str] = None

class TxOutcome(BaseModel):
    orderId: str
    traceId: str
    mandate: Mandate
    decision: GateDecision
    payment: Optional[PaymentCapture]
    railOrderId: Optional[str]

_span_counter = 0

def new_span(
    deps: EngineDeps,
    trace_id: str,
    order_id: str,
    name: str,
    ms: int,
    adapter: str,
    attrs: Optional[Dict[str, Any]] = None,
    parent_span_id: Optional[str] = None,
    at_ms: Optional[int] = None
) -> TraceSpan:
    global _span_counter
    _span_counter += 1
    span_id = f"sp_{_span_counter:04x}" # using hex as base36 rough equivalent
    
    final_attrs = {"startSeq": len(deps.ledger.all()) + 1}
    if attrs:
        final_attrs.update(attrs)
        
    span = TraceSpan(
        traceId=trace_id,
        orderId=order_id,
        spanId=span_id,
        parentSpanId=parent_span_id,
        name=name,
        ms=ms,
        adapter=adapter,
        attrs=final_attrs
    )
    
    import time
    ts = at_ms if at_ms is not None else int(time.time() * 1000)
    deps.ledger.append_at("span", span.model_dump(), ts)
    return span

def _snapshot_with_drift(deps: EngineDeps, overrides: Optional[Dict[str, int]] = None) -> CatalogSnapshot:
    if not overrides:
        return catalog_snapshot(deps.public_key_pem, deps.merchant_fingerprint)
        
    all_products = []
    for p in CATALOG:
        if p.id in overrides:
            d = p.model_dump()
            d["pricePaise"] = overrides[p.id]
            all_products.append(Product(**d))
        else:
            all_products.append(p)
            
    return CatalogSnapshot(
        all=all_products,
        byId={p.id: p for p in all_products},
        merchantPublicKeyPem=deps.public_key_pem,
        merchantFingerprint=deps.merchant_fingerprint
    )

def run_transaction(deps: EngineDeps, input_data: TxInput) -> TxOutcome:
    order_id = input_data.orderId or f"ord_{uuid.uuid4().hex[:10]}"
    trace_id = f"tr_{order_id}"
    t0 = input_data.nowMs
    
    new_span(deps, trace_id, order_id, "agent.session", 0, input_data.adapter, {"buyerId": input_data.buyerId}, None, t0)
    
    # 1. mandate request
    catalog0 = _snapshot_with_drift(deps)
    mandate_items_req = input_data.mandateItems if input_data.mandateItems is not None else input_data.items
    mandate_items = []
    
    from .types import MandateItem
    for it in mandate_items_req:
        p = catalog0.byId.get(it.productId)
        if not p:
            raise ValueError(f"unknown product {it.productId}")
        mandate_items.append(MandateItem(
            productId=it.productId,
            quantity=it.quantity,
            unitPricePaise=p.pricePaise
        ))
        
    cart_total = sum(it.unitPricePaise * it.quantity for it in mandate_items)
    
    tier_cap = TRUST_TIERS[input_data.tier]["maxAmountPaise"]
    amount_cap = input_data.amountCapPaise if input_data.amountCapPaise is not None else min(cart_total, tier_cap)
    
    mandate_body = build_mandate_body(
        IssueMandateInput(
            buyerId=input_data.buyerId,
            tier=input_data.tier,
            items=mandate_items,
            nowMs=t0,
            humanApproved=input_data.humanApproved or False,
            amountCapPaise=amount_cap,
            ttlMs=-60_000 if input_data.expired else None
        ),
        f"man_{uuid.uuid4().hex[:8]}"
    )
    
    mandate = sign_mandate(mandate_body, deps.private_key_pem)
    if input_data.forge:
        mandate = input_data.forge(mandate)
        
    new_span(deps, trace_id, order_id, "mandate.request", 1, input_data.adapter, {"tier": input_data.tier, "capPaise": mandate.amountCapPaise}, None, t0 + 1)
    
    deps.ledger.append_at("mandate.issued", {
        "mandateId": mandate.id, "buyerId": input_data.buyerId, "tier": mandate.tier,
        "amountCapPaise": mandate.amountCapPaise, "orderId": order_id, "traceId": trace_id
    }, t0 + 2)
    
    # 2. order proposal
    lines = []
    for it in input_data.items:
        p = catalog0.byId.get(it.productId)
        lines.append({
            "productId": it.productId,
            "name": p.name if p else "Unknown",
            "quantity": it.quantity,
            "unitPricePaise": p.pricePaise if p else 0
        })
        
    claimed_total = sum(l["unitPricePaise"] * l["quantity"] for l in lines)
    
    deps.ledger.append_at("order.proposed", {
        "orderId": order_id, "buyerId": input_data.buyerId, "tier": input_data.tier,
        "adapter": input_data.adapter, "items": lines, "totalPaise": claimed_total,
        "traceId": trace_id, "claimedTotalPaise": claimed_total
    }, t0 + 3)
    
    # 3. bind
    catalog = _snapshot_with_drift(deps, input_data.priceOverrides)
    order = OrderRequest(orderId=order_id, items=input_data.items, claimedTotalPaise=claimed_total)
    decision = decide_order(mandate, order, catalog, t0 + 5)
    
    turn_tokens_in = len(json.dumps({"items": [i.model_dump() for i in input_data.items], "tier": input_data.tier})) // 4
    turn_tokens_out = len(json.dumps([c.model_dump(by_alias=True) for c in decision.checks])) // 4
    
    new_span(deps, trace_id, order_id, "gate.decide", (decision.decidedAtMs - t0) or 2, input_data.adapter, {
        "kind": decision.kind, "code": decision.code or "ok", "tokensIn": turn_tokens_in, "tokensOut": turn_tokens_out
    }, None, t0 + 5)
    
    deps.ledger.append_at("gate.decision", {
        "orderId": order_id, "buyerId": input_data.buyerId, "kind": decision.kind,
        "code": decision.code, "reason": decision.reason, "totalPaise": decision.totalPaise,
        "checks": len(decision.checks), "traceId": trace_id
    }, t0 + 6)
    
    if decision.kind == "REFUSE":
        deps.ledger.append_at("order.refused", {
            "orderId": order_id, "code": decision.code, "reason": decision.reason, "traceId": trace_id
        }, t0 + 7)
        return TxOutcome(orderId=order_id, traceId=trace_id, mandate=mandate, decision=decision, payment=None, railOrderId=None)
        
    if decision.kind == "HOLD_FOR_APPROVAL":
        deps.ledger.append_at("approval.requested", {
            "orderId": order_id, "amountPaise": decision.totalPaise, "reason": "over ₹10,000 without human approval", "traceId": trace_id
        }, t0 + 7)
        return TxOutcome(orderId=order_id, traceId=trace_id, mandate=mandate, decision=decision, payment=None, railOrderId=None)
        
    # 4. smart cart & split settlement
    cart_items_for_smart_cart = []
    for it in input_data.items:
        p = catalog.byId.get(it.productId)
        if p:
            cart_items_for_smart_cart.append(CartItem(
                id=f"item_{p.id}",
                product_id=p.id,
                product_name=p.name,
                category=p.category,
                merchant_id="merchant_novatech", # Default for demo
                merchant_name="NovaTech Gear",
                price_inr=p.pricePaise / 100,
                shipping_cost_inr=0.0,
                quantity=it.quantity
            ))
            
    if cart_items_for_smart_cart:
        smart_cart_res = smart_cart_engine.evaluate_smart_cart(cart_items_for_smart_cart)
        deps.ledger.append_at("cart.optimized", smart_cart_res.model_dump(), t0 + 7)
        
        # Route Split plan
        primary = cart_items_for_smart_cart[0].model_dump()
        accessory = cart_items_for_smart_cart[1].model_dump() if len(cart_items_for_smart_cart) > 1 else None
        split_plan = split_settlement_engine.plan_split_transfer(primary, accessory)
        deps.ledger.append_at("settlement.split_planned", split_plan, t0 + 8)
        
    # Vulcan Payment Routing Telemetry
    vulcan_analysis = vulcan_engine.evaluate_transaction_telemetry(
        order_id=order_id,
        amount_inr=decision.totalPaise / 100,
        merchant_name="NovaTech Gear",
        category="Electronics"
    )
    deps.ledger.append_at("vulcan.telemetry_evaluated", vulcan_analysis.__dict__, t0 + 9)

    # 5. pay
    payment = simulated_capture(decision.totalPaise)
    rail = rail_info()
    rail_order = simulated_order(decision.totalPaise, order_id)
    
    new_span(deps, trace_id, order_id, "payment.create", 3, input_data.adapter, {"rail": payment.rail}, None, t0 + 10)
    
    deps.ledger.append_at("payment.captured", {
        "orderId": order_id, "rail": payment.rail, "simulated": payment.simulated,
        "paymentId": payment.paymentId, "confirmId": payment.confirmId, "totalPaise": decision.totalPaise,
        "railOrderId": rail_order.railOrderId, "railLabel": rail.label, "traceId": trace_id
    }, t0 + 11)
    
    return TxOutcome(orderId=order_id, traceId=trace_id, mandate=mandate, decision=decision, payment=payment, railOrderId=rail_order.railOrderId)

def confirm_payment_once(deps: EngineDeps, order_id: str, confirm_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    for e in deps.ledger.all():
        if e.type in ["payment.captured", "payment.confirmed"]:
            d = e.data if isinstance(e.data, dict) else {}
            if d.get("confirmId") == confirm_id:
                deps.ledger.append("replay.detected", {"orderId": order_id, "confirmId": confirm_id, "code": "REPLAY_DETECTED"})
                return {"ok": False, "code": "REPLAY_DETECTED"}
                
    event_data = {"orderId": order_id, "confirmId": confirm_id}
    event_data.update(payload)
    deps.ledger.append("payment.confirmed", event_data)
    return {"ok": True}
