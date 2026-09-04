import uuid
import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CartItem(BaseModel):
    id: str
    product_id: str
    product_name: str
    category: str
    merchant_id: str
    merchant_name: str
    price_inr: float
    shipping_cost_inr: float
    quantity: int = 1
    warranty_months: int = 12
    bundle_selected: bool = False
    bundle_item_name: Optional[str] = None
    bundle_price_inr: float = 0.0

class MerchantCartGroup(BaseModel):
    merchant_id: str
    merchant_name: str
    account_id: str
    items: List[CartItem]
    subtotal_inr: float
    shipping_inr: float
    merchant_total_inr: float
    estimated_delivery_days: int
    split_transfer_share_pct: float

class SplitSettlementTransfer(BaseModel):
    account_id: str
    merchant_name: str
    amount_inr: float
    amount_paise: int
    currency: str = "INR"
    platform_fee_inr: float
    net_transfer_inr: float

class SmartCartOptimizationResult(BaseModel):
    cart_id: str
    total_items_count: int
    grand_subtotal_inr: float
    grand_shipping_inr: float
    combo_discount_inr: float
    final_payable_inr: float
    merchant_breakdown: List[MerchantCartGroup]
    split_transfers: List[SplitSettlementTransfer]
    recommended_strategy: str
    cost_optimized_plan: Dict[str, Any]
    speed_optimized_plan: Dict[str, Any]
    savings_vs_individual_inr: float

class SmartCartEngine:
    def __init__(self):
        self.merchant_accounts = {
            "merchant_novatech": {"name": "NovaTech Gear", "acc_id": "acc_rzp_novatech_blr"},
            "merchant_byteforge": {"name": "ByteForge Electronics", "acc_id": "acc_rzp_byteforge_hyd"},
            "merchant_devdesk": {"name": "DevDesk Supply Co.", "acc_id": "acc_rzp_devdesk_del"}
        }

    def evaluate_smart_cart(self, items: List[CartItem]) -> SmartCartOptimizationResult:
        """
        Calculates merchant-wise groups, consolidated shipping discounts,
        Razorpay Route sub-account split transfers, and optimization strategies.
        """
        cart_id = f"cart_{uuid.uuid4().hex[:10]}"
        
        # Group items by merchant
        merchant_groups_map: Dict[str, List[CartItem]] = {}
        for item in items:
            m_id = item.merchant_id
            if m_id not in merchant_groups_map:
                merchant_groups_map[m_id] = []
            merchant_groups_map[m_id].append(item)

        merchant_groups: List[MerchantCartGroup] = []
        raw_subtotal = 0.0
        raw_shipping = 0.0

        for m_id, m_items in merchant_groups_map.items():
            acc_info = self.merchant_accounts.get(m_id, {"name": m_items[0].merchant_name, "acc_id": f"acc_rzp_{m_id}"})
            
            subtotal = sum((item.price_inr + (item.bundle_price_inr if item.bundle_selected else 0.0)) * item.quantity for item in m_items)
            
            # Shipping calculation with merchant bundle discount:
            # If multiple items from same merchant, consolidate shipping (pay max shipping once + ₹50 for extra items)
            base_shipping = max(item.shipping_cost_inr for item in m_items) if m_items else 0.0
            if len(m_items) > 1:
                consolidated_shipping = base_shipping + (len(m_items) - 1) * 30.0
            else:
                consolidated_shipping = base_shipping

            # Free shipping threshold per merchant
            if subtotal >= 4000.0:
                consolidated_shipping = 0.0

            m_total = subtotal + consolidated_shipping
            raw_subtotal += subtotal
            raw_shipping += consolidated_shipping

            delivery_days = 2 if "byteforge" in m_id else (3 if "novatech" in m_id else 4)

            merchant_groups.append(MerchantCartGroup(
                merchant_id=m_id,
                merchant_name=acc_info["name"],
                account_id=acc_info["acc_id"],
                items=m_items,
                subtotal_inr=subtotal,
                shipping_inr=consolidated_shipping,
                merchant_total_inr=m_total,
                estimated_delivery_days=delivery_days,
                split_transfer_share_pct=0.0 # Will calculate below
            ))

        # Overall Multi-Merchant Cross-Cart Combo Discount (5% if >= 2 items)
        combo_discount = round(raw_subtotal * 0.05, 2) if len(items) >= 2 else 0.0
        final_payable = round(raw_subtotal + raw_shipping - combo_discount, 2)

        # Calculate Razorpay Route Split Transfers
        split_transfers: List[SplitSettlementTransfer] = []
        for g in merchant_groups:
            if final_payable > 0:
                g.split_transfer_share_pct = round((g.merchant_total_inr / (raw_subtotal + raw_shipping)) * 100, 1)
            
            # 2% platform facilitation fee
            platform_fee = round(g.merchant_total_inr * 0.02, 2)
            net_transfer = round(g.merchant_total_inr - platform_fee, 2)

            split_transfers.append(SplitSettlementTransfer(
                account_id=g.account_id,
                merchant_name=g.merchant_name,
                amount_inr=g.merchant_total_inr,
                amount_paise=int(round(g.merchant_total_inr * 100)),
                platform_fee_inr=platform_fee,
                net_transfer_inr=net_transfer
            ))

        # Cost Optimized Plan
        cost_plan = {
            "plan_name": "Cost-Minimized Multi-Merchant Routing",
            "total_inr": final_payable,
            "savings_inr": combo_discount + 120.0,
            "avg_delivery_days": max([g.estimated_delivery_days for g in merchant_groups]) if merchant_groups else 3,
            "description": f"Splits across {len(merchant_groups)} merchants to capture lowest unit prices + ₹{combo_discount} multi-item discount."
        }

        # Speed Optimized Plan
        speed_plan = {
            "plan_name": "Air-Express Priority Dispatch",
            "total_inr": round(final_payable + 199.0, 2),
            "savings_inr": 0.0,
            "avg_delivery_days": 1,
            "description": "Consolidates priority routing with 24-hr Air Express SLA dispatch."
        }

        return SmartCartOptimizationResult(
            cart_id=cart_id,
            total_items_count=sum(i.quantity for i in items),
            grand_subtotal_inr=raw_subtotal,
            grand_shipping_inr=raw_shipping,
            combo_discount_inr=combo_discount,
            final_payable_inr=final_payable,
            merchant_breakdown=merchant_groups,
            split_transfers=split_transfers,
            recommended_strategy="COST_OPTIMIZED",
            cost_optimized_plan=cost_plan,
            speed_optimized_plan=speed_plan,
            savings_vs_individual_inr=combo_discount + (len(items) * 50.0)
        )

smart_cart_engine = SmartCartEngine()
