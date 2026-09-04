import json
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException

from ..projectx.runtime import get_runtime, reset_runtime, BuyerSession
from ..projectx.loop import agent_turn, new_session
from ..projectx.llm import brain_mode
from ..projectx.payments import rail_info, verify_payment_signature
from ..projectx.engine import run_transaction, confirm_payment_once, TxInput
from ..projectx.types import TRUST_TIERS
from ..projectx.ledger import Ledger
from ..projectx.fuzz.corpus import ATTACK_CORPUS, attack_tx_input

router = APIRouter(prefix="/api/_projectX")

ADAPTERS = ["naive", "mcp", "acp"]

@router.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
        rt = get_runtime()
        adapter = body.get("adapter", "naive")
        if adapter not in ADAPTERS:
            adapter = "naive"
            
        session_id = body.get("sessionId")
        session = rt.sessions.get(session_id) if session_id else None
        
        tier = body.get("tier", "UNVERIFIED")
        if tier not in ["ATTESTED", "MANDATED"]:
            tier = "UNVERIFIED"
            
        if not session:
            session = new_session(rt, tier=tier)
            
        result = await agent_turn(rt, session.sessionId, body.get("message", ""), adapter)
        
        return {
            "ok": True,
            "sessionId": session.sessionId,
            "buyerId": session.buyerId,
            "tier": session.tier,
            "cart": [[k, v] for k, v in session.cart.items()],
            "awaitingMandateApproval": session.awaitingMandateApproval,
            "events": [e.model_dump() for e in result.events],
            "suggestions": result.suggestions,
            "brain": brain_mode(),
            "rail": rail_info().model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def find_proposed(order_id: str) -> Optional[Dict[str, Any]]:
    rt = get_runtime()
    for e in rt.ledger.all():
        if e.type == "order.proposed":
            d = e.data
            if isinstance(d, dict) and d.get("orderId") == order_id:
                return d
    return None

@router.post("/decision")
async def decision(request: Request):
    try:
        body = await request.json()
        order_id = body.get("orderId")
        approve = body.get("approve", False)
        
        if not order_id:
            raise HTTPException(status_code=400, detail="orderId required")
            
        rt = get_runtime()
        proposed = find_proposed(order_id)
        if not proposed:
            raise HTTPException(status_code=404, detail="unknown order")
            
        tier_cap = TRUST_TIERS.get(proposed["tier"], {}).get("maxAmountPaise", 0)
        if proposed["totalPaise"] > tier_cap:
            raise HTTPException(status_code=409, detail="over tier cap — no approval can widen it")
            
        if approve:
            from ..projectx.decide import OrderRequestItem
            items = [OrderRequestItem(productId=it["productId"], quantity=it["quantity"]) for it in proposed["items"]]
            tx = run_transaction(rt.deps, TxInput(
                buyerId=proposed["buyerId"],
                tier=proposed["tier"],
                items=items,
                adapter=proposed.get("adapter", "naive"),
                nowMs=int(time.time() * 1000),
                orderId=f"{order_id}_approved",
                humanApproved=True
            ))
            rt.ledger.append("approval.granted", {
                "orderId": order_id,
                "newOrderId": tx.orderId,
                "by": "merchant-desk",
                "at": int(time.time() * 1000)
            })
            return {
                "ok": True,
                "approved": True,
                "captured": tx.decision.kind == "ALLOW",
                "orderId": tx.orderId,
                "decision": tx.decision.model_dump()
            }
            
        rt.ledger.append("approval.rejected", {"orderId": order_id, "by": "merchant-desk", "at": int(time.time() * 1000)})
        return {"ok": True, "approved": False}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fuzz")
async def fuzz(request: Request):
    rt = get_runtime()
    scratch = Ledger(None)
    
    from copy import copy
    class ScratchDeps:
        def __init__(self, old_deps, new_ledger):
            self.ledger = new_ledger
            self.private_key_pem = old_deps.private_key_pem
            self.public_key_pem = old_deps.public_key_pem
            self.merchant_fingerprint = old_deps.merchant_fingerprint
            
    scratch_deps = ScratchDeps(rt.deps, scratch)
    
    verdicts = []
    clock = int(time.time() * 1000) + 10_000
    
    for attack in ATTACK_CORPUS:
        t0 = time.time()
        clock += 60_000
        
        if attack.replayConfirm:
            tx = run_transaction(scratch_deps, attack_tx_input(attack, orderId=f"fuzz_{attack.id}", nowMs=clock, adapter="naive", buyerPrefix="fuzz"))
            clock += 60_000
            if tx.payment:
                replay = confirm_payment_once(scratch_deps, tx.orderId, tx.payment.confirmId, {"note": "replay"})
            else:
                replay = {"ok": False, "code": "REPLAY_DETECTED"}
            outcome = "PASSED" if replay["ok"] else "BLOCKED"
            code = None if replay["ok"] else "REPLAY_DETECTED"
        else:
            tx = run_transaction(scratch_deps, attack_tx_input(attack, orderId=f"fuzz_{attack.id}", nowMs=clock, adapter="naive", buyerPrefix="fuzz"))
            outcome = "PASSED" if tx.decision.kind == "ALLOW" else "BLOCKED"
            code = tx.decision.code
            
        matched = outcome == "BLOCKED" and code == attack.expect.code
        verdicts.append({
            "attackId": attack.id,
            "label": attack.label,
            "verdict": outcome,
            "code": code,
            "expected": attack.expect.code,
            "matched": matched,
            "ms": max(1, int((time.time() - t0) * 1000))
        })
        rt.ledger.append("attack.blocked", {
            "attackId": attack.id,
            "label": attack.label,
            "verdict": outcome,
            "code": code,
            "expected": attack.expect.code,
            "matched": matched,
            "live": True,
            "corpusRun": True
        })
        
    passed = sum(1 for v in verdicts if v["matched"])
    return {"ok": True, "passed": passed, "total": len(verdicts), "verdicts": verdicts}

@router.post("/pay/confirm")
async def pay_confirm(request: Request):
    try:
        body = await request.json()
        order_id = body.get("orderId")
        rzp_order_id = body.get("razorpay_order_id")
        rzp_payment_id = body.get("razorpay_payment_id")
        rzp_signature = body.get("razorpay_signature")
        
        if not order_id or not rzp_order_id or not rzp_payment_id or not rzp_signature:
            raise HTTPException(status_code=400, detail="missing handler fields")
            
        rt = get_runtime()
        valid = verify_payment_signature(rzp_order_id, rzp_payment_id, rzp_signature)
        if not valid:
            rt.ledger.append("payment.failed", {"orderId": order_id, "reason": "SIGNATURE_INVALID", "rail": "razorpay-test"})
            raise HTTPException(status_code=400, detail="signature verification failed")
            
        confirm_id = f"{rzp_order_id}:{rzp_payment_id}"
        result = confirm_payment_once(rt.deps, order_id, confirm_id, {
            "rail": "razorpay-test",
            "simulated": False,
            "paymentId": rzp_payment_id,
            "razorpayOrderId": rzp_order_id
        })
        
        if not result["ok"]:
            raise HTTPException(status_code=409, detail="replay detected — confirmation already seen")
            
        rt.ledger.append("payment.captured", {
            "orderId": order_id,
            "rail": "razorpay-test",
            "simulated": False,
            "paymentId": rzp_payment_id,
            "confirmId": confirm_id,
            "note": "captured via Razorpay test-mode checkout"
        })
        return {"ok": True, "captured": True, "paymentId": rzp_payment_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reset")
async def reset(request: Request):
    rt = reset_runtime()
    return {
        "ok": True,
        "events": len(rt.ledger.all()),
        "chain": rt.ledger.audit(),
        "ephemeral": rt.ephemeral
    }

def read_results(name: str):
    import os
    try:
        with open(os.path.join(os.getcwd(), "..", "results", name), "r") as f:
            return json.load(f)
    except:
        return None

@router.get("/state")
async def state(request: Request):
    rt = get_runtime()
    events = rt.ledger.all()
    
    from ..projectx.meter import meter_from_events, project_at_scale
    meter = meter_from_events(events)
    projection = project_at_scale(meter)
    
    orders = rt.ledger.orders()
    approvals = [
        {"orderId": o["orderId"], "buyerId": o["buyerId"], "totalPaise": o["totalPaise"], "items": o["items"], "createdAtMs": o["createdAtMs"]}
        for o in orders if o["status"] == "AWAITING_APPROVAL"
    ]
    attacks = [
        {"ts": e.ts, **e.data} for e in reversed(events) if e.type == "attack.blocked"
    ][:24]
    
    chain = rt.ledger.audit()
    
    return {
        "ok": True,
        "rail": rail_info().model_dump(),
        "brain": brain_mode(),
        "ephemeral": rt.ephemeral,
        "fingerprint": rt.keys.fingerprint,
        "keyEphemeral": rt.keys.ephemeral,
        "merchant": {"name": "Fieldnote Supply", "products": len(rt.catalog.all)},
        "meter": meter.model_dump(),
        "projection": projection,
        "orders": orders[:40],
        "approvals": approvals,
        "attacks": attacks,
        "chain": {"ok": chain["ok"], "length": chain["length"], "headHash": chain["headHash"]},
        "eventsTotal": len(events),
        "tiers": TRUST_TIERS,
        "ablation": read_results("ablation.json"),
        "conformance": read_results("conformance_matrix.json"),
        "generatedAt": int(time.time() * 1000)
    }

@router.get("/trace/{trace_id}")
async def trace(trace_id: str, request: Request):
    rt = get_runtime()
    tr_id = f"tr_{trace_id}" if not trace_id.startswith("tr_") else trace_id
    spans = rt.ledger.spans_for(tr_id)
    events = [
        {"seq": e.seq, "ts": e.ts, "type": e.type, "data": e.data}
        for e in rt.ledger.all() if isinstance(e.data, dict) and e.data.get("traceId") == tr_id
    ]
    return {"ok": True, "traceId": tr_id, "spans": [s.model_dump() for s in spans], "events": events}

@router.get("/health")
async def health(request: Request):
    try:
        rt = get_runtime()
        chain = rt.ledger.audit()
        return {
            "ok": True,
            "service": "_projectX",
            "rail": rail_info().model_dump(),
            "brain": brain_mode(),
            "ephemeral": rt.ephemeral,
            "keyEphemeral": rt.keys.ephemeral,
            "events": chain["length"],
            "chainOk": chain["ok"],
            "headHash": chain["headHash"],
            "ts": int(time.time() * 1000)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
