"use client";
import React, { useState, useEffect } from 'react';
import { ArrowLeftRight, Bot, Sparkles, Send, ShieldCheck, Zap, Award, CheckCircle2, TrendingDown, Clock, Shield } from 'lucide-react';

export function A2ANegotiationView({ onExecutePurchase, onSelectTab }) {
  const [query, setQuery] = useState("KeyChron K2 Pro wireless keyboard");
  const [budget, setBudget] = useState(4500);
  const [urgency, setUrgency] = useState("NORMAL");
  const [isNegotiating, setIsNegotiating] = useState(false);
  const [sessionResult, setSessionResult] = useState(null);
  const [visibleRounds, setVisibleRounds] = useState(0);

  const startNegotiation = async () => {
    setIsNegotiating(true);
    setSessionResult(null);
    setVisibleRounds(0);

    try {
      const res = await fetch('/api/agent/negotiate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query,
          budget_limit_inr: parseFloat(budget),
          urgency_mode: urgency,
          preferred_category: "Electronics"
        })
      });
      const data = await res.json();
      setSessionResult(data);

      // Animate rounds appearing
      setTimeout(() => setVisibleRounds(1), 300);
      setTimeout(() => setVisibleRounds(2), 900);
      setTimeout(() => {
        setVisibleRounds(3);
        setIsNegotiating(false);
      }, 1600);
    } catch (e) {
      console.error('Negotiation error:', e);
      setIsNegotiating(false);
    }
  };

  useEffect(() => {
    startNegotiation();
  }, []);

  const handleOrderWinningDeal = () => {
    if (!sessionResult) return;
    onExecutePurchase({
      user_prompt: `Procure ${sessionResult.winning_product_name} at agreed negotiated price of ₹${sessionResult.final_agreed_price_inr}`,
      spending_policy: {
        max_budget_inr: parseFloat(budget),
        max_shipping_inr: 200.0,
        allowed_categories: ['Electronics', 'Peripherals'],
        require_warranty: true,
        allow_bundle_upsell: true
      },
      include_upsell_bundle: false,
      force_failure_simulation: null
    });
    if (onSelectTab) onSelectTab('studio');
  };

  const getSpeakerBadge = (speaker) => {
    if (speaker === 'BuyerAgent') {
      return { name: 'VERITY Buyer Agent', color: 'var(--brand-primary)', bg: 'rgba(0, 210, 211, 0.15)', icon: Bot };
    } else if (speaker.includes('NovaTech')) {
      return { name: 'NovaTech Seller Agent', color: '#00d2d3', bg: 'rgba(0, 210, 211, 0.12)', icon: Sparkles };
    } else if (speaker.includes('ByteForge')) {
      return { name: 'ByteForge Seller Agent', color: '#f97316', bg: 'rgba(249, 115, 22, 0.12)', icon: Zap };
    } else {
      return { name: 'DevDesk Seller Agent', color: '#34d399', bg: 'rgba(16, 185, 129, 0.12)', icon: ShieldCheck };
    }
  };

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Info */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px', height: '36px', borderRadius: '10px',
              background: 'linear-gradient(135deg, #00d2d3, #6366f1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <ArrowLeftRight size={20} color="#04131d" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.02em' }}>
                Agent-to-Agent (A2A) Negotiation Arena
              </h2>
              <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                Multi-round autonomous bargaining across NovaTech, ByteForge & DevDesk merchant agents
              </p>
            </div>
          </div>
        </div>

        {/* Live Savings Meter */}
        {sessionResult && (
          <div style={{
            background: 'rgba(16, 185, 129, 0.15)',
            border: '1px solid rgba(16, 185, 129, 0.35)',
            borderRadius: '12px',
            padding: '10px 18px',
            display: 'flex',
            alignItems: 'center',
            gap: '14px'
          }}>
            <div>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', textTransform: 'uppercase', fontWeight: '700' }}>
                Buyer Savings Generated
              </span>
              <div style={{ fontSize: '1.35rem', fontWeight: '800', color: '#34d399' }}>
                ₹{sessionResult.total_savings_inr?.toLocaleString('en-IN')} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>({sessionResult.savings_percentage}%)</span>
              </div>
            </div>
            <TrendingDown size={28} color="#34d399" />
          </div>
        )}
      </div>

      {/* Control Bar */}
      <div className="glass-panel" style={{ padding: '18px 24px', display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: '240px' }}>
          <label style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Product Procurement Target
          </label>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              width: '100%', padding: '9px 14px', borderRadius: '8px',
              background: 'rgba(0,0,0,0.4)', border: '1px solid var(--border-subtle)',
              color: 'var(--text-main)', fontSize: '0.85rem', outline: 'none'
            }}
          />
        </div>

        <div style={{ width: '160px' }}>
          <label style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Budget Ceiling: ₹{budget}
          </label>
          <input
            type="range" min="3000" max="6000" step="100"
            value={budget} onChange={(e) => setBudget(e.target.value)}
            style={{ width: '100%', accentColor: 'var(--brand-primary)' }}
          />
        </div>

        <div style={{ width: '180px' }}>
          <label style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
            Urgency / Strategy
          </label>
          <select
            value={urgency} onChange={(e) => setUrgency(e.target.value)}
            style={{
              width: '100%', padding: '9px 12px', borderRadius: '8px',
              background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-subtle)',
              color: 'var(--text-main)', fontSize: '0.82rem', outline: 'none'
            }}
          >
            <option value="NORMAL">Balanced / Quality</option>
            <option value="HIGH_URGENCY">⚡ 24h Air Express Urgency</option>
            <option value="STRICT_BUDGET">💰 Lowest Price Maximizer</option>
          </select>
        </div>

        <button
          onClick={startNegotiation}
          disabled={isNegotiating}
          className="btn-primary"
          style={{ padding: '10px 20px', marginTop: '16px', fontSize: '0.88rem', height: '40px' }}
        >
          {isNegotiating ? (
            <>
              <Sparkles size={16} className="pulse-active" /> Bargaining...
            </>
          ) : (
            <>
              <Send size={16} /> Run Live Negotiation
            </>
          )}
        </button>
      </div>

      {/* Negotiation Timeline Arena */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* Rounds Stream */}
        {[1, 2, 3].map((roundNum) => {
          if (roundNum > visibleRounds && isNegotiating) return null;
          const roundBids = sessionResult?.dialogue_timeline?.filter(b => b.round_number === roundNum) || [];

          return (
            <div key={roundNum} className="animate-slide-up" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* Round Divider */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: '12px',
                padding: '4px 0', borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
              }}>
                <span className="badge badge-primary" style={{ fontSize: '0.7rem', padding: '2px 8px' }}>
                  Round {roundNum}
                </span>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', fontWeight: '600' }}>
                  {roundNum === 1 && "RFQ Broadcast & Initial Merchant Quotations"}
                  {roundNum === 2 && "Buyer Counter-Pressure & Merchant Concession Round"}
                  {roundNum === 3 && "Final Pareto-Optimal Contract Award"}
                </span>
              </div>

              {/* Dialogue Bubbles in this round */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {roundBids.map((bid, bIdx) => {
                  const speakerMeta = getSpeakerBadge(bid.speaker);
                  const SpeakerIcon = speakerMeta.icon;
                  const isAgreement = bid.action === 'FINAL_AGREEMENT';

                  return (
                    <div
                      key={bIdx}
                      style={{
                        background: isAgreement ? 'rgba(16, 185, 129, 0.14)' : 'rgba(0, 0, 0, 0.35)',
                        border: `1px solid ${isAgreement ? '#34d399' : 'var(--border-subtle)'}`,
                        borderRadius: '12px',
                        padding: '14px 18px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '8px'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{
                            padding: '3px 8px', borderRadius: '6px', fontSize: '0.7rem',
                            fontWeight: '700', background: speakerMeta.bg, color: speakerMeta.color,
                            display: 'flex', alignItems: 'center', gap: '5px'
                          }}>
                            <SpeakerIcon size={12} /> {speakerMeta.name}
                          </span>
                          <span className="badge" style={{ fontSize: '0.65rem', background: 'rgba(255,255,255,0.06)' }}>
                            {bid.action}
                          </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                          <span className="text-mono" style={{ fontSize: '0.82rem', fontWeight: '800', color: '#34d399' }}>
                            ₹{bid.offered_price_inr?.toLocaleString('en-IN')}
                          </span>
                          {bid.shipping_cost_inr === 0 ? (
                            <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>FREE SHIPPING</span>
                          ) : (
                            <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>+₹{bid.shipping_cost_inr} ship</span>
                          )}
                        </div>
                      </div>

                      <p style={{ fontSize: '0.82rem', color: 'var(--text-main)', lineHeight: '1.5' }}>
                        {bid.message}
                      </p>

                      {/* Perks */}
                      {bid.perks?.length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '2px' }}>
                          {bid.perks.map((perk, pIdx) => (
                            <span key={pIdx} style={{
                              fontSize: '0.68rem', color: '#38bdf8',
                              background: 'rgba(56, 189, 248, 0.1)', padding: '2px 8px', borderRadius: '4px',
                              border: '1px solid rgba(56, 189, 248, 0.2)'
                            }}>
                              ✓ {perk}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}

        {/* Final Decision Award Banner */}
        {sessionResult && visibleRounds === 3 && (
          <div className="animate-slide-up" style={{
            background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(0, 210, 211, 0.15))',
            border: '1px solid #34d399',
            borderRadius: '14px',
            padding: '20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Award size={20} color="#34d399" />
                <span style={{ fontSize: '0.95rem', fontWeight: '800', color: '#34d399' }}>
                  Winning Merchant Contract: {sessionResult.winning_merchant}
                </span>
              </div>
              <p style={{ fontSize: '0.82rem', color: '#cbd5e1', marginTop: '4px' }}>
                {sessionResult.winning_product_name} • Agreed: <strong>₹{sessionResult.final_agreed_price_inr?.toLocaleString('en-IN')}</strong> (Saved ₹{sessionResult.total_savings_inr})
              </p>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {sessionResult.verdict_explanation}
              </div>
            </div>

            <button
              onClick={handleOrderWinningDeal}
              className="btn-primary"
              style={{ padding: '12px 24px', fontSize: '0.9rem', justifyContent: 'center' }}
            >
              <ShieldCheck size={18} /> Execute Negotiated Order
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

