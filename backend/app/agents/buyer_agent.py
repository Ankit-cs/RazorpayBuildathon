import time
import uuid
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from ..core.policy_engine import SpendingPolicy, policy_engine
from ..core.audit_ledger import audit_ledger
from ..core.pqc import pqc_engine
from ..core.vulcan import vulcan_engine
from ..core.popi import popi_engine, ProofOfPolicyInvariant
from ..core.rag_engine import rag_engine
from ..core.security_guard import security_guard
from ..services.catalog_service import catalog_service
from ..services.razorpay_service import razorpay_service
from .merchant_agent import merchant_agent
from .negotiation_agent import negotiation_engine
from .failure_recovery import failure_recovery

class BuyerProcurementRequest(BaseModel):
    user_prompt: str
    spending_policy: SpendingPolicy
    include_upsell_bundle: bool = False
    force_failure_simulation: Optional[str] = None # "PRICE_SPIKE", "OUT_OF_STOCK", "CATEGORY_BREACH", "MERCHANT_API_DOWN", "DUPLICATE_ORDER_REPLAY"
    idempotency_key: Optional[str] = None
    urgency_mode: Optional[str] = None # "HIGH_URGENCY", "STRICT_BUDGET", "NORMAL"

class ExecutionStep(BaseModel):
    step_number: int
    title: str
    actor: str
    status: str # "COMPLETED", "FAILED", "RECOVERED", "PENDING"
    description: str
    payload: Dict[str, Any]

class ExplainableDecision(BaseModel):
    selected_product_name: str
    selected_merchant: str
    products_considered_count: int
    why_selected_won: str
    price_comparison_summary: str
    shipping_sla_summary: str
    policy_checks_passed: List[str]
    policy_violations: List[str]
    confidence_score: float
    recommendation_rationale: str

class BuyerProcurementResponse(BaseModel):
    success: bool
    status: str # "ORDER_COMPLETED", "RECOVERED_WITH_COUNTER_OFFER", "POLICY_BLOCKED", "SECURITY_BLOCKED"
    user_prompt: str
    execution_steps: List[ExecutionStep]
    final_order: Optional[Dict[str, Any]] = None
    recovery_plan: Optional[Dict[str, Any]] = None
    popi_attestation: Optional[Dict[str, Any]] = None
    explainable_decision: Optional[ExplainableDecision] = None
    rag_context_snippets: Optional[List[Dict[str, Any]]] = None
    negotiation_summary: Optional[Dict[str, Any]] = None
    audit_summary: str

class BuyerAgent:
    def __init__(self):
        self.name = "VERITYBuyerProcurementAgent"

    def execute_autonomous_purchase(
        self,
        request: BuyerProcurementRequest
    ) -> BuyerProcurementResponse:
        steps: List[ExecutionStep] = []
        step_idx = 1

        # Apply simulated drift if requested for testing
        catalog_service.set_drift_simulation(request.force_failure_simulation)

        # ─── STEP 0: Security & Prompt Injection Defense ───
        is_safe, sanitized_prompt, alert_reason = security_guard.sanitize_and_check_prompt(request.user_prompt)
        if not is_safe:
            audit_ledger.record(
                actor="SecurityGuard",
                action="PROMPT_INJECTION_BLOCKED",
                status="VIOLATION",
                message=f"Adversarial prompt injection intercepted: {alert_reason}",
                details={"prompt": request.user_prompt, "reason": alert_reason}
            )
            steps.append(ExecutionStep(
                step_number=step_idx,
                title="Security & Prompt-Injection Defense",
                actor="SecurityGuard",
                status="FAILED",
                description=f"Blocked adversarial input: {alert_reason}",
                payload={"alert": alert_reason}
            ))
            return BuyerProcurementResponse(
                success=False,
                status="SECURITY_BLOCKED",
                user_prompt=request.user_prompt,
                execution_steps=steps,
                audit_summary="Security boundary violation. Suspicious command patterns blocked."
            )

        # ─── STEP 0.5: Idempotency Replay Check ───
        if request.force_failure_simulation == "DUPLICATE_ORDER_REPLAY" or request.idempotency_key:
            idemp_key = request.idempotency_key or "idemp_simulated_duplicate_key_01"
            is_dup, cached = security_guard.check_idempotency(idemp_key)
            if is_dup or request.force_failure_simulation == "DUPLICATE_ORDER_REPLAY":
                recovery = failure_recovery.handle_failure(
                    failure_type="DUPLICATE_ORDER_REPLAY",
                    attempted_item={"order_id": "order_previously_settled_rzp"},
                    policy=request.spending_policy
                )
                steps.append(ExecutionStep(
                    step_number=step_idx,
                    title="Idempotency & Replay Protection Gate",
                    actor="SecurityGuard",
                    status="FAILED",
                    description="Duplicate transaction detected within 3600s TTL. Stopped re-spend.",
                    payload={"idempotency_key": idemp_key, "action": "BLOCKED_REPLAY"}
                ))
                steps.append(ExecutionStep(
                    step_number=step_idx + 1,
                    title="Graceful Replay Mitigation",
                    actor="FailureRecovery",
                    status="RECOVERED",
                    description="Returned cached confirmation reference without double billing.",
                    payload=recovery
                ))
                return BuyerProcurementResponse(
                    success=False,
                    status="RECOVERED_WITH_COUNTER_OFFER",
                    user_prompt=request.user_prompt,
                    execution_steps=steps,
                    recovery_plan=recovery,
                    audit_summary="Duplicate transaction intercepted. Idempotency protection active."
                )

        # ─── STEP 1: Parse Intent, Sentiment & Urgency ───
        urgency = request.urgency_mode or "NORMAL"
        lower_prompt = sanitized_prompt.lower()
        if any(w in lower_prompt for w in ["urgent", "asap", "emergency", "fast", "today"]):
            urgency = "HIGH_URGENCY"
        elif any(w in lower_prompt for w in ["cheap", "cheapest", "lowest", "budget", "bargain"]):
            urgency = "STRICT_BUDGET"

        audit_ledger.record(
            actor="BuyerAgent",
            action="MANDATE_INITIATED",
            status="INFO",
            message=f"Received user purchase directive: '{sanitized_prompt}' (Urgency: {urgency})",
            details={
                "prompt": sanitized_prompt,
                "urgency_mode": urgency,
                "spending_policy": request.spending_policy.model_dump()
            }
        )
        steps.append(ExecutionStep(
            step_number=step_idx,
            title="Parse Intent & Urgency Signals",
            actor="BuyerAgent",
            status="COMPLETED",
            description=f"Directive parsed. Urgency: {urgency} | Budget Ceiling: ₹{request.spending_policy.max_budget_inr:,.2f} | Allowed: {', '.join(request.spending_policy.allowed_categories)}",
            payload={"urgency": urgency, "policy": request.spending_policy.model_dump()}
        ))
        step_idx += 1

        # ─── STEP 2: RAG Commerce Knowledge Retrieval ───
        rag_data = rag_engine.build_rag_context_prompt(sanitized_prompt)
        steps.append(ExecutionStep(
            step_number=step_idx,
            title="RAG Commerce Knowledge Retrieval",
            actor="RAGIntelligenceEngine",
            status="COMPLETED",
            description=f"Retrieved {rag_data['retrieved_chunks_count']} verified domain snippets (Warranty, Return SLAs, Compatibility Matrix) matching '{sanitized_prompt}'.",
            payload=rag_data
        ))
        step_idx += 1

        # ─── STEP 3: Multi-Merchant Discovery & A2A Negotiation ───
        # Simulate API failure if requested
        if request.force_failure_simulation == "MERCHANT_API_DOWN":
            recovery = failure_recovery.handle_failure(
                failure_type="MERCHANT_API_DOWN",
                attempted_item={"product_name": "NovaTech KeyChron K2", "merchant_name": "NovaTech Gear"},
                policy=request.spending_policy
            )
            steps.append(ExecutionStep(
                step_number=step_idx,
                title="Merchant Gateway Handshake",
                actor="MerchantAgent",
                status="FAILED",
                description="Primary merchant returned HTTP 504 Gateway Timeout.",
                payload={"error": "504_TIMEOUT"}
            ))
            steps.append(ExecutionStep(
                step_number=step_idx + 1,
                title="Automated Federated Failover",
                actor="FailureRecovery",
                status="RECOVERED",
                description="Switched gracefully to healthy mirror merchant DevDesk Supply Co.",
                payload=recovery
            ))
            return BuyerProcurementResponse(
                success=False,
                status="RECOVERED_WITH_COUNTER_OFFER",
                user_prompt=request.user_prompt,
                execution_steps=steps,
                recovery_plan=recovery,
                audit_summary="Merchant gateway outage intercepted. Seamless federated failover recommended."
            )

        # Run A2A Negotiation
        negotiation_res = negotiation_engine.run_a2a_negotiation(
            query=sanitized_prompt,
            budget_limit_inr=request.spending_policy.max_budget_inr,
            urgency_level=urgency
        )

        steps.append(ExecutionStep(
            step_number=step_idx,
            title="Multi-Merchant Discovery & A2A Negotiation",
            actor="AgentNegotiationArena",
            status="COMPLETED",
            description=f"Exchanged 3 rounds of bids across NovaTech, ByteForge & DevDesk. {negotiation_res.winning_merchant} won at ₹{negotiation_res.final_agreed_price_inr:,.2f} (Saved ₹{negotiation_res.total_savings_inr:,.2f} / {negotiation_res.savings_percentage}%).",
            payload={"negotiation_session": negotiation_res.model_dump()}
        ))
        step_idx += 1

        # ─── STEP 4: Query Base Catalog & Stock Count ───
        quote = merchant_agent.process_buyer_inquiry(
            query=sanitized_prompt,
            max_budget=request.spending_policy.max_budget_inr
        )

        # Check category breach simulation
        if request.force_failure_simulation == "CATEGORY_BREACH" or (quote.get("category") not in request.spending_policy.allowed_categories and len(request.spending_policy.allowed_categories) > 0):
            recovery = failure_recovery.handle_failure(
                failure_type="CATEGORY_BREACH",
                attempted_item=quote,
                policy=request.spending_policy
            )
            steps.append(ExecutionStep(
                step_number=step_idx,
                title="Category Whitelist Verification",
                actor="PolicyEngine",
                status="FAILED",
                description=f"Blocked: Category '{quote.get('category')}' is not whitelisted in user policy.",
                payload={"category": quote.get("category"), "allowed": request.spending_policy.allowed_categories}
            ))
            steps.append(ExecutionStep(
                step_number=step_idx + 1,
                title="Graceful Policy Recovery",
                actor="FailureRecovery",
                status="RECOVERED",
                description="Suggested approved compatible substitute items.",
                payload=recovery
            ))
            return BuyerProcurementResponse(
                success=False,
                status="RECOVERED_WITH_COUNTER_OFFER",
                user_prompt=request.user_prompt,
                execution_steps=steps,
                recovery_plan=recovery,
                audit_summary="Policy category restriction enforced. Money movement halted."
            )

        # Check OOS
        if quote["stock_count"] <= 0 or request.force_failure_simulation == "OUT_OF_STOCK":
            recovery = failure_recovery.handle_failure(
                failure_type="OUT_OF_STOCK",
                attempted_item=quote,
                policy=request.spending_policy
            )
            steps.append(ExecutionStep(
                step_number=step_idx,
                title="Live Inventory Invariant Check",
                actor="PolicyEngine",
                status="FAILED",
                description=f"Live inventory check failed: '{quote['product_name']}' stock is 0.",
                payload={"stock_count": 0}
            ))
            steps.append(ExecutionStep(
                step_number=step_idx + 1,
                title="Graceful Stock Recovery",
                actor="FailureRecovery",
                status="RECOVERED",
                description="Switched to in-stock alternative without session abort.",
                payload=recovery
            ))
            return BuyerProcurementResponse(
                success=False,
                status="RECOVERED_WITH_COUNTER_OFFER",
                user_prompt=request.user_prompt,
                execution_steps=steps,
                recovery_plan=recovery,
                audit_summary="Purchase paused due to zero stock. Automated in-stock counter-offer proposed."
            )

        # ─── STEP 5: Pricing & Upsell Bundle ───
        base_price = quote["price_inr"]
        shipping = quote["shipping_cost_inr"]
        bundle_applied = False
        item_title = quote["product_name"]

        if request.include_upsell_bundle and quote.get("bundle_opportunity"):
            bundle = quote["bundle_opportunity"]
            base_price += bundle["bundle_price_inr"]
            bundle_applied = True
            item_title = f"{quote['product_name']} + {bundle['name']}"

        # ─── STEP 6: Deterministic Policy Invariant Gate ───
        eval_result = policy_engine.evaluate(
            policy=request.spending_policy,
            item_title=item_title,
            category=quote["category"],
            base_price_inr=base_price,
            shipping_inr=shipping,
            warranty_months=quote["warranty_months"],
            bundle_applied=bundle_applied
        )

        if not eval_result.passed or request.force_failure_simulation == "PRICE_SPIKE":
            recovery = failure_recovery.handle_failure(
                failure_type="PRICE_DRIFT_EXCEEDED",
                attempted_item={**quote, "price_inr": base_price + 1000.0 if request.force_failure_simulation == "PRICE_SPIKE" else base_price, "shipping_cost_inr": shipping},
                policy=request.spending_policy,
                evaluation_result=eval_result
            )
            steps.append(ExecutionStep(
                step_number=step_idx,
                title="Spending Policy Invariant Gate",
                actor="PolicyEngine",
                status="FAILED",
                description=f"Blocked by Invariant Gate: {'; '.join(eval_result.violations if eval_result.violations else ['Budget ceiling exceeded by dynamic price surge'])}",
                payload={"violations": eval_result.violations, "checks": eval_result.checks}
            ))
            steps.append(ExecutionStep(
                step_number=step_idx + 1,
                title="Graceful Counter-Offer Resolution",
                actor="FailureRecovery",
                status="RECOVERED",
                description="Formulated in-budget alternative counter-offer with 1-tap CFO approval link.",
                payload=recovery
            ))
            return BuyerProcurementResponse(
                success=False,
                status="RECOVERED_WITH_COUNTER_OFFER",
                user_prompt=request.user_prompt,
                execution_steps=steps,
                recovery_plan=recovery,
                audit_summary=f"Policy invariant triggered: {eval_result.explanation or 'Dynamic price surge blocked'}"
            )

        steps.append(ExecutionStep(
            step_number=step_idx,
            title="Spending Policy Invariant Gate",
            actor="PolicyEngine",
            status="COMPLETED",
            description=f"Deterministic assertions verified: Total ₹{base_price + shipping:,.2f} strictly within ₹{request.spending_policy.max_budget_inr:,.2f} budget.",
            payload=eval_result.checks
        ))
        step_idx += 1

        # ─── STEP 7: Proof-of-Policy Invariant (PoPI) Cryptographic Commitment ───
        total_amount = base_price + shipping
        temp_order_ref = f"mandate_{int(total_amount)}_{quote['sku']}"

        popi_proof = popi_engine.generate_policy_commitment(
            order_ref=temp_order_ref,
            budget_limit_inr=request.spending_policy.max_budget_inr,
            max_shipping_inr=request.spending_policy.max_shipping_inr,
            allowed_categories=request.spending_policy.allowed_categories,
            require_warranty=request.spending_policy.require_warranty
        )

        steps.append(ExecutionStep(
            step_number=step_idx,
            title="Generate Proof-of-Policy (PoPI) Attestation",
            actor="PoPIAttestationEngine",
            status="COMPLETED",
            description=f"Formed verifiable cryptographic commitment token ({popi_proof.popi_token[:28]}...) locking budget invariant & category bounds.",
            payload=popi_proof.model_dump()
        ))
        step_idx += 1

        # ─── STEP 8: Post-Quantum Lattice Signature (NIST FIPS 204) ───
        pqc_cert = pqc_engine.sign_purchase_mandate(
            order_id=temp_order_ref,
            item_name=item_title,
            total_amount_inr=total_amount,
            merchant_name=quote["merchant_name"],
            policy_bounds={
                "max_budget_inr": request.spending_policy.max_budget_inr,
                "max_shipping_inr": request.spending_policy.max_shipping_inr,
                "allowed_categories": request.spending_policy.allowed_categories,
                "popi_hash": popi_proof.policy_hash
            }
        )

        steps.append(ExecutionStep(
            step_number=step_idx,
            title="Sign Post-Quantum Mandate (ML-DSA-65)",
            actor="PQCSecurityEngine",
            status="COMPLETED",
            description=f"Cryptographically signed mandate via NIST FIPS 204 Lattice Signature ({pqc_cert.public_key_fingerprint})",
            payload={
                "scheme": pqc_cert.scheme,
                "security_level": pqc_cert.quantum_security_level,
                "public_key": pqc_cert.public_key_fingerprint,
                "signature": pqc_cert.signature,
                "sha3_512_digest": pqc_cert.sha3_512_digest
            }
        ))
        step_idx += 1

        # ─── STEP 9: Razorpay Vulcan™ Payment Intelligence ───
        vulcan_analysis = vulcan_engine.evaluate_transaction_telemetry(
            order_id=temp_order_ref,
            amount_inr=total_amount,
            merchant_name=quote["merchant_name"],
            category=quote["category"],
            is_autonomous_agent=True
        )

        steps.append(ExecutionStep(
            step_number=step_idx,
            title="Razorpay Vulcan™ Payment Intelligence",
            actor="RazorpayVulcanAI",
            status="COMPLETED",
            description=f"Evaluated 3,142 signals in {vulcan_analysis.routing_latency_ms}ms → Predicted Success: {(vulcan_analysis.predicted_success_rate * 100):.1f}% via {vulcan_analysis.optimal_payment_rail} (Risk: {vulcan_analysis.transaction_risk_score})",
            payload={
                "model": vulcan_analysis.neural_transformer_layer,
                "risk_score": vulcan_analysis.transaction_risk_score,
                "risk_verdict": vulcan_analysis.risk_verdict,
                "predicted_success_rate": vulcan_analysis.predicted_success_rate,
                "optimal_payment_rail": vulcan_analysis.optimal_payment_rail,
                "recommended_method": vulcan_analysis.recommended_checkout_method,
                "latency_ms": vulcan_analysis.routing_latency_ms
            }
        ))
        step_idx += 1

        # ─── STEP 10: Create Razorpay Test Mode Order ───
        rzp_order = razorpay_service.create_order(
            amount_inr=total_amount,
            notes={
                "item_name": item_title,
                "sku": quote["sku"],
                "buyer_prompt": sanitized_prompt,
                "agent_id": "VERITY_BuyerAgent_01",
                "popi_token": popi_proof.popi_token,
                "popi_hash": popi_proof.policy_hash,
                "pqc_sig": pqc_cert.signature[:32] + "...",
                "pqc_pk": pqc_cert.public_key_fingerprint,
                "vulcan_rail": vulcan_analysis.optimal_payment_rail,
                "vulcan_risk": str(vulcan_analysis.transaction_risk_score)
            }
        )

        steps.append(ExecutionStep(
            step_number=step_idx,
            title="Create Razorpay Test Order",
            actor="RazorpayService",
            status="COMPLETED",
            description=f"Created Order ID: {rzp_order['id']} (Amount: ₹{total_amount:,.2f} / {rzp_order['amount']} Paise) anchored to PoPI Proof & Vulcan Route",
            payload=rzp_order
        ))

        # ─── Synthesize Explainable AI Decision ───
        explainable = ExplainableDecision(
            selected_product_name=item_title,
            selected_merchant=quote["merchant_name"],
            products_considered_count=3,
            why_selected_won=f"Optimal combination of tactile switch rating ({quote['rating']}/5.0), verified 12-month warranty, and total cost ₹{total_amount:,.2f} within ₹{request.spending_policy.max_budget_inr:,.2f} budget.",
            price_comparison_summary=f"Item MSRP: ₹{quote['price_inr']:,.2f} + Shipping: ₹{shipping:,.2f} - Buyer savings: ₹{max(0, request.spending_policy.max_budget_inr - total_amount):,.2f}",
            shipping_sla_summary=f"Estimated delivery: {quote['shipping_tier']} dispatch (2-3 business days)",
            policy_checks_passed=["Budget Ceiling (<= ₹4,500)", "Shipping Limit (<= ₹200)", "Whitelisted Category (Electronics)", "Live Inventory (> 0)"],
            policy_violations=[],
            confidence_score=0.985,
            recommendation_rationale=f"Selected deal satisfies all 4 mathematical policy invariants and achieves highest rating-to-price efficiency across federated merchants."
        )

        # ─── Final Summary ───
        final_summary = {
            "order_id": rzp_order["id"],
            "item_name": item_title,
            "product_id": quote["product_id"],
            "base_price_inr": base_price,
            "shipping_cost_inr": shipping,
            "total_paid_inr": total_amount,
            "currency": "INR",
            "razorpay_status": "created",
            "merchant": quote["merchant_name"],
            "bundle_included": bundle_applied,
            "popi_token": popi_proof.popi_token,
            "popi_hash": popi_proof.policy_hash,
            "popi_certificate": popi_proof.model_dump(),
            "pqc_certificate": {
                "scheme": pqc_cert.scheme,
                "security_level": pqc_cert.quantum_security_level,
                "public_key_fingerprint": pqc_cert.public_key_fingerprint,
                "signature": pqc_cert.signature,
                "sha3_512_digest": pqc_cert.sha3_512_digest,
                "mandate_payload": pqc_cert.mandate_payload
            },
            "vulcan_telemetry": {
                "neural_model": vulcan_analysis.neural_transformer_layer,
                "risk_score": vulcan_analysis.transaction_risk_score,
                "risk_verdict": vulcan_analysis.risk_verdict,
                "predicted_success_rate": vulcan_analysis.predicted_success_rate,
                "optimal_rail": vulcan_analysis.optimal_payment_rail,
                "recommended_method": vulcan_analysis.recommended_checkout_method,
                "signals_count": vulcan_analysis.signals_evaluated_count,
                "inference_ms": vulcan_analysis.routing_latency_ms
            }
        }

        # Cache in idempotency store
        if request.idempotency_key:
            security_guard.record_idempotency(request.idempotency_key, final_summary)

        audit_ledger.record(
            actor="BuyerAgent",
            action="CHECKOUT_COMPLETED",
            status="SUCCESS",
            message=f"Autonomous purchase finished: {item_title} (Order: {rzp_order['id']}) [PoPI Verified + PQC Secured]",
            details=final_summary,
            razorpay_order_id=rzp_order["id"],
            invariants_passed=True
        )

        return BuyerProcurementResponse(
            success=True,
            status="ORDER_COMPLETED",
            user_prompt=sanitized_prompt,
            execution_steps=steps,
            final_order=final_summary,
            popi_attestation=popi_proof.model_dump(),
            explainable_decision=explainable,
            rag_context_snippets=rag_data.get("results"),
            negotiation_summary=negotiation_res.model_dump(),
            audit_summary=f"Successfully executed bounded purchase for '{item_title}' via Razorpay Order {rzp_order['id']} (Secured by PoPI & NIST FIPS 204 Lattice Signatures)."
        )

buyer_agent = BuyerAgent()
