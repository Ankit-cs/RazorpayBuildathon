from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .audit_ledger import audit_ledger

class SpendingPolicy(BaseModel):
    max_budget_inr: float = Field(default=5000.0, description="Upper monetary ceiling in INR")
    max_shipping_inr: float = Field(default=250.0, description="Max allowed shipping cost")
    allowed_categories: List[str] = Field(default=["Electronics", "Accessories", "Peripherals", "Developer Gear"])
    require_warranty: bool = Field(default=False, description="Require minimum 6 months warranty")
    allow_bundle_upsell: bool = Field(default=True, description="Allow merchants to propose discounted bundles")
    auto_approve_threshold_pct: float = Field(default=100.0, description="Auto-approve if total <= 100% of max budget")

class InvariantEvaluationResult(BaseModel):
    passed: bool
    violations: List[str] = []
    checks: Dict[str, Any] = {}
    explanation: str

class PolicyEngine:
    @staticmethod
    def evaluate(
        policy: SpendingPolicy,
        item_title: str,
        category: str,
        base_price_inr: float,
        shipping_inr: float,
        warranty_months: int = 0,
        bundle_applied: bool = False
    ) -> InvariantEvaluationResult:
        total_amount = base_price_inr + shipping_inr
        violations = []
        checks = {}

        # 1. Check Total Budget Invariant
        budget_passed = total_amount <= policy.max_budget_inr
        checks["budget_check"] = {
            "total_amount": total_amount,
            "max_budget": policy.max_budget_inr,
            "passed": budget_passed,
            "variance": total_amount - policy.max_budget_inr
        }
        if not budget_passed:
            violations.append(
                f"Budget Invariant Breach: Total amount ₹{total_amount:,.2f} exceeds ceiling of ₹{policy.max_budget_inr:,.2f} by ₹{total_amount - policy.max_budget_inr:,.2f}"
            )

        # 2. Check Shipping Invariant
        shipping_passed = shipping_inr <= policy.max_shipping_inr
        checks["shipping_check"] = {
            "shipping_cost": shipping_inr,
            "max_shipping": policy.max_shipping_inr,
            "passed": shipping_passed
        }
        if not shipping_passed:
            violations.append(
                f"Shipping Cap Breach: Shipping ₹{shipping_inr} exceeds allowed max of ₹{policy.max_shipping_inr}"
            )

        # 3. Check Category Whitelist Invariant
        category_passed = any(cat.lower() in category.lower() for cat in policy.allowed_categories)
        checks["category_check"] = {
            "category": category,
            "allowed_categories": policy.allowed_categories,
            "passed": category_passed
        }
        if not category_passed:
            violations.append(
                f"Category Whitelist Breach: '{category}' is not in authorized categories ({', '.join(policy.allowed_categories)})"
            )

        # 4. Check Warranty Invariant (if required)
        warranty_passed = True
        if policy.require_warranty:
            warranty_passed = warranty_months >= 6
            checks["warranty_check"] = {
                "warranty_months": warranty_months,
                "required_months": 6,
                "passed": warranty_passed
            }
            if not warranty_passed:
                violations.append(
                    f"Warranty Requirement Breach: Item provides {warranty_months}m warranty (min 6m required)"
                )

        all_passed = len(violations) == 0

        explanation = (
            f"All {len(checks)} policy invariants satisfied. Total: ₹{total_amount:,.2f} within ₹{policy.max_budget_inr:,.2f} budget."
            if all_passed
            else f"Policy evaluation failed with {len(violations)} invariant breach(es)."
        )

        audit_ledger.record(
            actor="PolicyEngine",
            action="POLICY_EVALUATION",
            status="SUCCESS" if all_passed else "VIOLATION",
            message=explanation,
            details={
                "item": item_title,
                "total_inr": total_amount,
                "checks": checks,
                "violations": violations
            },
            invariants_passed=all_passed
        )

        return InvariantEvaluationResult(
            passed=all_passed,
            violations=violations,
            checks=checks,
            explanation=explanation
        )

policy_engine = PolicyEngine()
