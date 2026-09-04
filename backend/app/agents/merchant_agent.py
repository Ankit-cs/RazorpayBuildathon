from typing import List, Dict, Any, Optional
from ..services.catalog_service import catalog_service, Product
from ..core.audit_ledger import audit_ledger

class MerchantAgent:
    def __init__(self):
        self.name = "MerchantCommerceAgent"

    def process_buyer_inquiry(
        self,
        query: str,
        max_budget: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Queries ALL merchant catalogs, compares prices, and returns the best-deal quote.
        """
        audit_ledger.record(
            actor="MerchantAgent",
            action="MULTI_MERCHANT_SEARCH",
            status="INFO",
            message=f"Searching across all merchants: '{query}' (budget: ₹{max_budget or 'N/A'})",
            details={"query": query, "max_budget": max_budget}
        )

        # Cross-merchant comparison
        comparison = catalog_service.compare_across_merchants(query, max_budget)

        # Log comparison results
        if comparison["merchants_compared"] > 0:
            audit_ledger.record(
                actor="MerchantAgent",
                action="COMPARISON_COMPLETE",
                status="SUCCESS",
                message=f"Compared {comparison['merchants_compared']} merchants. Best deal: {comparison['best_deal']['merchant_name']} (Savings: ₹{comparison['savings_vs_worst']})",
                details={
                    "merchants_compared": comparison["merchants_compared"],
                    "savings_vs_worst": comparison["savings_vs_worst"],
                    "best_merchant": comparison["best_deal"]["merchant_name"] if comparison["best_deal"] else None
                }
            )

        # If no results from comparison, fall back to first available
        if not comparison["best_deal"]:
            all_products = catalog_service.get_all_products()
            if not all_products:
                return self._empty_quote()
            selected = all_products[0]
        else:
            selected_data = comparison["best_deal"]["product"]
            selected = catalog_service.get_product(selected_data["id"])
            if not selected:
                selected = catalog_service.get_all_products()[0]

        proposal = {
            "merchant_name": selected.merchant_name,
            "merchant_id": selected.merchant_id,
            "product_id": selected.id,
            "product_name": selected.name,
            "sku": selected.sku,
            "category": selected.category,
            "price_inr": selected.price_inr,
            "original_price_inr": selected.original_price_inr,
            "stock_count": selected.stock_count,
            "shipping_tier": selected.shipping_tier,
            "shipping_cost_inr": selected.shipping_cost_inr,
            "warranty_months": selected.warranty_months,
            "specs": selected.specs,
            "rating": selected.rating,
            "bundle_opportunity": None,
            "comparison_summary": comparison
        }

        if selected.upsell_bundle:
            bundle = selected.upsell_bundle
            bundled_total = selected.price_inr + bundle["bundle_price_inr"] + selected.shipping_cost_inr
            proposal["bundle_opportunity"] = {
                **bundle,
                "bundled_total_inr": bundled_total,
                "value_proposition": f"Special 50% discount on {bundle['name']} when purchased together"
            }

        audit_ledger.record(
            actor="MerchantAgent",
            action="BEST_DEAL_SELECTED",
            status="SUCCESS",
            message=f"Selected {selected.name} from {selected.merchant_name}: ₹{selected.price_inr:,.2f} + Ship ₹{selected.shipping_cost_inr}",
            details=proposal
        )

        return proposal

    def _empty_quote(self) -> Dict[str, Any]:
        return {
            "merchant_name": "N/A",
            "merchant_id": "",
            "product_id": "",
            "product_name": "No matching products",
            "sku": "",
            "category": "",
            "price_inr": 0,
            "original_price_inr": 0,
            "stock_count": 0,
            "shipping_tier": "N/A",
            "shipping_cost_inr": 0,
            "warranty_months": 0,
            "specs": {},
            "rating": 0,
            "bundle_opportunity": None,
            "comparison_summary": None
        }

merchant_agent = MerchantAgent()
