from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from .types import Mandate, GateDecision, GateCheck, RefusalReason, REFUSAL_REASONS, HUMAN_APPROVAL_THRESHOLD_PAISE, TRUST_TIERS
from .canonical import canonical_json, CanonicalError
from .mandate import verify_mandate_signature
from .catalog import CatalogSnapshot

class OrderRequestItem(BaseModel):
    productId: str
    quantity: int

class OrderRequest(BaseModel):
    orderId: str
    items: List[OrderRequestItem]
    claimedTotalPaise: Optional[int] = None

def rupees(paise: int) -> str:
    # formatted like ₹10,000
    formatted = f"{paise / 100:,.0f}"
    return f"₹{formatted}"

def decide_order(
    mandate: Mandate,
    order: OrderRequest,
    catalog: CatalogSnapshot,
    now_ms: int
) -> GateDecision:
    checks: List[GateCheck] = []
    
    def fail(code: str, extra: Optional[str] = None) -> GateDecision:
        reason = REFUSAL_REASONS.get(code, "Unknown reason")
        if extra:
            reason += f" ({extra})"
        return GateDecision(
            kind="REFUSE",
            code=code,
            reason=reason,
            checks=checks,
            decidedAtMs=now_ms,
            totalPaise=0
        )
        
    def push(id: str, label: str, pass_: Optional[bool], detail: str):
        checks.append(GateCheck(id=id, label=label, pass_=pass_, detail=detail))

    # 1. canonical shape
    try:
        mandate_dict = mandate.model_dump(exclude_unset=True)
        mandate_dict.pop("signature", None)
        canonical_json(mandate_dict)
        push("parse", "mandate parses canonically", True, "sorted keys, integers only")
    except Exception as err:
        if isinstance(err, CanonicalError):
            return fail("MALFORMED_MANDATE", str(err))
        raise err

    # 2. currency
    if mandate.currency != "INR":
        push("currency", "mandate currency is INR", False, f"got {mandate.currency}")
        return fail("CURRENCY_UNSUPPORTED")
    push("currency", "mandate currency is INR", True, "INR")

    # 3. signature
    sig_ok = verify_mandate_signature(mandate, catalog.merchantPublicKeyPem)
    detail = "fingerprint " + catalog.merchantFingerprint if sig_ok else "tampered or wrong desk"
    push("signature", "merchant Ed25519 signature verifies", sig_ok, detail)
    if not sig_ok:
        return fail("SIGNATURE_INVALID")

    # 4. expiry
    live = now_ms < mandate.expiresAtMs
    if live:
        detail = f"expires in {max(0, round((mandate.expiresAtMs - now_ms) / 1000))}s"
    else:
        detail = f"expired {round((now_ms - mandate.expiresAtMs) / 1000)}s ago"
    push("expiry", "mandate is unexpired", live, detail)
    if not live:
        return fail("MANDATE_EXPIRED")

    # 5. items resolve against the mandate allowlist
    for line in order.items:
        mandated = next((mi for mi in mandate.items if mi.productId == line.productId), None)
        if not mandated:
            push("allowlist", "order items are inside the mandate", False, f"{line.productId} is not in the mandate")
            return fail("ITEM_NOT_IN_MANDATE")
        if line.quantity > mandated.quantity:
            push("allowlist", "order items are inside the mandate", False, f"{line.productId}: {line.quantity} > mandated {mandated.quantity}")
            return fail("QUANTITY_OVER_MANDATE")
            
    push("allowlist", "order items are inside the mandate", True, f"{len(order.items)} line(s) covered")

    # 6. price re-verification
    for mi in mandate.items:
        live_product = catalog.byId.get(mi.productId)
        if not live_product:
            push("price", "prices re-verified at bind", False, f"{mi.productId} no longer stocked")
            return fail("PRICE_CHANGED_AT_BIND", "delisted")
        if live_product.pricePaise != mi.unitPricePaise:
            push("price", "prices re-verified at bind", False, f"{mi.productId}: mandated {rupees(mi.unitPricePaise)}, now {rupees(live_product.pricePaise)}")
            return fail("PRICE_CHANGED_AT_BIND")
            
    push("price", "prices re-verified at bind", True, "catalog matches mandate snapshots")

    # 7. server-side total
    total_paise = 0
    for line in order.items:
        product = catalog.byId.get(line.productId)
        if not product:
            return fail("PRICE_CHANGED_AT_BIND", "delisted at total")
        total_paise += product.pricePaise * line.quantity
        
    agent_differs = order.claimedTotalPaise is not None and order.claimedTotalPaise != total_paise
    total_detail = f"{rupees(total_paise)}"
    if agent_differs:
        total_detail += f" — agent claimed {rupees(order.claimedTotalPaise)}, corrected"
    push("total", "total recomputed server-side", True, total_detail)

    # 8. trust-tier bounds
    tier = TRUST_TIERS[mandate.tier]
    if total_paise > tier["maxAmountPaise"]:
        push("tier", "total within trust-tier bound", False, f"{rupees(tier['maxAmountPaise'])} cap for {tier['label']}")
        return fail("AMOUNT_OVER_TIER")
        
    distinct = len(order.items)
    if distinct > tier["maxItems"]:
        push("tier", "distinct items within trust-tier bound", False, f"{distinct} > {tier['maxItems']}")
        return fail("ITEM_COUNT_OVER_TIER")
        
    push("tier", "trust-tier bounds hold", True, f"{rupees(tier['maxAmountPaise'])} / {tier['maxItems']} items for {tier['label']}")

    # 9. mandate cap
    under_cap = total_paise <= mandate.amountCapPaise
    push("cap", "total is under the mandate cap", under_cap, f"{rupees(total_paise)} of {rupees(mandate.amountCapPaise)}")
    if not under_cap:
        return fail("AMOUNT_OVER_CAP")

    # 10. human threshold
    if total_paise >= HUMAN_APPROVAL_THRESHOLD_PAISE and not mandate.humanApproved:
        push("human", "under the ₹10,000 human-approval threshold", False, f"{rupees(total_paise)} needs a human at the desk")
        return GateDecision(
            kind="HOLD_FOR_APPROVAL",
            code="OVER_HUMAN_THRESHOLD_UNAPPROVED",
            reason=REFUSAL_REASONS["OVER_HUMAN_THRESHOLD_UNAPPROVED"],
            checks=checks,
            decidedAtMs=now_ms,
            totalPaise=total_paise
        )
        
    push(
        "human",
        "human-approval threshold",
        None if total_paise >= HUMAN_APPROVAL_THRESHOLD_PAISE else True,
        "over threshold — human approval on file" if total_paise >= HUMAN_APPROVAL_THRESHOLD_PAISE else f"under {rupees(HUMAN_APPROVAL_THRESHOLD_PAISE)}"
    )

    return GateDecision(
        kind="ALLOW",
        code=None,
        reason="cleared — all bounds verified",
        checks=checks,
        decidedAtMs=now_ms,
        totalPaise=total_paise
    )
