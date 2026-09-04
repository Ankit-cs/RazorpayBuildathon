import os
import json
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from .ledger import Ledger
from .keys import load_keys, KeyPair
from .catalog import catalog_snapshot, CATALOG
from .engine import EngineDeps, run_transaction, confirm_payment_once, TxInput
from .types import TrustTier

class BuyerSession(BaseModel):
    sessionId: str
    buyerId: str
    tier: TrustTier
    cart: Dict[str, int]
    mandate: Optional[Dict[str, Any]]
    awaitingMandateApproval: bool
    lastOrderId: Optional[str]
    createdAtMs: int

class ProjectXRuntime:
    def __init__(self):
        self.keys: KeyPair = None
        self.ledger: Ledger = None
        self.ephemeral: bool = False
        self.stateDir: Optional[str] = None
        self.sessions: Dict[str, BuyerSession] = {}
        self.deps: EngineDeps = None
        self.catalog = None

PROBE = "_projectX-state-probe"

def state_dir_for() -> Dict[str, Any]:
    override = os.environ.get("CUSTOMS_STATE_DIR")
    base = override if override else os.path.join(os.getcwd(), "data", "state")
    try:
        os.makedirs(base, exist_ok=True)
        probe_path = os.path.join(base, PROBE)
        with open(probe_path, "w") as f:
            f.write("1")
        os.remove(probe_path)
        return {"dir": base, "ephemeral": False}
    except Exception:
        return {"dir": None, "ephemeral": True}

_runtime: Optional[ProjectXRuntime] = None

def get_runtime() -> ProjectXRuntime:
    global _runtime
    if _runtime:
        return _runtime
        
    res = state_dir_for()
    dir_path = res["dir"]
    ephemeral = res["ephemeral"]
    
    keys = load_keys(dir_path if dir_path else os.path.join(os.getcwd(), "data", "state"))
    ledger = Ledger(dir_path)
    deps = EngineDeps(ledger=ledger, private_key_pem=keys.privateKeyPem, public_key_pem=keys.publicKeyPem, merchant_fingerprint=keys.fingerprint)
    
    rt = ProjectXRuntime()
    rt.keys = keys
    rt.ledger = ledger
    rt.ephemeral = ephemeral
    rt.stateDir = dir_path
    rt.sessions = {}
    rt.deps = deps
    rt.catalog = catalog_snapshot(keys.publicKeyPem, keys.fingerprint)
    
    _runtime = rt
    
    if len(ledger.all()) == 0:
        seed_history(deps)
        ledger.append("demo.seeded", {"note": "deterministic 48h history via the real engine", "ephemeral": ephemeral})
        
    return rt

def reset_runtime() -> ProjectXRuntime:
    rt = get_runtime()
    rt.ledger.reset()
    rt.sessions.clear()
    seed_history(rt.deps)
    rt.ledger.append("demo.seeded", {"note": "reset requested — deterministic history regenerated", "ephemeral": rt.ephemeral})
    return rt

# --- SEED ---

def mulberry32(seed: int):
    a = seed
    def _next():
        nonlocal a
        a = (a + 0x6d2b79f5) & 0xFFFFFFFF
        t = (a ^ (a >> 15)) & 0xFFFFFFFF
        t = (t * (1 | a)) & 0xFFFFFFFF
        t = (t + ((t ^ (t >> 7)) * (61 | t))) & 0xFFFFFFFF
        t = t ^ t
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0
    return _next

import datetime
SEED_CLOCK_BASE = int(datetime.datetime(2026, 8, 30, 4, 0, 0, tzinfo=datetime.timezone.utc).timestamp() * 1000)
SEED_RNG = mulberry32(0x5eed2026)

BUYERS = [
  {"id": "buyer-ola", "tier": "MANDATED"},
  {"id": "buyer-kite", "tier": "ATTESTED"},
  {"id": "buyer-mono", "tier": "ATTESTED"},
  {"id": "buyer-vanta", "tier": "UNVERIFIED"},
  {"id": "buyer-iris", "tier": "MANDATED"},
]

ADAPTER_CYCLE = ["naive", "mcp", "acp", "mcp", "naive", "acp", "naive", "mcp"]

SHOPPING_TRIPS = [
  {"buyer": BUYERS[0], "items": [{"productId": "field-mech-65", "quantity": 1}]},
  {"buyer": BUYERS[1], "items": [{"productId": "ridge-mouse", "quantity": 1}, {"productId": "slate-desk-mat", "quantity": 1}]},
  {"buyer": BUYERS[2], "items": [{"productId": "globe-adapter", "quantity": 2}]},
  {"buyer": BUYERS[3], "items": [{"productId": "temp-ir-thermometer", "quantity": 1}]},
  {"buyer": BUYERS[4], "items": [{"productId": "vault-ssd-1tb", "quantity": 1}, {"productId": "junction-hub-7", "quantity": 1}]},
  {"buyer": BUYERS[0], "items": [{"productId": "paper-ereader", "quantity": 1}]},
  {"buyer": BUYERS[1], "items": [{"productId": "bud-pro-earbuds", "quantity": 1}]},
  {"buyer": BUYERS[2], "items": [{"productId": "arc-light-bar", "quantity": 1}]},
  {"buyer": BUYERS[4], "items": [{"productId": "traverse-backpack-22", "quantity": 1}, {"productId": "pocket-multitool", "quantity": 1}]},
  {"buyer": BUYERS[0], "items": [{"productId": "trail-anc-headphones", "quantity": 1}]},
  {"buyer": BUYERS[1], "items": [{"productId": "cell-powerbank-20k", "quantity": 1}, {"productId": "signal-router", "quantity": 1}]},
  {"buyer": BUYERS[2], "items": [{"productId": "beacon-speaker", "quantity": 1}]},
  {"buyer": BUYERS[3], "items": [{"productId": "trail-anc-headphones", "quantity": 1}]},
  {"buyer": BUYERS[4], "items": [{"productId": "riser-stand", "quantity": 1}]},
  {"buyer": BUYERS[0], "items": [{"productId": "shade-sunglasses", "quantity": 1}]},
  {"buyer": BUYERS[2], "items": [{"productId": "paper-ereader", "quantity": 3}]},
  {"buyer": BUYERS[4], "items": [{"productId": "summit-drone-4k", "quantity": 1}]},
  {"buyer": BUYERS[1], "items": [{"productId": "temp-ir-thermometer", "quantity": 2}]},
  {"buyer": BUYERS[0], "items": [{"productId": "bud-pro-earbuds", "quantity": 2}, {"productId": "slate-desk-mat", "quantity": 1}]},
  {"buyer": BUYERS[4], "items": [{"productId": "globe-adapter", "quantity": 3}]},
]

def seed_history(deps: EngineDeps):
    clock = SEED_CLOCK_BASE
    
    def step():
        nonlocal clock
        clock += int(8_400_000 + SEED_RNG() * 2_400_000)
        return clock
        
    for i, trip in enumerate(SHOPPING_TRIPS):
        step()
        run_transaction(deps, TxInput(
            buyerId=trip["buyer"]["id"],
            tier=trip["buyer"]["tier"],
            items=trip["items"],
            adapter=ADAPTER_CYCLE[i % len(ADAPTER_CYCLE)],
            nowMs=clock,
            orderId=f"ord_hist_{str(i + 1).zfill(3)}",
            humanApproved=False
        ))
        
    step()
    held_idx = next((i for i, t in enumerate(SHOPPING_TRIPS) if len(t["items"]) > 0 and t["items"][0]["productId"] == "trail-anc-headphones" and t["buyer"]["id"] == "buyer-ola"), -1)
    held = SHOPPING_TRIPS[held_idx] if held_idx >= 0 else SHOPPING_TRIPS[9]
    
    approved_tx = run_transaction(deps, TxInput(
        buyerId=held["buyer"]["id"],
        tier=held["buyer"]["tier"],
        items=held["items"],
        adapter="naive",
        nowMs=step(),
        orderId="ord_hist_021",
        humanApproved=True
    ))
    
    if approved_tx.decision.kind == "ALLOW":
        deps.ledger.append_at("approval.granted", {"orderId": approved_tx.orderId, "by": "merchant-desk", "note": "human approved the held ₹18,999 order"}, step())
        
    # TODO: port attacks later
    
    step()
    replay_base = run_transaction(deps, TxInput(
        buyerId="attacker-replay-payment",
        tier="ATTESTED",
        items=[{"productId": "arc-light-bar", "quantity": 1}],
        adapter="mcp",
        nowMs=clock,
        orderId="ord_atk_012"
    ))
    
    if replay_base.payment:
        replayed = confirm_payment_once(deps, replay_base.orderId, replay_base.payment.confirmId, {"note": "duplicate submission of the same confirmation"})
        deps.ledger.append_at("attack.blocked", {
            "attackId": "replay-payment",
            "label": "Replay the payment confirmation",
            "orderId": replay_base.orderId,
            "tier": "ATTESTED",
            "verdict": "PASSED" if replayed["ok"] else "BLOCKED",
            "code": None if replayed["ok"] else "REPLAY_DETECTED",
            "expected": "REPLAY_DETECTED",
            "matched": not replayed["ok"]
        }, step())
