from typing import Dict, Any, Optional, List
from ..core.audit_ledger import audit_ledger
from ..core.policy_engine import SpendingPolicy, InvariantEvaluationResult
from ..services.catalog_service import catalog_service, Product

class GracefulFailureRecovery:
    @staticmethod
    def handle_failure(
        failure_type: str, # "PRICE_DRIFT_EXCEEDED", "OUT_OF_STOCK", "CATEGORY_BREACH", "MERCHANT_API_DOWN", "DUPLICATE_ORDER_REPLAY"
        attempted_item: Dict[str, Any],
        policy: SpendingPolicy,
        evaluation_result: Optional[InvariantEvaluationResult] = None
    ) -> Dict[str, Any]:
        """
        Catches checkout / policy / API failure and gracefully constructs an alternative counter-offer
        or ambient human-gated approval link without crashing.
        """
        audit_ledger.record(
            actor="FailureRecovery",
            action="RECOVERY_TRIGGERED",
            status="WARNING",
            message=f"Intercepted failure ({failure_type}) for item '{attempted_item.get('product_name')}'",
            details={
                "failure_type": failure_type,
                "attempted_item": attempted_item,
                "policy_bounds": policy.model_dump()
            }
        )

        recovery_strategy = {}

        if failure_type in ["PRICE_DRIFT_EXCEEDED", "PRICE_SPIKE"] or (evaluation_result and not evaluation_result.passed and any("budget" in v.lower() for v in evaluation_result.violations)):
            # Search for best alternative in catalog strictly within budget
            alternatives: List[Product] = catalog_service.search_catalog(
                query="keyboard",
                max_price=policy.max_budget_inr - attempted_item.get("shipping_cost_inr", 100.0)
            )

            viable_alt = None
            for alt in alternatives:
                if alt.id != attempted_item.get("product_id") and alt.stock_count > 0:
                    viable_alt = alt
                    break

            if viable_alt:
                recovery_strategy = {
                    "strategy": "IN_BUDGET_COUNTER_OFFER",
                    "reason": f"Original item price surged to ₹{attempted_item.get('price_inr'):,.2f}, breaching your ₹{policy.max_budget_inr:,.2f} ceiling.",
                    "recommended_action": "SWAP_WITH_ALTERNATIVE",
                    "alternative_product": {
                        "id": viable_alt.id,
                        "name": viable_alt.name,
                        "price_inr": viable_alt.price_inr,
                        "shipping_inr": viable_alt.shipping_cost_inr,
                        "total_inr": viable_alt.price_inr + viable_alt.shipping_cost_inr,
                        "savings_inr": policy.max_budget_inr - (viable_alt.price_inr + viable_alt.shipping_cost_inr),
                        "specs": viable_alt.specs
                    },
                    "human_gated_approval_link": f"/api/approve-override?token=auth_stepup_{attempted_item.get('product_id')}"
                }
            else:
                recovery_strategy = {
                    "strategy": "HUMAN_IN_THE_LOOP_GATE",
                    "reason": f"Total price of ₹{attempted_item.get('price_inr', 0) + attempted_item.get('shipping_cost_inr', 0):,.2f} exceeds budget of ₹{policy.max_budget_inr:,.2f}.",
                    "recommended_action": "REQUEST_HUMAN_STEP_UP",
                    "step_up_delta_inr": (attempted_item.get('price_inr', 0) + attempted_item.get('shipping_cost_inr', 0)) - policy.max_budget_inr,
                    "human_gated_approval_link": f"/api/approve-override?token=auth_stepup_{attempted_item.get('product_id')}"
                }

        elif failure_type == "OUT_OF_STOCK":
            alternatives = catalog_service.search_catalog("keyboard")
            in_stock_alt = next((p for p in alternatives if p.stock_count > 0 and p.id != attempted_item.get("product_id")), None)
            
            recovery_strategy = {
                "strategy": "OUT_OF_STOCK_REROUTE",
                "reason": f"Live inventory for '{attempted_item.get('product_name')}' was exhausted by another buyer immediately prior to order generation.",
                "recommended_action": "OFFER_IN_STOCK_MATCH",
                "alternative_product": {
                    "id": in_stock_alt.id if in_stock_alt else "prod_dock_01",
                    "name": in_stock_alt.name if in_stock_alt else "NovaHub Docking Hub",
                    "price_inr": in_stock_alt.price_inr if in_stock_alt else 3299.0,
                    "stock_count": in_stock_alt.stock_count if in_stock_alt else 12
                } if in_stock_alt else None
            }

        elif failure_type in ["CATEGORY_BREACH", "CATEGORY_MISMATCH"] or (evaluation_result and not evaluation_result.passed and any("category" in v.lower() for v in evaluation_result.violations)):
            recovery_strategy = {
                "strategy": "CATEGORY_RESTRICTION_INTERCEPT",
                "reason": f"Requested item category '{attempted_item.get('category')}' is not in policy whitelist: {', '.join(policy.allowed_categories)}.",
                "recommended_action": "PROPOSE_WHITELISTED_COMPATIBLE_SUBSTITUTE",
                "suggested_action": "Switch to approved category or update policy whitelist",
                "whitelisted_alternatives": [
                    {"id": "nt_kb_01", "name": "KeyChron K2 Pro Mechanical Keyboard", "category": "Electronics", "price_inr": 3899.0},
                    {"id": "dd_kb_01", "name": "DevDesk Silent Pro 75%", "category": "Electronics", "price_inr": 2999.0}
                ]
            }

        elif failure_type in ["MERCHANT_API_DOWN", "TIMEOUT", "500_ERROR"]:
            recovery_strategy = {
                "strategy": "FEDERATED_MERCHANT_FAILOVER",
                "reason": "Primary merchant gateway returned 504 Gateway Timeout / 500 Internal Error during order initialization.",
                "recommended_action": "AUTO_FAILOVER_TO_MIRROR_MERCHANT",
                "failover_merchant": "DevDesk Supply Co.",
                "substitute_item": {
                    "id": "dd_kb_01",
                    "name": "DevDesk Silent Pro 75% Keyboard",
                    "merchant_name": "DevDesk Supply Co.",
                    "price_inr": 2999.0,
                    "status": "ONLINE_HEALTHY"
                }
            }

        elif failure_type in ["DUPLICATE_ORDER_REPLAY", "REPLAY_ATTACK"]:
            recovery_strategy = {
                "strategy": "IDEMPOTENCY_REPLAY_INTERCEPT",
                "reason": "Cryptographic nonce and idempotency key match an already processed transaction within 3600s TTL.",
                "recommended_action": "REJECT_DUPLICATE_EXECUTION",
                "details": "Prevented accidental double billing on Razorpay Rails. Returned existing order reference.",
                "original_order_id": attempted_item.get("order_id", "order_prev_verified")
            }

        audit_ledger.record(
            actor="FailureRecovery",
            action="RECOVERY_RESOLVED",
            status="RECOVERED",
            message=f"Graceful recovery plan formulated: {recovery_strategy.get('strategy')}",
            details=recovery_strategy
        )

        return recovery_strategy

failure_recovery = GracefulFailureRecovery()
