from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Product(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    description: str
    price_inr: float
    original_price_inr: float
    stock_count: int
    shipping_tier: str
    shipping_cost_inr: float
    warranty_months: int
    tags: List[str]
    specs: Dict[str, str]
    upsell_bundle: Optional[Dict[str, Any]] = None
    rating: float = 4.8
    merchant_id: str = "merchant_novatech"
    merchant_name: str = "NovaTech Gear"

# ─── Merchant 1: NovaTech Gear ───
NOVATECH_PRODUCTS = [
    Product(
        id="nt_kb_01", sku="NT-KB-PRO-BROWN",
        name="KeyChron K2 Pro Mechanical Keyboard (Gateron Brown)",
        category="Electronics",
        description="Hot-swappable wireless mechanical keyboard with tactile brown switches, RGB backlight, and Mac/Windows layout.",
        price_inr=3899.0, original_price_inr=4499.0, stock_count=14,
        shipping_tier="Standard", shipping_cost_inr=150.0, warranty_months=12,
        tags=["keyboard", "mechanical", "coding", "brown switches", "wireless"],
        specs={"Switches": "Gateron Brown", "Connectivity": "Bluetooth 5.1 / Type-C", "Battery": "4000mAh"},
        upsell_bundle={
            "bundle_id": "bnd_kb_wrist", "name": "Ergonomic Walnut Palm Rest + Keycap Puller",
            "bundle_price_inr": 499.0, "original_bundle_price": 999.0, "discount_pct": 50
        },
        merchant_id="merchant_novatech", merchant_name="NovaTech Gear"
    ),
    Product(
        id="nt_kb_02", sku="NT-KB-COMPACT-RED",
        name="Apex 60% Linear Red Gaming/Typing Keyboard",
        category="Electronics",
        description="Ultra-compact 60% mechanical keyboard with quiet linear red switches and PBT keycaps.",
        price_inr=2499.0, original_price_inr=2999.0, stock_count=22,
        shipping_tier="Standard", shipping_cost_inr=100.0, warranty_months=12,
        tags=["keyboard", "mechanical", "red switches", "compact", "silent"],
        specs={"Switches": "Linear Red", "Size": "60% Compact", "Weight": "650g"},
        upsell_bundle={
            "bundle_id": "bnd_coiled_cable", "name": "Custom Aviator Coiled Type-C Cable",
            "bundle_price_inr": 350.0, "original_bundle_price": 700.0, "discount_pct": 50
        },
        merchant_id="merchant_novatech", merchant_name="NovaTech Gear"
    ),
    Product(
        id="nt_anc_01", sku="NT-ANC-FLOW-X",
        name="AuraSound Flow ANC Developer Headphones",
        category="Electronics",
        description="Active Noise Cancelling over-ear headphones with 40mm drivers, multipoint pairing, and ultra-low latency.",
        price_inr=4499.0, original_price_inr=5999.0, stock_count=8,
        shipping_tier="Free", shipping_cost_inr=0.0, warranty_months=12,
        tags=["headphones", "audio", "anc", "noise cancelling", "bluetooth"],
        specs={"ANC Depth": "38dB", "Playtime": "45 Hours", "Codecs": "AAC, LDAC, SBC"},
        upsell_bundle={
            "bundle_id": "bnd_hard_case", "name": "EVA Hard Travel Case & Hangar",
            "bundle_price_inr": 299.0, "original_bundle_price": 599.0, "discount_pct": 50
        },
        merchant_id="merchant_novatech", merchant_name="NovaTech Gear"
    ),
    Product(
        id="nt_dock_01", sku="NT-DOCK-11IN1",
        name="NovaHub 11-in-1 Dual 4K USB-C Docking Station",
        category="Peripherals",
        description="High-speed docking hub with 100W Power Delivery, Dual HDMI 4K@60Hz, Gigabit Ethernet, and SD card reader.",
        price_inr=3299.0, original_price_inr=3999.0, stock_count=19,
        shipping_tier="Standard", shipping_cost_inr=120.0, warranty_months=24,
        tags=["dock", "hub", "usb-c", "dual monitor", "macbook", "workstation"],
        specs={"Ports": "11 (2x HDMI, 3x USB 3.0, 1x RJ45, 1x PD 100W)", "Material": "Aluminum Alloy"},
        merchant_id="merchant_novatech", merchant_name="NovaTech Gear"
    ),
    Product(
        id="nt_desk_01", sku="NT-DESK-MAT-XL",
        name="HyperGlide Merino Felt & Leather Desk Pad (90x40cm)",
        category="Accessories",
        description="Premium waterproof vegan leather desk mat with anti-slip suede base and stitched borders.",
        price_inr=899.0, original_price_inr=1299.0, stock_count=45,
        shipping_tier="Standard", shipping_cost_inr=80.0, warranty_months=6,
        tags=["desk mat", "leather", "mouse pad", "workspace", "ergonomics"],
        specs={"Dimensions": "900mm x 400mm x 3mm", "Surface": "Water-resistant Vegan Leather"},
        merchant_id="merchant_novatech", merchant_name="NovaTech Gear"
    )
]

# ─── Merchant 2: ByteForge Electronics ───
BYTEFORGE_PRODUCTS = [
    Product(
        id="bf_kb_01", sku="BF-KB-GATERON-Y",
        name="ByteForge TKL Mechanical Board (Gateron Yellow)",
        category="Electronics",
        description="Tenkeyless mechanical keyboard with smooth linear Gateron Yellow switches, aluminum frame, USB-C.",
        price_inr=3499.0, original_price_inr=3999.0, stock_count=18,
        shipping_tier="Express", shipping_cost_inr=199.0, warranty_months=18,
        tags=["keyboard", "mechanical", "coding", "yellow switches", "tkl"],
        specs={"Switches": "Gateron Yellow (Linear)", "Layout": "TKL 87-key", "Frame": "CNC Aluminum"},
        upsell_bundle={
            "bundle_id": "bf_bnd_wrist", "name": "Memory Foam Wrist Rest + Cleaning Kit",
            "bundle_price_inr": 399.0, "original_bundle_price": 799.0, "discount_pct": 50
        },
        merchant_id="merchant_byteforge", merchant_name="ByteForge Electronics", rating=4.6
    ),
    Product(
        id="bf_anc_01", sku="BF-ANC-STUDIO",
        name="ByteForge Studio ANC Pro Headphones",
        category="Electronics",
        description="Audiophile-grade ANC headphones with 50mm planar drivers, aptX HD, 60-hour battery life.",
        price_inr=3999.0, original_price_inr=5499.0, stock_count=12,
        shipping_tier="Free", shipping_cost_inr=0.0, warranty_months=24,
        tags=["headphones", "audio", "anc", "noise cancelling", "studio", "planar"],
        specs={"ANC Depth": "42dB", "Playtime": "60 Hours", "Codecs": "aptX HD, AAC, LDAC"},
        upsell_bundle={
            "bundle_id": "bf_bnd_dac", "name": "Portable USB-C DAC Amplifier",
            "bundle_price_inr": 599.0, "original_bundle_price": 1199.0, "discount_pct": 50
        },
        merchant_id="merchant_byteforge", merchant_name="ByteForge Electronics", rating=4.9
    ),
    Product(
        id="bf_dock_01", sku="BF-DOCK-TRIPLE",
        name="ByteForge TripleView 14-in-1 Dock (Triple 4K)",
        category="Peripherals",
        description="Triple-display docking station with 3x HDMI 4K@60Hz, 130W PD, NVMe SSD slot, Gigabit LAN.",
        price_inr=4299.0, original_price_inr=5299.0, stock_count=6,
        shipping_tier="Express", shipping_cost_inr=149.0, warranty_months=24,
        tags=["dock", "hub", "usb-c", "triple monitor", "nvme", "workstation"],
        specs={"Ports": "14 (3x HDMI, 4x USB 3.2, NVMe, RJ45, PD 130W)", "Material": "Titanium Alloy"},
        merchant_id="merchant_byteforge", merchant_name="ByteForge Electronics", rating=4.7
    )
]

# ─── Merchant 3: DevDesk Supply Co. ───
DEVDESK_PRODUCTS = [
    Product(
        id="dd_kb_01", sku="DD-KB-SILENT-BLK",
        name="DevDesk Silent Pro 75% Keyboard (Silent Brown)",
        category="Electronics",
        description="Office-quiet 75% layout with silent brown tactile switches, hot-swap sockets, and multi-device Bluetooth.",
        price_inr=2999.0, original_price_inr=3599.0, stock_count=30,
        shipping_tier="Free", shipping_cost_inr=0.0, warranty_months=12,
        tags=["keyboard", "mechanical", "coding", "silent", "office", "75%"],
        specs={"Switches": "Silent Brown (Tactile)", "Layout": "75% Compact", "Connectivity": "BT 5.2 / USB-C"},
        upsell_bundle={
            "bundle_id": "dd_bnd_mat", "name": "Matching Desk Mat + Cable Organizer",
            "bundle_price_inr": 449.0, "original_bundle_price": 899.0, "discount_pct": 50
        },
        merchant_id="merchant_devdesk", merchant_name="DevDesk Supply Co.", rating=4.5
    ),
    Product(
        id="dd_anc_01", sku="DD-ANC-FOCUS",
        name="DevDesk Focus Zone ANC Earbuds",
        category="Electronics",
        description="True wireless ANC earbuds optimized for voice calls with 6-mic array and transparency mode.",
        price_inr=2499.0, original_price_inr=3299.0, stock_count=25,
        shipping_tier="Free", shipping_cost_inr=0.0, warranty_months=12,
        tags=["headphones", "earbuds", "anc", "bluetooth", "tws", "calls"],
        specs={"ANC Depth": "32dB", "Playtime": "32 Hours", "Mics": "6-Mic ENC Array"},
        merchant_id="merchant_devdesk", merchant_name="DevDesk Supply Co.", rating=4.3
    ),
    Product(
        id="dd_dock_01", sku="DD-DOCK-SLIM-7",
        name="DevDesk SlimHub 7-in-1 Travel Dock",
        category="Peripherals",
        description="Compact portable travel hub with 4K HDMI, 85W PD charging, 3x USB 3.0, and braided nylon cable.",
        price_inr=1799.0, original_price_inr=2299.0, stock_count=40,
        shipping_tier="Free", shipping_cost_inr=0.0, warranty_months=12,
        tags=["dock", "hub", "usb-c", "travel", "portable", "macbook"],
        specs={"Ports": "7 (HDMI 4K, 3x USB 3.0, PD 85W, SD/TF)", "Weight": "95g"},
        merchant_id="merchant_devdesk", merchant_name="DevDesk Supply Co.", rating=4.4
    )
]

ALL_PRODUCTS = NOVATECH_PRODUCTS + BYTEFORGE_PRODUCTS + DEVDESK_PRODUCTS

MERCHANTS = {
    "merchant_novatech": {
        "id": "merchant_novatech",
        "name": "NovaTech Gear",
        "badge": "Verified Razorpay Merchant",
        "rating": 4.8,
        "location": "Bangalore, India",
        "color": "#00d2d3",
        "shipping_policy": "Standard ₹150 (Free above ₹4,000) • 2-3 days",
        "product_count": len(NOVATECH_PRODUCTS)
    },
    "merchant_byteforge": {
        "id": "merchant_byteforge",
        "name": "ByteForge Electronics",
        "badge": "Premium Seller",
        "rating": 4.7,
        "location": "Hyderabad, India",
        "color": "#f97316",
        "shipping_policy": "Express ₹149-₹199 • 24-hr Air Cargo",
        "product_count": len(BYTEFORGE_PRODUCTS)
    },
    "merchant_devdesk": {
        "id": "merchant_devdesk",
        "name": "DevDesk Supply Co.",
        "badge": "Budget Direct",
        "rating": 4.4,
        "location": "New Delhi, India",
        "color": "#34d399",
        "shipping_policy": "100% Free Shipping on All Orders • 3-4 days",
        "product_count": len(DEVDESK_PRODUCTS)
    }
}

class CatalogService:
    def __init__(self):
        self._products = {p.id: p.model_copy(deep=True) for p in ALL_PRODUCTS}
        self.simulated_drift_type: Optional[str] = None

    def get_all_products(self, merchant_id: Optional[str] = None) -> List[Product]:
        prods = []
        for p in self._products.values():
            if merchant_id and p.merchant_id != merchant_id:
                continue
            p_copy = p.model_copy(deep=True)
            if self.simulated_drift_type == "PRICE_SPIKE" and p.id == "nt_kb_01":
                p_copy.price_inr = 5499.0
            elif self.simulated_drift_type == "OUT_OF_STOCK" and p.id == "nt_kb_01":
                p_copy.stock_count = 0
            prods.append(p_copy)
        return prods

    def get_product(self, product_id: str) -> Optional[Product]:
        prod = self._products.get(product_id)
        if not prod:
            return None
        prod_copy = prod.model_copy(deep=True)
        if self.simulated_drift_type == "PRICE_SPIKE" and product_id == "nt_kb_01":
            prod_copy.price_inr = 5499.0
        elif self.simulated_drift_type == "OUT_OF_STOCK" and product_id == "nt_kb_01":
            prod_copy.stock_count = 0
        return prod_copy

    # Alias for get_product
    get_product_by_id = get_product

    def search_catalog(self, query: str, max_price: Optional[float] = None) -> List[Product]:
        q = query.lower()
        results = []
        for p in self.get_all_products():
            match = (
                q in p.name.lower() or
                q in p.description.lower() or
                any(q in tag.lower() for tag in p.tags) or
                any(q in v.lower() for v in p.specs.values())
            )
            if match:
                if max_price is None or p.price_inr <= max_price:
                    results.append(p)
        return results

    def compare_across_merchants(self, query: str, max_price: Optional[float] = None) -> Dict[str, Any]:
        """Search all merchants and return per-merchant results with best-deal winner."""
        results = self.search_catalog(query, max_price)
        merchant_groups: Dict[str, List[Product]] = {}
        for p in results:
            merchant_groups.setdefault(p.merchant_id, []).append(p)

        comparison = []
        best_deal = None
        best_total = float('inf')

        for mid, products in merchant_groups.items():
            merchant_info = MERCHANTS.get(mid, {})
            cheapest = min(products, key=lambda p: p.price_inr + p.shipping_cost_inr)
            total = cheapest.price_inr + cheapest.shipping_cost_inr
            entry = {
                "merchant_id": mid,
                "merchant_name": merchant_info.get("name", mid),
                "merchant_badge": merchant_info.get("badge", ""),
                "merchant_color": merchant_info.get("color", "#888"),
                "product": cheapest.model_dump(),
                "product_name": cheapest.name,
                "total_cost_inr": total,
                "products_found": len(products)
            }
            comparison.append(entry)
            if total < best_total:
                best_total = total
                best_deal = entry

        comparison.sort(key=lambda x: x["total_cost_inr"])
        return {
            "query": query,
            "merchants_compared": len(comparison),
            "comparison": comparison,
            "best_deal": best_deal,
            "cheapest_deal": best_deal,
            "buyer_savings_inr": round(max((c["total_cost_inr"] for c in comparison), default=0) - best_total, 2) if comparison else 0,
            "savings_vs_worst": round(max((c["total_cost_inr"] for c in comparison), default=0) - best_total, 2) if comparison else 0
        }

    def get_merchants(self) -> List[Dict[str, Any]]:
        return list(MERCHANTS.values())

    def set_drift_simulation(self, drift_type: Optional[str]):
        self.simulated_drift_type = drift_type

    def reset_catalog(self):
        self._products = {p.id: p.model_copy(deep=True) for p in ALL_PRODUCTS}
        self.simulated_drift_type = None

catalog_service = CatalogService()
