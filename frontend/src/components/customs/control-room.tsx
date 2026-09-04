"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import {
  CountUp,
  GhostButton,
  InkButton,
  LiveDot,
  ManifestRow,
  MeterBar,
  SectionLabel,
  Stamp,
  StatusChip,
  TierChip,
  inr,
  monoId,
} from "./bits";

interface AgentMetrics {
  gmv_inr: number;
  total_purchases_attempted: number;
  successful_transactions: number;
  blocked_violations: number;
  failure_recoveries: number;
  recovery_success_rate: number;
  conversion_rate_pct: number;
  aov_inr: number;
  aov_uplift_pct: number;
  total_savings_generated_inr: number;
  latency_waterfall_ms: Record<string, number>;
  merchant_distribution: Record<string, number>;
  pqc_status: string;
  razorpay_rails: string;
}

interface AuditEvent {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  status: string;
  message: string;
  details: any;
  razorpay_order_id: string | null;
  invariants_passed: boolean | null;
  pqc_scheme: string;
  pqc_signature: string;
  pqc_block_hash: string;
  prev_block_hash: string;
}

export function ControlRoom() {
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null);
  const [ledger, setLedger] = useState<AuditEvent[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const prevGmv = useRef(0);
  const seenIds = useRef<Set<string>>(new Set());
  const [flashIds, setFlashIds] = useState<Set<string>>(new Set());

  const refresh = useCallback(async () => {
    try {
      const [mRes, lRes] = await Promise.all([
        fetch("/api/python/agent/metrics", { cache: "no-store" }),
        fetch("/api/python/agent/audit-ledger?limit=100", { cache: "no-store" }),
      ]);
      const mData = await mRes.json();
      const lData = await lRes.json();
      
      prevGmv.current = metrics?.gmv_inr ?? 0;
      setMetrics(mData);
      setLedger(lData);
    } catch {
      // ignore
    }
  }, [metrics]);

  useEffect(() => {
    if (ledger.length === 0) return;
    const current = new Set(ledger.map((o) => o.id));
    const fresh = new Set([...current].filter((id) => !seenIds.current.has(id)));
    if (seenIds.current.size > 0 && fresh.size > 0) {
      setFlashIds(fresh);
      window.setTimeout(() => setFlashIds(new Set()), 2200);
    }
    seenIds.current = current;
  }, [ledger]);

  useEffect(() => {
    void refresh();
    const i = setInterval(() => void refresh(), 6000);
    return () => clearInterval(i);
  }, [refresh]);

  if (!metrics) {
    return (
      <div className="doc flex min-h-[480px] items-center justify-center">
        <span className="text-[13px] text-inksoft">connecting to agent backend…</span>
      </div>
    );
  }

  const gmvDelta = metrics.gmv_inr - prevGmv.current;
  const maxLatency = Math.max(...Object.values(metrics.latency_waterfall_ms), 1);

  return (
    <div className="space-y-7">
      {/* ------------------------------ header ------------------------------ */}
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
        <div>
          <div className="label-caps">fieldnote supply · merchant desk</div>
          <h2 className="mt-1.5 font-display text-2xl font-medium tracking-[-0.02em]">Control Room</h2>
          <p className="mt-2 max-w-[52ch] text-[14px] leading-relaxed text-inksoft">
            The desk a payments company needs before it lets agents spend — live agent performance,
            latency telemetry, and quantum-signed audit ledger.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[12.5px]">
          <span className="text-inksoft">
            rail <span className="font-medium text-ink">{metrics.razorpay_rails.toLowerCase()}</span>
          </span>
          <span className="text-inksoft">
            security <span className="font-mono text-[11.5px] font-medium text-ink">NIST FIPS 204</span>
          </span>
          <GhostButton
            onClick={async () => {
              setBusy("reset");
              await fetch("/api/python/agent/audit-ledger/clear", { method: "POST" });
              await fetch("/api/python/catalog/reset", { method: "POST" });
              await refresh();
              setBusy(null);
            }}
            disabled={busy === "reset"}
          >
            {busy === "reset" ? "reseeding…" : "reset environment"}
          </GhostButton>
        </div>
      </div>

      {/* ------------------------------ meter ------------------------------ */}
      <section className="doc overflow-hidden" aria-label="agent performance metrics">
        <div className="grid gap-px bg-line md:grid-cols-[1.25fr_1fr_1fr_1fr]">
          <div className="bg-card px-5 py-5 md:col-span-1">
            <div className="label-caps">agent GMV — cleared &amp; captured</div>
            <div className="mt-1.5 flex items-baseline gap-2.5">
              <CountUp value={metrics.gmv_inr} format={(n) => inr(Math.round(n * 100), { decimals: false })} className="font-display text-[38px] font-medium leading-none tracking-[-0.02em] text-ink" />
              {gmvDelta > 0 && <span className="text-[12px] font-medium text-cleared">+{inr(gmvDelta * 100)} live</span>}
            </div>
            <div className="mt-2.5 text-[12px] text-inksoft">
              {metrics.successful_transactions} captured · {metrics.blocked_violations} blocked
            </div>
          </div>
          <div className="bg-card px-5 py-5">
            <div className="label-caps">conversion rate</div>
            <CountUp value={metrics.conversion_rate_pct} format={(n) => `${n.toFixed(1)}%`} className="font-display text-[26px] font-medium tracking-[-0.02em] text-ink" />
            <div className="mt-1.5 text-[12px] text-inksoft">{metrics.total_purchases_attempted} total attempts</div>
          </div>
          <div className="bg-card px-5 py-5">
            <div className="label-caps">average order value</div>
            <CountUp value={metrics.aov_inr} format={(n) => inr(Math.round(n * 100), { decimals: false })} className="font-display text-[26px] font-medium tracking-[-0.02em] text-ink" />
            <div className="mt-1.5 text-[12px] text-cleared">
              +{metrics.aov_uplift_pct}% AI uplift
            </div>
          </div>
          <div className="bg-card px-5 py-5">
            <div className="label-caps">buyer savings generated</div>
            <CountUp value={metrics.total_savings_generated_inr} format={(n) => inr(Math.round(n * 100), { decimals: false })} className="font-display text-[26px] font-medium tracking-[-0.02em] text-cleared" />
            <div className="mt-1.5 text-[12px] text-inksoft">
              via A2A negotiation &amp; split cart
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-7 xl:grid-cols-[minmax(0,1.9fr)_minmax(0,1fr)]">
        <div className="space-y-7">
          {/* ------------------------------ orders / audit ledger ------------------------------ */}
          <section className="doc overflow-hidden px-5 py-5" aria-label="quantum audit ledger">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <SectionLabel>audit ledger — live</SectionLabel>
                <LiveDot label="ticking" />
              </div>
              <span className="text-[12px] text-inksoft">
                NIST FIPS 204 Lattice Signed
              </span>
            </div>
            
            <div className="ledger-scroll mt-6 max-h-[440px] overflow-auto">
              <table className="w-full min-w-[780px] table-fixed border-collapse text-left">
                <colgroup>
                  <col style={{ width: 70 }} />
                  <col style={{ width: 130 }} />
                  <col style={{ width: 120 }} />
                  <col />
                  <col style={{ width: 96 }} />
                  <col style={{ width: 100 }} />
                </colgroup>
                <thead className="sticky top-0 z-10">
                  <tr className="border-b border-line2 bg-card/95 backdrop-blur-sm">
                    {["time", "event id", "actor", "action", "status", "order"].map((h, i) => (
                      <th key={h || i} className={cn("label-caps py-2 pr-3 font-mono")}>
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ledger.map((ev) => {
                    const fresh = flashIds.has(ev.id);
                    return (
                      <tr
                        key={ev.id}
                        className={cn(
                          "border-b border-line/70 transition-colors",
                          "hover:bg-paper2/60",
                          fresh && "row-fresh"
                        )}
                      >
                        <td className="tnum py-3 pr-3 font-mono text-[10px] text-inksoft">
                          {new Date(ev.timestamp).toLocaleTimeString("en-IN", { hour12: false })}
                        </td>
                        <td className="py-3 pr-3 font-mono text-[11px] text-inksoft">{monoId(ev.id, 14)}</td>
                        <td className="py-3 pr-3 font-mono text-[10px] text-inksoft">{ev.actor}</td>
                        <td className="py-3 pr-3 text-[12px] text-inksoft truncate" title={ev.message}>
                          <span className="font-medium text-ink mr-2">{ev.action}</span>
                          {ev.message}
                        </td>
                        <td className="py-3 pr-3">
                          <StatusChip status={ev.status === "SUCCESS" || ev.status === "RECOVERED" ? "CAPTURED" : ev.status === "VIOLATION" ? "REFUSED" : "PROPOSED"} />
                        </td>
                        <td className="py-3 pr-3 font-mono text-[10px] text-inksoft truncate">
                          {ev.razorpay_order_id ? monoId(ev.razorpay_order_id, 14) : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {ledger.length === 0 && (
                <p className="py-6 text-center text-[13px] text-inksoft">
                  no events recorded — fire a chat or initiate checkout
                </p>
              )}
            </div>
            <div className="mt-3.5 flex flex-wrap items-center justify-between gap-x-6 gap-y-1.5 border-t border-line pt-3 text-[12px] text-inksoft">
              <span>{ledger.length} events logged</span>
              <span className="font-mono">{metrics.pqc_status}</span>
            </div>
          </section>
        </div>

        <div className="space-y-7">
          {/* ------------------------------ latency ablation ------------------------------ */}
          <section className="doc px-5 py-5" aria-label="latency waterfall">
            <SectionLabel>latency — protocol overhead</SectionLabel>
            <div className="mt-4">
              {Object.entries(metrics.latency_waterfall_ms)
                .filter(([k]) => k !== "total_e2e_latency")
                .map(([k, v]) => (
                <MeterBar
                  key={k}
                  label={k.replace(/_/g, " ")}
                  value={v}
                  max={maxLatency}
                  kind={k.includes("vulcan") ? "refused" : k.includes("rag") ? "held" : "cleared"}
                  right={`${v.toFixed(1)}ms`}
                />
              ))}
            </div>
            <div className="mt-4">
              <ManifestRow
                left="total end-to-end latency"
                right={`${metrics.latency_waterfall_ms.total_e2e_latency?.toFixed(1) || 0}ms`}
                mono
              />
            </div>
          </section>
          
          {/* ------------------------------ merchant distribution ------------------------------ */}
          <section className="doc px-5 py-5" aria-label="merchant distribution">
            <SectionLabel>merchant distribution</SectionLabel>
            <div className="mt-4 space-y-2">
              {Object.entries(metrics.merchant_distribution).map(([merchant, count]) => (
                <ManifestRow
                  key={merchant}
                  left={merchant}
                  right={String(count)}
                  mono
                />
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
