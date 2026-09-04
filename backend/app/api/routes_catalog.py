from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional, Dict, Any
from ..services.catalog_service import catalog_service, Product

router = APIRouter(prefix="/catalog", tags=["Merchant Catalog"])

@router.get("/products", response_model=List[Product])
def get_products(merchant_id: Optional[str] = Query(None)):
    """Returns product inventory, optionally filtered by merchant."""
    return catalog_service.get_all_products(merchant_id=merchant_id)

@router.get("/products/{product_id}", response_model=Product)
def get_product_by_id(product_id: str):
    product = catalog_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.get("/merchants")
def get_merchants():
    """Lists all registered merchants on the platform."""
    return catalog_service.get_merchants()

@router.get("/compare")
def compare_across_merchants(
    query: str = Query(..., description="Product search query"),
    max_price: Optional[float] = Query(None, description="Max price filter")
):
    """Compares products across all merchants for best deal discovery."""
    return catalog_service.compare_across_merchants(query, max_price)

@router.get("/agent-schema")
def get_agent_readable_mcp_schema() -> Dict[str, Any]:
    return {
        "name": "razorpay_multi_merchant_storefront",
        "description": "Agent-readable multi-merchant catalog with cross-merchant comparison on Razorpay",
        "merchants": catalog_service.get_merchants(),
        "tools": [
            {
                "name": "search_products",
                "description": "Searches all merchant inventories with fuzzy matching and budget constraints",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query like 'keyboard', 'headphones'"},
                        "max_budget_inr": {"type": "number", "description": "Maximum price ceiling"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "compare_merchants",
                "description": "Compares the same product across all merchants to find the best deal",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "max_budget_inr": {"type": "number"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_bounded_checkout",
                "description": "Evaluates policy invariants and creates a Razorpay Order ID for verified purchasing",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_id": {"type": "string"},
                        "max_budget_inr": {"type": "number"},
                        "include_upsell": {"type": "boolean"}
                    },
                    "required": ["product_id", "max_budget_inr"]
                }
            }
        ]
    }

@router.post("/simulate-drift")
def simulate_drift(drift_type: Optional[str] = Query(None)):
    catalog_service.set_drift_simulation(drift_type)
    return {"status": "ok", "active_drift": drift_type}

@router.post("/reset")
def reset_catalog():
    catalog_service.reset_catalog()
    return {"status": "ok", "message": "Catalog reset to defaults."}
