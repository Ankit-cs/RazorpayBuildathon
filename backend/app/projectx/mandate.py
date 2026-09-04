import base64
from typing import List, Optional
from pydantic import BaseModel
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

from .types import MandateItem, TrustTier, TRUST_TIERS, MandateBody, Mandate
from .canonical import canonical_json, CanonicalError

class IssueMandateInput(BaseModel):
    buyerId: str
    tier: TrustTier
    items: List[MandateItem]
    nowMs: int
    humanApproved: Optional[bool] = False
    amountCapPaise: Optional[int] = None
    ttlMs: Optional[int] = None

def build_mandate_body(input_data: IssueMandateInput, mandate_id: str) -> MandateBody:
    tier = TRUST_TIERS[input_data.tier]
    ttl = input_data.ttlMs if input_data.ttlMs is not None else tier["mandateTtlMs"]
    requested = input_data.amountCapPaise if input_data.amountCapPaise is not None else tier["maxAmountPaise"]
    
    if not isinstance(requested, int) or requested <= 0:
        raise ValueError("amountCapPaise must be a positive safe integer")
        
    amountCapPaise = min(requested, tier["maxAmountPaise"])
    
    return MandateBody(
        id=mandate_id,
        buyerId=input_data.buyerId,
        tier=input_data.tier,
        amountCapPaise=amountCapPaise,
        items=input_data.items,
        currency="INR",
        issuedAtMs=input_data.nowMs,
        expiresAtMs=input_data.nowMs + ttl,
        humanApproved=input_data.humanApproved or False
    )

def sign_mandate(body: MandateBody, private_key_pem: str) -> Mandate:
    payload = canonical_json(body.model_dump(exclude_unset=True)).encode('utf-8')
    private_key = serialization.load_pem_private_key(private_key_pem.encode('utf-8'), password=None)
    
    if not isinstance(private_key, ed25519.Ed25519PrivateKey):
        raise ValueError("Provided key is not an Ed25519 private key")
        
    signature = private_key.sign(payload)
    sig_b64 = base64.b64encode(signature).decode('utf-8')
    
    body_dict = body.model_dump(exclude_unset=True)
    return Mandate(**body_dict, signature=sig_b64)

def verify_mandate_signature(mandate: Mandate, public_key_pem: str) -> bool:
    try:
        # Exclude signature to get the body
        mandate_dict = mandate.model_dump(exclude_unset=True)
        signature = mandate_dict.pop("signature")
        
        # Pydantic may convert enums/etc, ensure canonical format matches
        payload = canonical_json(mandate_dict).encode('utf-8')
        
        public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        if not isinstance(public_key, ed25519.Ed25519PublicKey):
            return False
            
        sig_bytes = base64.b64decode(signature)
        public_key.verify(sig_bytes, payload)
        return True
    except CanonicalError:
        raise
    except (InvalidSignature, Exception):
        return False
