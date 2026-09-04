# Video transcript — the 5:00 pitch (recorded at submission)

Shot list assumes the live demo (with the deterministic seed). Timestamps are
beats, not hard cuts. One take, screen + voice, no intro animation — the first
10 seconds must carry the thesis.

## 0:00–0:20 — the thesis

**On screen:** the landing page, hero stamp.

> "Razorpay's homepage already sells the future: AI agents, shopping in your
> app, paying on their own. Everyone is building the buyer side of that
> counter. Somebody has to build the other side — the part a payments company
> needs before it lets an agent spend. ProjectX is both sides, powered by a Python engine."

## 0:20–1:05 — the buyer side (the brief's named example, live)

**On screen:** Playground. Type "headphones under 5000".

> "Here's the agent. Every step it takes is visible. But instead of standard RAG, we use
> Agent-to-Agent (A2A) negotiation. The buyer agent barters with the merchant agent
> to establish a live cart."

Type "checkout".

> "The desk signs a mandate: an amount cap, the item list, an expiry, and my
> trust tier — post-quantum ML-DSA-65 over canonical JSON. As the buyer's principal, I approve
> the envelope, and only then does the agent bind and pay."

Approve → gate checklist → capture.

> "The Proof-of-Policy Invariant (PoPI) gate re-verified everything at bind time — signature, tier bounds,
> live prices, quantities. Deterministic Python code, zero tokens: the LLM never
> decides money."

## 1:05–1:50 — the refusal beat (failure, handled)

**On screen:** red-team panel → "Overspend the tier" → BLOCKED.

> "Now the interesting part. I attack my own product. An unverified session
> tries a ₹2,199 mouse against a ₹500 tier — refused, with a reason code, and
> the attempt is SHA3-512 hash-chained into the audit log. Twelve authored attacks,
> each with its expected verdict."

**On screen:** "Tamper the signature" → BLOCKED · SIGNATURE_INVALID.

> "Tamper the mandate after signing — the post-quantum signature check kills it. And this
> ledger is tamper-evident: we flip one historical byte and the chain breaks exactly there."

## 1:50–2:35 — the merchant side (the empty cell)

**On screen:** Control Room. The P&L meter counting up.

> "Now walk around the counter. The Control Room is what the merchant needs to see.
> Agent GMV, revenue at list MDR, the AI serving cost from metered tokens, and the net, live.
> We're also using Razorpay Route to split the base and shipping costs instantly across multiple merchants."

**On screen:** approval queue → approve the ₹18,999 hold.

> "Orders over ten thousand rupees hold for a human, any tier. I approve — it
> captures, and it's replayable span-by-span."

## 2:35–3:20 — the protocol matrix (why this generalizes)

**On screen:** adapter switcher → wire chip expands.

> "The same PoPI gate behind three protocols. Same tool implementations, same verdicts, 
> different wire overhead. When ACP and friends settle, the adapter is a transport swap,
> not a rewrite."

## 3:20–4:05 — the proof layer (built for machine judges)

**On screen:** terminal — `make triage` scrolling.

> "Triage will be machine-assisted, so this repo is built to be judged by a machine:
> JUDGE.md maps every claim to a file and a regenerate command. The engineering log records
> every incident, each one turned into a test."

## 4:05–4:45 — honesty slide (scope, limits, next)

**On screen:** the honest scope ledger, one card at a time.

> "What's not done, on purpose, said plainly: the payment rail runs labeled
> simulation until test keys are attached. The math is real post-quantum math in Python.
> Every limit is labeled in the product, not hidden in a footnote."

## 4:45–5:00 — close

**On screen:** the manifest receipt, stamp lands.

> "The buyer side everyone is building. The desk nobody has built. Both
> sides, bounded by PoPI, metered, quantum-safe — and provable to a machine in sixty
> seconds. ProjectX. Thank you."

---

**Recording notes**

- Use the live seeded state (reset demo before recording).
- Cursor + typing must be visible; the step chips are the transparency story.
- Total: 5:00 hard limit. 
