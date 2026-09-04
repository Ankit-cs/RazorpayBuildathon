import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .neural_engine import neural_core

class RAGDocument(BaseModel):
    id: str
    category: str # "SPECIFICATION", "WARRANTY", "MERCHANT_POLICY", "SHIPPING_RULE", "COMPATIBILITY"
    title: str
    content: str
    merchant_name: Optional[str] = None
    product_id: Optional[str] = None
    tags: List[str]

class RAGSearchResult(BaseModel):
    document: RAGDocument
    similarity_score: float
    relevance_snippet: str

# ─── Comprehensive Commerce Knowledge Base ───
COMMERCE_KNOWLEDGE_BASE: List[RAGDocument] = [
    # NovaTech Gear Knowledge
    RAGDocument(
        id="rag_nt_warranty",
        category="WARRANTY",
        title="NovaTech Official 1-Year Pan-India Replacement Warranty",
        content="NovaTech Gear provides 12 months comprehensive hardware replacement on all KeyChron, Apex, and AuraSound devices. Doorstep reverse pickup supported in 24 major Indian cities with average turnaround of 48 hours. Accidental liquid damage requires an optional accidental cover add-on.",
        merchant_name="NovaTech Gear",
        product_id="nt_kb_01",
        tags=["warranty", "novatech", "replacement", "rma", "keychron", "headphones"]
    ),
    RAGDocument(
        id="rag_nt_return",
        category="MERCHANT_POLICY",
        title="NovaTech 7-Day No-Questions-Asked Return & Razorpay Instant Refund",
        content="NovaTech permits 7-day hassle-free returns on unopened electronics. Refunds are automatically dispatched via Razorpay Instant Refund APIs directly back to the original source account within 15 minutes of package scan.",
        merchant_name="NovaTech Gear",
        tags=["refund", "returns", "policy", "instant refund", "razorpay"]
    ),
    RAGDocument(
        id="rag_nt_shipping",
        category="SHIPPING_RULE",
        title="NovaTech Blueline Express & Same-Day Dispatch Rules",
        content="Orders placed before 2:00 PM IST qualify for same-day dispatch from Bangalore & Mumbai fulfillment centers. Standard delivery (₹150) takes 2-3 business days. Free shipping activates on orders exceeding ₹4,000.",
        merchant_name="NovaTech Gear",
        tags=["shipping", "delivery", "sla", "bangalore", "mumbai", "express"]
    ),
    RAGDocument(
        id="rag_kb_compatibility",
        category="COMPATIBILITY",
        title="KeyChron K2 Pro & Apex 60% OS and Switch Compatibility",
        content="KeyChron K2 Pro supports macOS, Windows, Linux, Android, and iOS with dedicated hardware switch toggle. Full VIA/QMK programmable keymaps. Hot-swappable 5-pin PCB accepts Cherry MX, Gateron, Kailh, and Panda switches without soldering.",
        merchant_name="NovaTech Gear",
        product_id="nt_kb_01",
        tags=["compatibility", "qmk", "via", "macos", "windows", "switches", "hot-swap"]
    ),

    # ByteForge Electronics Knowledge
    RAGDocument(
        id="rag_bf_warranty",
        category="WARRANTY",
        title="ByteForge 24-Month Extended Studio Care Assurance",
        content="ByteForge guarantees 2 full years (24 months) warranty on all Studio ANC headphones and TripleView docking hubs. Includes complimentary replacement ear-cushions and firmware updates over Bluetooth.",
        merchant_name="ByteForge Electronics",
        product_id="bf_anc_01",
        tags=["warranty", "byteforge", "extended", "studio", "headphones", "dock"]
    ),
    RAGDocument(
        id="rag_bf_shipping",
        category="SHIPPING_RULE",
        title="ByteForge Air Express Tier-1 SLA",
        content="ByteForge ships via Dedicated Air Cargo with 24-hour delivery guarantee to Delhi NCR, Mumbai, Hyderabad, and Bangalore. Express shipping surcharge is ₹199, waived for high-tier developer bundles.",
        merchant_name="ByteForge Electronics",
        tags=["air cargo", "express", "shipping", "delhi", "bangalore", "sla"]
    ),
    RAGDocument(
        id="rag_dock_compatibility",
        category="COMPATIBILITY",
        title="ByteForge TripleView 14-in-1 M1/M2/M3 Mac & Windows DisplayLink Matrix",
        content="ByteForge TripleView Dock leverages DisplayLink DL-6950 silicon. Enables dual and triple 4K@60Hz extended displays even on base Apple Silicon M1/M2/M3 MacBooks that natively limit external displays to one.",
        merchant_name="ByteForge Electronics",
        product_id="bf_dock_01",
        tags=["dock", "compatibility", "displaylink", "macbook", "m1", "m2", "m3", "triple monitor"]
    ),

    # DevDesk Supply Co. Knowledge
    RAGDocument(
        id="rag_dd_pricing",
        category="MERCHANT_POLICY",
        title="DevDesk Developer Direct Budget Guarantee & Volume Discounts",
        content="DevDesk manufactures direct-to-consumer developer ergonomics. Offers zero-margin introductory pricing with 100% free standard shipping on all orders. B2B volume orders receive 10% instant rebate on split checkout.",
        merchant_name="DevDesk Supply Co.",
        tags=["devdesk", "budget", "free shipping", "rebate", "pricing"]
    ),
    RAGDocument(
        id="rag_dd_mat_spec",
        category="SPECIFICATION",
        title="DevDesk HyperGlide Vegan Leather & Merino Desk Mat Material Datasheet",
        content="Triple-layered hydrophobic construction with 900x400x3mm footprint. Top layer: scratch-resistant PU vegan leather with micro-textured tracking surface for optical mice (16,000 DPI tested). Base layer: non-slip natural rubber.",
        merchant_name="DevDesk Supply Co.",
        tags=["spec", "material", "desk mat", "leather", "dpi", "dimensions"]
    )
]

class RAGEngine:
    def __init__(self):
        self.documents = COMMERCE_KNOWLEDGE_BASE

    def retrieve_context(
        self,
        query: str,
        category: Optional[str] = None,
        top_k: int = 3
    ) -> List[RAGSearchResult]:
        """
        Retrieves relevant commerce domain chunks using dense neural vector embeddings.
        """
        query_vec = neural_core.dense_vector.generate_embedding(query)
        scored_results: List[RAGSearchResult] = []

        for doc in self.documents:
            if category and doc.category != category:
                continue

            doc_text = f"{doc.title} {doc.content} {' '.join(doc.tags)}"
            doc_vec = neural_core.dense_vector.generate_embedding(doc_text)
            sim = neural_core.dense_vector.cosine_similarity(query_vec, doc_vec)

            # Keyword overlap boost
            query_words = set(query.lower().split())
            overlap = sum(1 for w in query_words if w in doc_text.lower())
            final_score = round(min(1.0, sim * 0.7 + (overlap / max(1, len(query_words))) * 0.3), 4)

            # Extract snippet
            snippet = doc.content[:160] + "..." if len(doc.content) > 160 else doc.content

            scored_results.append(RAGSearchResult(
                document=doc,
                similarity_score=final_score,
                relevance_snippet=snippet
            ))

        scored_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return scored_results[:top_k]

    def build_rag_context_prompt(self, query: str) -> Dict[str, Any]:
        """Synthesizes context for autonomous buyer agent reasoning."""
        retrieved = self.retrieve_context(query, top_k=3)
        context_lines = []
        for r in retrieved:
            context_lines.append(f"[{r.document.category} | {r.document.merchant_name or 'General'}] {r.document.title}: {r.document.content}")
        
        return {
            "query": query,
            "retrieved_chunks_count": len(retrieved),
            "context_summary": " \n".join(context_lines),
            "top_match_title": retrieved[0].document.title if retrieved else "None",
            "top_score": retrieved[0].similarity_score if retrieved else 0.0,
            "results": [r.model_dump() for r in retrieved]
        }

rag_engine = RAGEngine()
