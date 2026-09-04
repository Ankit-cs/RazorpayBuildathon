import os
import uuid
import hmac
import hashlib
import httpx
from typing import Dict, Any, Optional
from pydantic import BaseModel

class RailInfo(BaseModel):
    id: str
    label: str
    simulated: bool

def rail_info() -> RailInfo:
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    secret = os.environ.get("RAZORPAY_KEY_SECRET")
    
    if key_id and secret and not key_id.startswith("rzp_live"):
        return RailInfo(id="razorpay-test", label="Razorpay test mode", simulated=False)
        
    if key_id and key_id.startswith("rzp_live"):
        raise ValueError("live keys refused — test keys (rzp_test_) only")
        
    return RailInfo(id="simulation", label="simulation (no keys)", simulated=True)

class PaymentOrder(BaseModel):
    rail: str
    railOrderId: str
    amountPaise: int
    receipt: str
    keyId: Optional[str] = None

class PaymentCapture(BaseModel):
    rail: str
    simulated: bool
    paymentId: str
    confirmId: str
    amountPaise: int

async def create_razorpay_order(amount_paise: int, receipt: str, notes: Dict[str, str]) -> PaymentOrder:
    key_id = os.environ.get("RAZORPAY_KEY_ID")
    secret = os.environ.get("RAZORPAY_KEY_SECRET")
    
    if not key_id or not secret:
        raise ValueError("Razorpay credentials missing")
        
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.razorpay.com/v1/orders",
            auth=(key_id, secret),
            json={
                "amount": amount_paise,
                "currency": "INR",
                "receipt": receipt,
                "notes": notes
            },
            timeout=10.0
        )
        
    if not res.is_success:
        raise Exception(f"razorpay order creation failed: {res.status_code} {res.text}")
        
    data = res.json()
    return PaymentOrder(
        rail="razorpay-test",
        railOrderId=data["id"],
        amountPaise=amount_paise,
        receipt=receipt,
        keyId=key_id
    )

def simulated_order(amount_paise: int, receipt: str) -> PaymentOrder:
    return PaymentOrder(
        rail="simulation",
        railOrderId=f"sim_order_{uuid.uuid4().hex[:8]}",
        amountPaise=amount_paise,
        receipt=receipt
    )

def simulated_capture(amount_paise: int) -> PaymentCapture:
    return PaymentCapture(
        rail="simulation",
        simulated=True,
        paymentId=f"sim_pay_{uuid.uuid4().hex[:12]}",
        confirmId=f"sim_conf_{uuid.uuid4().hex[:12]}",
        amountPaise=amount_paise
    )

def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    secret = os.environ.get("RAZORPAY_KEY_SECRET")
    if not secret:
        return False
        
    payload = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return expected == signature

def verify_webhook_signature(raw_body: str, signature: str, webhook_secret: str) -> bool:
    expected = hmac.new(webhook_secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
    return expected == signature
