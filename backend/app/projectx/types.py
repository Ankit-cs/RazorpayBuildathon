from typing import Literal, Dict, Any, List, Optional
from pydantic import BaseModel, Field

TrustTier = Literal["UNVERIFIED", "ATTESTED", "MANDATED"]

TRUST_TIERS = {
    "UNVERIFIED": {
        "maxAmountPaise": 50_000,
        "maxItems": 1,
        "mandateTtlMs": 10 * 60_000,
        "label": "unverified walk-in",
        "blurb": "No identity on file. One item, up to ₹500, ten minutes.",
    },
    "ATTESTED": {
        "maxAmountPaise": 500_000,
        "maxItems": 3,
        "mandateTtlMs": 30 * 60_000,
        "label": "attested agent",
        "blurb": "Attested identity (OTP-bound). Three items, up to ₹5,000, half an hour.",
    },
    "MANDATED": {
        "maxAmountPaise": 5_000_000,
        "maxItems": 10,
        "mandateTtlMs": 24 * 3_600_000,
        "label": "mandated agent",
        "blurb": "Signed standing mandate. Ten items, up to ₹50,000, twenty-four hours.",
    },
}

HUMAN_APPROVAL_THRESHOLD_PAISE = 1_000_000

class MandateItem(BaseModel):
    productId: str
    quantity: int
    unitPricePaise: int

class MandateBody(BaseModel):
    id: str
    buyerId: str
    tier: TrustTier
    amountCapPaise: int
    items: List[MandateItem]
    currency: Literal["INR"] = "INR"
    issuedAtMs: int
    expiresAtMs: int
    humanApproved: bool

class Mandate(MandateBody):
    signature: str

MandateStatus = Literal["PENDING_APPROVAL", "ACTIVE", "CONSUMED", "EXPIRED", "REFUSED"]

REFUSAL_REASONS = {
    "AMOUNT_OVER_CAP": "amount exceeds mandate cap",
    "AMOUNT_OVER_TIER": "amount exceeds trust-tier cap",
    "ITEM_COUNT_OVER_TIER": "item count exceeds trust-tier cap",
    "MANDATE_EXPIRED": "mandate expired",
    "PRICE_CHANGED_AT_BIND": "price changed since mandate — re-approval required",
    "SIGNATURE_INVALID": "mandate signature verification failed",
    "OVER_HUMAN_THRESHOLD_UNAPPROVED": "over ₹10,000 without human approval",
    "MALFORMED_MANDATE": "mandate failed canonical parsing",
    "CURRENCY_UNSUPPORTED": "mandate currency is not INR",
    "ITEM_NOT_IN_MANDATE": "item is not covered by the mandate",
    "QUANTITY_OVER_MANDATE": "quantity exceeds mandated quantity",
    "REPLAY_DETECTED": "payment confirmation already seen — replay refused",
    "UNKNOWN": "unclassified refusal",
}

RefusalReason = Literal[
    "AMOUNT_OVER_CAP",
    "AMOUNT_OVER_TIER",
    "ITEM_COUNT_OVER_TIER",
    "MANDATE_EXPIRED",
    "PRICE_CHANGED_AT_BIND",
    "SIGNATURE_INVALID",
    "OVER_HUMAN_THRESHOLD_UNAPPROVED",
    "MALFORMED_MANDATE",
    "CURRENCY_UNSUPPORTED",
    "ITEM_NOT_IN_MANDATE",
    "QUANTITY_OVER_MANDATE",
    "REPLAY_DETECTED",
    "UNKNOWN",
]

GateDecisionKind = Literal["ALLOW", "HOLD_FOR_APPROVAL", "REFUSE"]

class GateCheck(BaseModel):
    id: str
    label: str
    pass_: Optional[bool] = Field(default=None, alias="pass")
    detail: str
    class Config:
        populate_by_name = True

class GateDecision(BaseModel):
    kind: GateDecisionKind
    code: Optional[RefusalReason]
    reason: str
    checks: List[GateCheck]
    decidedAtMs: int
    totalPaise: int
