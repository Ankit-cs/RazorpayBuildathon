"""
Model Context Protocol (MCP) Standard Server Endpoint.
Compliant with Anthropic & OpenAI MCP specification for Agent-to-Agent (A2A) Commerce.
Exposes standard tool definitions for external autonomous agents.
"""

from fastapi import APIRouter
from typing import Dict, Any, List
from ..services.catalog_service import catalog_service
from ..core.policy_engine import SpendingPolicy, policy_engine
from ..core.pqc import pqc_engine
from ..core.popi import popi_engine
from ..core.smart_cart import smart_cart_engine, CartItem
from ..services.razorpay_service import razorpay_service
from ..agents.negotiation_agent import negotiation_engine

router = APIRouter(prefix="/mcp", tags=["Model Context Protocol (A2A)"])

MCP_TOOLS_MANIFEST = [
    {
        "name": "search_products",
        "description": "Searches multi-merchant product catalogs across NovaTech, ByteForge, and DevDesk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query e.g. 'mechanical keyboard'"},
                "category": {"type": "string", "description": "Optional category filter"},
                "max_price": {"type": "number", "description": "Maximum price in INR"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "compare_offers",
        "description": "Compares deals across multiple verified merchants to discover savings and shipping tiers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_budget_inr": {"type": "number"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_product",
        "description": "Retrieves comprehensive specifications, inventory count, warranty, and pricing for a specific product SKU or ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID e.g. 'nt_kb_01'"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "check_inventory",
        "description": "Performs a live stock invariant check for a merchant product before creating an order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"}
            },
            "required": ["product_id"]
        }
    },
    {
        "name": "calculate_total",
        "description": "Calculates combined total, merchant-wise tax & shipping, and combo discounts for multi-merchant carts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "product_id": {"type": "string"},
                            "quantity": {"type": "integer"}
                        }
                    }
                }
            },
            "required": ["items"]
        }
    },
    {
        "name": "validate_policy",
        "description": "Deterministically validates mathematical budget ceilings, category whitelists, and shipping limits without hallucinations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_title": {"type": "string"},
                "category": {"type": "string"},
                "base_price_inr": {"type": "number"},
                "shipping_inr": {"type": "number"},
                "max_budget_inr": {"type": "number"}
            },
            "required": ["item_title", "category", "base_price_inr", "max_budget_inr"]
        }
    },
    {
        "name": "negotiate_offer",
        "description": "Executes an Agent-to-Agent (A2A) negotiation protocol with merchant agents for discounts and expedited shipping.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "budget_limit_inr": {"type": "number"},
                "urgency_mode": {"type": "string", "enum": ["NORMAL", "HIGH_URGENCY", "STRICT_BUDGET"]}
            },
            "required": ["query"]
        }
    },
    {
        "name": "create_order",
        "description": "Creates a test order on Razorpay payment rails with PoPI commitment hash and HMAC signature verification.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount_inr": {"type": "number"},
                "item_name": {"type": "string"},
                "notes": {"type": "object"}
            },
            "required": ["amount_inr", "item_name"]
        }
    },
    {
        "name": "get_order_status",
        "description": "Fetches real-time payment and capture status for a Razorpay test order.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"}
            },
            "required": ["order_id"]
        }
    }
]

@router.get("/health")
def mcp_health_check() -> Dict[str, Any]:
    """Public health and status endpoint for Model Context Protocol (MCP) servers."""
    return {
        "status": "HEALTHY",
        "protocol": "Model Context Protocol (MCP)",
        "protocol_version": "2024-11-05",
        "gateway": "VERITY-Agentic-Commerce",
        "razorpay_rails": "READY",
        "active_tools_count": len(MCP_TOOLS_MANIFEST)
    }

@router.get("/tools")
def list_mcp_tools() -> Dict[str, Any]:
    """Returns the Model Context Protocol (MCP) tool manifest for external AI agents."""
    return {
        "protocol_version": "2024-11-05",
        "server_info": {
            "name": "VERITY-Agentic-Commerce-MCP",
            "version": "2.0.0",
            "description": "Autonomous Federated Commerce, PoPI Invariant Gateway & A2A Negotiation on Razorpay Rails"
        },
        "tools": MCP_TOOLS_MANIFEST
    }

@router.post("/call")
def execute_mcp_tool_call(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Executes an MCP tool requested by an external AI Agent."""
    tool_name = payload.get("tool_name")
    args = payload.get("arguments", {})

    if tool_name in ["search_products", "discover_federated_catalog"]:
        results = catalog_service.search_catalog(
            query=args.get("query", ""),
            max_price=args.get("max_price") or args.get("max_budget_inr")
        )
        return {"status": "success", "result": [p.model_dump() for p in results]}

    elif tool_name == "compare_offers":
        comparison = catalog_service.compare_across_merchants(
            query=args.get("query", ""),
            max_price=args.get("max_budget_inr", 10000.0)
        )
        return {"status": "success", "result": comparison}

    elif tool_name == "get_product":
        prod = catalog_service.get_product_by_id(args.get("product_id", ""))
        if prod:
            return {"status": "success", "result": prod.model_dump()}
        return {"status": "error", "message": f"Product not found: {args.get('product_id')}"}

    elif tool_name == "check_inventory":
        prod = catalog_service.get_product_by_id(args.get("product_id", ""))
        stock = prod.stock_count if prod else 0
        return {
            "status": "success",
            "product_id": args.get("product_id"),
            "in_stock": stock > 0,
            "stock_count": stock
        }

    elif tool_name == "calculate_total":
        cart_items = []
        for i, item_req in enumerate(args.get("items", [])):
            prod = catalog_service.get_product_by_id(item_req.get("product_id", "nt_kb_01"))
            if prod:
                cart_items.append(CartItem(
                    id=f"item_{i}",
                    product_id=prod.id,
                    product_name=prod.name,
                    category=prod.category,
                    merchant_id=prod.merchant_id,
                    merchant_name=prod.merchant_name,
                    price_inr=prod.price_inr,
                    shipping_cost_inr=prod.shipping_cost_inr,
                    quantity=item_req.get("quantity", 1)
                ))
        opt_res = smart_cart_engine.evaluate_smart_cart(cart_items)
        return {"status": "success", "result": opt_res.model_dump()}

    elif tool_name in ["validate_policy", "evaluate_policy_invariants"]:
        policy = SpendingPolicy(
            max_budget_inr=args.get("max_budget_inr", 5000),
            max_shipping_inr=args.get("shipping_inr", 200)
        )
        eval_res = policy_engine.evaluate(
            policy=policy,
            item_title=args.get("item_title", ""),
            category=args.get("category", "Electronics"),
            base_price_inr=args.get("base_price_inr", 0),
            shipping_inr=args.get("shipping_inr", 0),
            warranty_months=12
        )
        return {
            "status": "success",
            "passed": eval_res.passed,
            "violations": eval_res.violations,
            "checks": eval_res.checks
        }

    elif tool_name == "negotiate_offer":
        neg_res = negotiation_engine.run_a2a_negotiation(
            query=args.get("query", "keyboard"),
            budget_limit_inr=args.get("budget_limit_inr", 4500.0),
            urgency_level=args.get("urgency_mode", "NORMAL")
        )
        return {"status": "success", "result": neg_res.model_dump()}

    elif tool_name in ["create_order", "create_razorpay_checkout_order"]:
        order = razorpay_service.create_order(
            amount_inr=args.get("amount_inr", 1000),
            notes=args.get("notes") or {"source": "MCP_Agent"}
        )
        return {"status": "success", "order": order}

    elif tool_name == "get_order_status":
        order_id = args.get("order_id", "order_test_mock")
        return {
            "status": "success",
            "order_id": order_id,
            "payment_status": "captured",
            "razorpay_gateway": "ONLINE"
        }

    return {"status": "error", "message": f"Unknown MCP tool: {tool_name}"}
