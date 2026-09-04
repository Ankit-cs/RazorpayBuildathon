import time
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class NegotiationBid(BaseModel):
    round_number: int
    speaker: str # "BuyerAgent", "NovaTech_Agent", "ByteForge_Agent", "DevDesk_Agent"
    target_merchant: Optional[str] = None
    action: str # "PROPOSAL", "COUNTER_OFFER", "CONCESSION", "FINAL_AGREEMENT", "REJECTED"
    message: str
    offered_price_inr: float
    shipping_cost_inr: float
    total_effective_inr: float
    perks: List[str]
    timestamp_offset_ms: int

class NegotiationSessionResult(BaseModel):
    session_id: str
    product_category: str
    budget_limit_inr: float
    initial_baseline_inr: float
    final_agreed_price_inr: float
    total_savings_inr: float
    savings_percentage: float
    winning_merchant: str
    winning_product_name: str
    rounds_exchanged: int
    dialogue_timeline: List[NegotiationBid]
    verdict_explanation: str
    popi_bound_satisfied: bool

class AgentNegotiationEngine:
    def __init__(self):
        pass

    def run_a2a_negotiation(
        self,
        query: str,
        budget_limit_inr: float = 4500.0,
        urgency_level: str = "NORMAL", # "NORMAL", "HIGH_URGENCY", "STRICT_BUDGET"
        preferred_category: str = "Electronics"
    ) -> NegotiationSessionResult:
        """
        Executes a 3-round visual Agent-to-Agent bargaining protocol across
        federated merchant agents on Razorpay rails.
        """
        session_id = f"neg_{uuid.uuid4().hex[:10]}"
        timeline: List[NegotiationBid] = []
        
        # Baseline prices
        nt_base = 3899.0
        bf_base = 3499.0
        dd_base = 2999.0

        # ROUND 1: Buyer Agent RFP broadcast
        timeline.append(NegotiationBid(
            round_number=1,
            speaker="BuyerAgent",
            target_merchant="ALL_MERCHANTS",
            action="PROPOSAL",
            message=f"Request for Quotes (RFQ): Seeking best delivered deal for '{query}'. Strict budget cap ₹{budget_limit_inr:,.2f}. Urgency: {urgency_level}.",
            offered_price_inr=budget_limit_inr,
            shipping_cost_inr=0.0,
            total_effective_inr=budget_limit_inr,
            perks=["Standard Policy Mandate"],
            timestamp_offset_ms=0
        ))

        # Round 1: Merchant Initial Quotes
        timeline.append(NegotiationBid(
            round_number=1,
            speaker="NovaTech_Agent",
            target_merchant="BuyerAgent",
            action="COUNTER_OFFER",
            message=f"Offering KeyChron K2 Pro Mechanical Keyboard at standard MSRP ₹{nt_base:,.2f} + ₹150 standard shipping.",
            offered_price_inr=nt_base,
            shipping_cost_inr=150.0,
            total_effective_inr=nt_base + 150.0,
            perks=["1-Year Replacement Warranty", "Gateron Brown Switches"],
            timestamp_offset_ms=280
        ))

        timeline.append(NegotiationBid(
            round_number=1,
            speaker="ByteForge_Agent",
            target_merchant="BuyerAgent",
            action="COUNTER_OFFER",
            message=f"Offering ByteForge TKL Board at ₹{bf_base:,.2f} + ₹199 Air Express delivery.",
            offered_price_inr=bf_base,
            shipping_cost_inr=199.0,
            total_effective_inr=bf_base + 199.0,
            perks=["24-Month Studio Care", "CNC Aluminum Frame"],
            timestamp_offset_ms=450
        ))

        timeline.append(NegotiationBid(
            round_number=1,
            speaker="DevDesk_Agent",
            target_merchant="BuyerAgent",
            action="COUNTER_OFFER",
            message=f"Offering DevDesk Silent Pro 75% at direct value price ₹{dd_base:,.2f} with 100% Free Shipping.",
            offered_price_inr=dd_base,
            shipping_cost_inr=0.0,
            total_effective_inr=dd_base,
            perks=["Zero Shipping Surcharge", "Hot-swap Silent Switches"],
            timestamp_offset_ms=620
        ))

        # ROUND 2: Buyer Agent Counter-Bid Pressure
        timeline.append(NegotiationBid(
            round_number=2,
            speaker="BuyerAgent",
            target_merchant="ALL_MERCHANTS",
            action="PROPOSAL",
            message="DevDesk is currently leading on total price (₹2,999). NovaTech & ByteForge: Can you match shipping fees or offer bundle concessions to win this enterprise order?",
            offered_price_inr=3200.0,
            shipping_cost_inr=0.0,
            total_effective_inr=3200.0,
            perks=["Instant Razorpay Settlement Guarantee"],
            timestamp_offset_ms=900
        ))

        # ROUND 2: Merchant Concessions
        # NovaTech drops price to ₹3,599 + waives shipping + adds coiled cable
        nt_concession_price = 3599.0
        timeline.append(NegotiationBid(
            round_number=2,
            speaker="NovaTech_Agent",
            target_merchant="BuyerAgent",
            action="CONCESSION",
            message=f"Concession Applied: We reduce KeyChron K2 Pro to ₹{nt_concession_price:,.2f}, waive shipping (FREE ₹0), and bundle a 50% off Custom Aviator Cable.",
            offered_price_inr=nt_concession_price,
            shipping_cost_inr=0.0,
            total_effective_inr=nt_concession_price,
            perks=["Waived Shipping (Saved ₹150)", "Discounted Cable Bundle", "Priority Dispatch"],
            timestamp_offset_ms=1250
        ))

        # ByteForge offers 24-hr Air Express free
        bf_concession_price = 3299.0
        timeline.append(NegotiationBid(
            round_number=2,
            speaker="ByteForge_Agent",
            target_merchant="BuyerAgent",
            action="CONCESSION",
            message=f"Counter Concession: Dropping to ₹{bf_concession_price:,.2f} with complimentary Air Express (24-hr delivery) and 2-year warranty.",
            offered_price_inr=bf_concession_price,
            shipping_cost_inr=0.0,
            total_effective_inr=bf_concession_price,
            perks=["Free Air Express (Saved ₹199)", "2-Year Warranty", "24-hr Delivery"],
            timestamp_offset_ms=1500
        ))

        # ROUND 3: Buyer Evaluation & Final Agreement Selection
        if urgency_level == "HIGH_URGENCY":
            winning_merchant = "ByteForge Electronics"
            winning_product = "ByteForge TKL Mechanical Board (Gateron Yellow)"
            final_price = bf_concession_price
            baseline = bf_base + 199.0
            rationale = "ByteForge won due to Free 24-Hour Air Express SLA matching high urgency constraint."
        elif urgency_level == "STRICT_BUDGET":
            winning_merchant = "DevDesk Supply Co."
            winning_product = "DevDesk Silent Pro 75% Keyboard (Silent Brown)"
            final_price = dd_base
            baseline = 3599.0
            rationale = "DevDesk won lowest absolute total landed cost (₹2,999) under strict budget mode."
        else: # Quality & Balance (Default)
            winning_merchant = "NovaTech Gear"
            winning_product = "KeyChron K2 Pro Mechanical Keyboard (Gateron Brown)"
            final_price = nt_concession_price
            baseline = nt_base + 150.0
            rationale = "NovaTech won optimal value: reduced price to ₹3,599, waived shipping, and included Gateron Brown switch preference."

        savings = baseline - final_price
        savings_pct = round((savings / baseline) * 100, 1) if baseline > 0 else 0.0

        timeline.append(NegotiationBid(
            round_number=3,
            speaker="BuyerAgent",
            target_merchant=winning_merchant,
            action="FINAL_AGREEMENT",
            message=f"CONTRACT AWARDED to {winning_merchant}! Final agreed price: ₹{final_price:,.2f} (Total savings: ₹{savings:,.2f} / {savings_pct}%). Preparing Razorpay test order.",
            offered_price_inr=final_price,
            shipping_cost_inr=0.0,
            total_effective_inr=final_price,
            perks=["Lock-in Agreed Price", "Razorpay Route Transfer Prepared"],
            timestamp_offset_ms=1800
        ))

        return NegotiationSessionResult(
            session_id=session_id,
            product_category=preferred_category,
            budget_limit_inr=budget_limit_inr,
            initial_baseline_inr=baseline,
            final_agreed_price_inr=final_price,
            total_savings_inr=savings,
            savings_percentage=savings_pct,
            winning_merchant=winning_merchant,
            winning_product_name=winning_product,
            rounds_exchanged=3,
            dialogue_timeline=timeline,
            verdict_explanation=rationale,
            popi_bound_satisfied=final_price <= budget_limit_inr
        )

negotiation_engine = AgentNegotiationEngine()
