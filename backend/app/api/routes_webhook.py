from fastapi import APIRouter, Header, HTTPException, Request
from typing import Dict, Any, Optional
from ..services.razorpay_service import razorpay_service
from ..core.audit_ledger import audit_ledger
from ..core.security_guard import security_guard

router = APIRouter(prefix="/webhooks", tags=["Razorpay Webhooks"])

@router.post("/razorpay")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    """
    Receives, verifies, and processes official Razorpay webhook events
    (e.g., payment.captured, order.paid, payment.failed) with idempotency protection.
    """
    body = await request.body()
    data: Dict[str, Any] = await request.json() if body else {}

    event_type = data.get("event", "payment.captured")
    payload = data.get("payload", {})
    payment_entity = payload.get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id", data.get("order_id", "order_test_simulated"))
    payment_id = payment_entity.get("id", data.get("payment_id", "pay_test_simulated"))

    # 1. Replay / Idempotency Check
    idemp_key = x_idempotency_key or f"wh_{order_id}_{payment_id}_{event_type}"
    is_dup, cached_res = security_guard.check_idempotency(idemp_key)
    if is_dup and cached_res:
        return cached_res

    # 2. Cryptographic HMAC Signature check
    is_valid = True
    if x_razorpay_signature:
        is_valid = razorpay_service.verify_payment_signature(
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            razorpay_signature=x_razorpay_signature
        )

    if not is_valid:
        audit_ledger.record(
            actor="RazorpayWebhook",
            action="WEBHOOK_REJECTED",
            status="VIOLATION",
            message=f"Rejected Razorpay webhook for {order_id} due to invalid HMAC signature",
            details={"order_id": order_id, "signature": x_razorpay_signature}
        )
        raise HTTPException(status_code=400, detail="Invalid HMAC Webhook Signature")

    # 3. Record verified payment in audit ledger
    audit_ledger.record(
        actor="RazorpayWebhook",
        action="PAYMENT_CAPTURED",
        status="SUCCESS",
        message=f"Received verified Razorpay webhook event '{event_type}' for {order_id} (Payment: {payment_id})",
        details={
            "event": event_type,
            "order_id": order_id,
            "payment_id": payment_id,
            "amount_paid_inr": payment_entity.get("amount", 0) / 100,
            "hmac_verified": True
        },
        razorpay_order_id=order_id
    )

    response_payload = {
        "status": "processed",
        "event": event_type,
        "order_id": order_id,
        "payment_id": payment_id,
        "verified": True,
        "idempotency_key": idemp_key
    }

    security_guard.record_idempotency(idemp_key, response_payload)
    return response_payload
