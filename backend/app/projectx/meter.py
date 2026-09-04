from typing import List, Dict, Any
from pydantic import BaseModel
from .ledger import LedgerEvent

class ModelAssumptions(BaseModel):
    name: str
    inputUsdPer1M: float
    outputUsdPer1M: float

class Assumptions(BaseModel):
    mdrPct: float
    model: ModelAssumptions
    usdToInr: float
    projectionPaymentsPerMonth: int

ASSUMPTIONS = Assumptions(
    mdrPct=2.0,
    model=ModelAssumptions(name="gpt-4o-mini-class (assumed)", inputUsdPer1M=0.15, outputUsdPer1M=0.6),
    usdToInr=83,
    projectionPaymentsPerMonth=1_000_000
)

class MeterSnapshot(BaseModel):
    gmvPaise: int
    capturedCount: int
    refusedCount: int
    attackCount: int
    refusalRate: float
    tokensIn: int
    tokensOut: int
    aiCostPaise: int
    channelRevenuePaise: int
    netPaise: int
    aiCostPerCapturedPaise: int
    assumptions: Assumptions

def meter_from_events(events: List[LedgerEvent]) -> MeterSnapshot:
    gmv_paise = 0
    captured_count = 0
    refused_count = 0
    attack_count = 0
    tokens_in = 0
    tokens_out = 0
    
    for e in events:
        d = e.data if isinstance(e.data, dict) else {}
        if e.type == "payment.captured":
            gmv_paise += d.get("totalPaise", 0)
            captured_count += 1
        elif e.type == "gate.decision" and d.get("kind") == "REFUSE":
            buyer = str(d.get("buyerId", ""))
            is_attack = buyer.startswith("attacker") or buyer.startswith("fuzz-")
            if not is_attack:
                refused_count += 1
        elif e.type == "attack.blocked":
            attack_count += 1
        elif e.type == "span":
            attrs = d.get("attrs", {})
            tokens_in += attrs.get("tokensIn", 0)
            tokens_out += attrs.get("tokensOut", 0)
            
    ai_cost_usd = (tokens_in / 1_000_000) * ASSUMPTIONS.model.inputUsdPer1M + (tokens_out / 1_000_000) * ASSUMPTIONS.model.outputUsdPer1M
    ai_cost_paise = round(ai_cost_usd * ASSUMPTIONS.usdToInr * 100)
    channel_revenue_paise = round((gmv_paise * ASSUMPTIONS.mdrPct) / 100)
    net_paise = channel_revenue_paise - ai_cost_paise
    
    decisions = captured_count + refused_count
    
    return MeterSnapshot(
        gmvPaise=gmv_paise,
        capturedCount=captured_count,
        refusedCount=refused_count,
        attackCount=attack_count,
        refusalRate=0.0 if decisions == 0 else refused_count / decisions,
        tokensIn=tokens_in,
        tokensOut=tokens_out,
        aiCostPaise=ai_cost_paise,
        channelRevenuePaise=channel_revenue_paise,
        netPaise=net_paise,
        aiCostPerCapturedPaise=0 if captured_count == 0 else round(ai_cost_paise / captured_count),
        assumptions=ASSUMPTIONS
    )

def project_at_scale(snapshot: MeterSnapshot) -> Dict[str, Any]:
    n = ASSUMPTIONS.projectionPaymentsPerMonth
    avg_ticket_paise = 0 if snapshot.capturedCount == 0 else round(snapshot.gmvPaise / snapshot.capturedCount)
    cost_per_payment = snapshot.aiCostPerCapturedPaise
    
    revenue_inr_per_month = round(((avg_ticket_paise * n * ASSUMPTIONS.mdrPct) / 100) / 100)
    ai_cost_inr_per_month = round((cost_per_payment * n) / 100)
    
    return {
        "paymentsPerMonth": n,
        "avgTicketPaise": avg_ticket_paise,
        "revenueInrPerMonth": revenue_inr_per_month,
        "aiCostInrPerMonth": ai_cost_inr_per_month,
        "netInrPerMonth": revenue_inr_per_month - ai_cost_inr_per_month,
        "formula": "revenue = avgTicket × N × MDR% ; aiCost = measured ₹/captured-payment × N ; net = revenue − aiCost",
        "assumptions": ASSUMPTIONS.model_dump()
    }
