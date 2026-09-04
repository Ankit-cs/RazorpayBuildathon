# Architecture

The brief asks for three artifacts: the repo, the video, and *the architecture*. This is
that artifact — one diagram, one table, the decisions that mattered, and the threat model
the corpus encodes.

## The one diagram

```
              BUYER SIDE                              MERCHANT SIDE
   ┌──────────────────────────┐            ┌───────────────────────────┐
   │  Next.js Frontend        │            │  Control Room             │
   │  chat → intent → cart    │            │  channel P&L meter        │
   │  A2A Negotiation UI      │            │  approvals ≥ ₹10,000      │
   │  Multi-Merchant Cart     │            │  order ledger · trace     │
   └────────────┬─────────────┘            └─────────────▲─────────────┘
                │ HTTP API Calls                         │ SSE / Polling
                ▼                                        │
   ┌────────────────────────────────────────────────────┴──────────────┐
   │                backend/app/projectx/ — THE ENGINE                 │
   │  Python FastAPI backend                                           │
   │  GATE — Proof-of-Policy Invariant (PoPI) checking engine          │
   │         NIST FIPS 204 ML-DSA-65 signatures, no LLM inside gate    │
   │  ledger — SHA3-512 hash-chained JSONL ledger for non-repudiation  │
   │  settlement — Razorpay Route Atomic Split across Merchants        │
   └───────────────┬────────────────────────────────────────────────── ┘
                   │ orders (test-mode only · labeled simulation by default)
                   ▼
            Razorpay Test Rails ──► Route Settlement ──► capture
```

## Component table

| Component | Responsibility | Evidence |
|---|---|---|
| `backend/app/projectx/ledger.py` | SHA3-512 Hash-chained JSONL, order projection, span storage | `make audit` (tamper control) |
| `backend/app/projectx/engine.py` | The PoPI gate, policy verification, ML-DSA-65 signature checks | the conformance verdicts match live UI refusals |
| `backend/app/projectx/fuzz/` | The authored attacks — the test suite of record | `make fuzz` (12/12) |
| `frontend/src/app/` | Next.js App Router for all React surfaces | `npm run dev` |
| `frontend/src/components/ProjectX/` | UI Components, Live Execution Trace | `results/project.json` |

## Decisions

| # | Decision | Rationale | Status |
|---|---|---|---|
| 1 | Payment mechanism: Razorpay Route | We are fulfilling multi-merchant carts, so atomic split transfers via Route is required for zero fund leakage. | **code ready** |
| 2 | ML-DSA-65 for mandate signatures | Post-Quantum cryptography protects the non-repudiation of the ledger against 10-year Shor/Grover attacks. | locked |
| 3 | JSONL ledger instead of SQLite/ORM | the brief's bar is "show the audit trail" — here the audit trail IS the database; `head data/state/ledger.jsonl` is a debugging command; zero native deps; the chain gives tamper evidence an ORM doesn't. | locked |
| 4 | Integer paise end-to-end; canonical JSON refuses floats | floats never touch money; the refusal itself is a fuzz case | locked |
| 5 | Trust tiers: unverified ₹500/1 item/10 min · attested ₹5,000/3/30 min · mandated ₹50,000/10/24 h | UPI-Circle-style delegated caps; blocks get their most quotable refusal line | locked |
| 6 | Human approval threshold ₹10,000 | above it, money waits for a human regardless of tier — hold, not refuse | locked |
| 7 | Separation of Frontend/Backend | A dedicated Python FastAPI backend handles quantum crypto math and hashing much better than a Node backend. | locked |

## The threat model (what the corpus encodes)

| Attack | Why it exists | Where it dies |
|---|---|---|
| Overspend the tier | agents inflate spend under weak identity | tier cap check |
| Overspend the mandate cap | legitimately-signed envelope, bigger order | mandate cap check |
| Tampered signature | body widened after signing | ML-DSA-65 verify |
| Quantum key attack | Grover/Shor cracking classical keys | PQC (Lattice cryptography) |
| Price drift at bind | catalog moves between proposal and bind | price re-verification |
| Sneak past ₹10,000 | un-approved high-ticket order | human threshold (hold) |

Each is a case in `backend/app/projectx/fuzz/` with its expected verdict — the corpus is the regression suite.
