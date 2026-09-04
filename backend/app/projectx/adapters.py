import json
import hashlib
import math
from typing import Dict, Any, Optional, List, Callable, Awaitable
from pydantic import BaseModel

AdapterId = str

ADAPTERS = {
    "naive": {
        "label": "naive",
        "blurb": "Direct in-process tool calls. The baseline: zero protocol overhead."
    },
    "mcp": {
        "label": "MCP-style",
        "blurb": "JSON-RPC 2.0 tool envelopes (tools/list → tools/call), MCP-shaped."
    },
    "acp": {
        "label": "ACP-style",
        "blurb": "Agent-to-agent message envelopes with ack + signed receipt per call."
    }
}

TOOL_SCHEMAS = [
    {
        "name": "search_catalog",
        "description": "Search Fieldnote Supply's catalog. Returns up to 3 products.",
        "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
    },
    {
        "name": "get_product",
        "description": "Fetch one product by id (price, stock, tags).",
        "inputSchema": {"type": "object", "properties": {"productId": {"type": "string"}}, "required": ["productId"]}
    },
    {
        "name": "add_to_cart",
        "description": "Add quantity of a product to the session cart.",
        "inputSchema": {
            "type": "object",
            "properties": {"productId": {"type": "string"}, "quantity": {"type": "integer", "minimum": 1}},
            "required": ["productId", "quantity"]
        }
    },
    {
        "name": "request_mandate",
        "description": "Ask the merchant desk for a signed spending mandate for the cart.",
        "inputSchema": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "bind_and_pay",
        "description": "Bind the order against the mandate and pay on the rail.",
        "inputSchema": {"type": "object", "properties": {"orderId": {"type": "string"}}, "required": ["orderId"]}
    }
]

class WireLogEntry(BaseModel):
    adapter: AdapterId
    dir: str
    method: Optional[str] = None
    body: str
    bytes: int

class AdapterResult(BaseModel):
    value: Any
    wire: List[WireLogEntry]
    calls: int
    roundTrips: int

class AdapterContext:
    def __init__(self, callTool: Callable[[str, Dict[str, Any]], Awaitable[Any]], sign: Callable[[str], str], sessionId: str):
        self.callTool = callTool
        self.sign = sign
        self.sessionId = sessionId

def est_tokens(s: str) -> int:
    return math.ceil(len(s) / 4)

def tokens_of(text: str) -> int:
    return est_tokens(text)

async def naive_call(name: str, args: Dict[str, Any], ctx: AdapterContext) -> AdapterResult:
    value = await ctx.callTool(name, args)
    body = f"direct:{name}"
    return AdapterResult(
        value=value,
        wire=[WireLogEntry(adapter="naive", dir="out", method=name, body=body, bytes=len(body))],
        calls=1,
        roundTrips=1
    )

async def mcp_call(name: str, args: Dict[str, Any], ctx: AdapterContext) -> AdapterResult:
    request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})
    value = await ctx.callTool(name, args)
    response = json.dumps({"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "json", "json": value}]}})
    return AdapterResult(
        value=value,
        wire=[
            WireLogEntry(adapter="mcp", dir="out", method="tools/call", body=request, bytes=len(request)),
            WireLogEntry(adapter="mcp", dir="in", method="result", body=response, bytes=len(response))
        ],
        calls=1,
        roundTrips=1
    )

async def acp_call(name: str, args: Dict[str, Any], ctx: AdapterContext) -> AdapterResult:
    thread = ctx.sessionId
    request = json.dumps({
        "type": "agent.message",
        "from": f"buyer:{thread}",
        "to": "merchant:fieldnote-supply",
        "threadId": thread,
        "performative": "request",
        "body": {"tool": name, "args": args}
    })
    
    ack = json.dumps({
        "type": "agent.message",
        "from": "merchant:fieldnote-supply",
        "to": f"buyer:{thread}",
        "threadId": thread,
        "performative": "ack",
        "ref": hashlib.sha256(request.encode("utf-8")).hexdigest()[:12]
    })
    
    value = await ctx.callTool(name, args)
    
    result_envelope = json.dumps({
        "type": "agent.message",
        "from": "merchant:fieldnote-supply",
        "to": f"buyer:{thread}",
        "threadId": thread,
        "performative": "result",
        "body": {"value": value}
    })
    
    receipt = ctx.sign(hashlib.sha256(result_envelope.encode("utf-8")).hexdigest())
    
    return AdapterResult(
        value=value,
        wire=[
            WireLogEntry(adapter="acp", dir="out", method="request", body=request, bytes=len(request)),
            WireLogEntry(adapter="acp", dir="in", method="ack", body=ack, bytes=len(ack)),
            WireLogEntry(adapter="acp", dir="in", method="result", body=result_envelope, bytes=len(result_envelope) + len(receipt))
        ],
        calls=1,
        roundTrips=3
    )

async def adapter_call(adapter: AdapterId, name: str, args: Dict[str, Any], ctx: AdapterContext) -> AdapterResult:
    if adapter == "mcp":
        return await mcp_call(name, args, ctx)
    elif adapter == "acp":
        return await acp_call(name, args, ctx)
    else:
        return await naive_call(name, args, ctx)
