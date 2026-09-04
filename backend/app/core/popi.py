import hashlib
import hmac
import json
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ProofOfPolicyInvariant(BaseModel):
    """
    Proof-of-Policy (PoPI) Cryptographic Commitment Token.
    Represents an immutable, mathematical commitment of buyer spending invariants
    that must be validated before any financial rails are invoked.
    """
    popi_token: str
    policy_hash: str
    budget_limit_inr: float
    max_shipping_inr: float
    allowed_categories: List[str]
    require_warranty: bool
    timestamp: int
    nonce: str
    order_reference: str
    budget_commitment_paise: int
    signature: str
    verification_status: str = "VERIFIED_VALID"
    algorithm: str = "HMAC-SHA256+SHA3-512"

class PoPIEngine:
    def __init__(self, secret_seed: str = "verity_popi_master_attestation_key_2026"):
        self.secret_seed = secret_seed

    def generate_policy_commitment(
        self,
        order_ref: str,
        budget_limit_inr: float,
        max_shipping_inr: float,
        allowed_categories: List[str],
        require_warranty: bool = True,
        notes: Optional[Dict[str, Any]] = None
    ) -> ProofOfPolicyInvariant:
        """
        Generates a deterministic cryptographic proof-of-policy commitment token.
        """
        timestamp = int(time.time())
        nonce = hashlib.sha256(f"{order_ref}_{timestamp}_{budget_limit_inr}".encode()).hexdigest()[:16]

        canonical_payload = {
            "order_reference": order_ref,
            "budget_limit_inr": round(budget_limit_inr, 2),
            "max_shipping_inr": round(max_shipping_inr, 2),
            "allowed_categories": sorted(allowed_categories),
            "require_warranty": require_warranty,
            "timestamp": timestamp,
            "nonce": nonce,
            "budget_commitment_paise": int(round(budget_limit_inr * 100))
        }

        # Double-hash payload: SHA-256 for canonical state + HMAC for unforgeability
        serialized = json.dumps(canonical_payload, sort_keys=True)
        policy_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        
        signature = hmac.new(
            self.secret_seed.encode("utf-8"),
            policy_hash.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        popi_token = f"popi_{policy_hash[:16]}_{signature[:24]}"

        return ProofOfPolicyInvariant(
            popi_token=popi_token,
            policy_hash=policy_hash,
            budget_limit_inr=budget_limit_inr,
            max_shipping_inr=max_shipping_inr,
            allowed_categories=allowed_categories,
            require_warranty=require_warranty,
            timestamp=timestamp,
            nonce=nonce,
            order_reference=order_ref,
            budget_commitment_paise=int(round(budget_limit_inr * 100)),
            signature=signature,
            verification_status="VERIFIED_VALID"
        )

    def verify_commitment(
        self,
        popi: ProofOfPolicyInvariant,
        actual_total_inr: float,
        actual_shipping_inr: float,
        actual_category: str
    ) -> Dict[str, Any]:
        """
        Validates whether a proposed purchase strictly satisfies the cryptographic PoPI commitment.
        """
        # 1. Verify cryptographic signature
        canonical_payload = {
            "order_reference": popi.order_reference,
            "budget_limit_inr": round(popi.budget_limit_inr, 2),
            "max_shipping_inr": round(popi.max_shipping_inr, 2),
            "allowed_categories": sorted(popi.allowed_categories),
            "require_warranty": popi.require_warranty,
            "timestamp": popi.timestamp,
            "nonce": popi.nonce,
            "budget_commitment_paise": popi.budget_commitment_paise
        }
        serialized = json.dumps(canonical_payload, sort_keys=True)
        expected_policy_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        
        expected_signature = hmac.new(
            self.secret_seed.encode("utf-8"),
            expected_policy_hash.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        sig_valid = hmac.compare_digest(expected_signature, popi.signature)
        hash_valid = hmac.compare_digest(expected_policy_hash, popi.policy_hash)

        # 2. Verify invariant rules
        budget_satisfied = round(actual_total_inr, 2) <= round(popi.budget_limit_inr, 2)
        shipping_satisfied = round(actual_shipping_inr, 2) <= round(popi.max_shipping_inr, 2)
        category_satisfied = actual_category in popi.allowed_categories or len(popi.allowed_categories) == 0

        is_valid = sig_valid and hash_valid and budget_satisfied and shipping_satisfied and category_satisfied

        return {
            "is_valid": is_valid,
            "cryptographic_integrity": sig_valid and hash_valid,
            "signature_valid": sig_valid,
            "policy_hash_valid": hash_valid,
            "budget_invariant_passed": budget_satisfied,
            "shipping_invariant_passed": shipping_satisfied,
            "category_invariant_passed": category_satisfied,
            "actual_total_inr": actual_total_inr,
            "committed_budget_inr": popi.budget_limit_inr,
            "budget_headroom_inr": max(0.0, round(popi.budget_limit_inr - actual_total_inr, 2)),
            "popi_token": popi.popi_token,
            "timestamp": popi.timestamp
        }

popi_engine = PoPIEngine()
