"use client";
import React from 'react';
import { Sparkles, CheckCircle2, Award, ArrowRight, ShieldCheck, Truck, Tag, TrendingUp, Info } from 'lucide-react';

export function ExplainableDecisionCard({ decision, finalOrder }) {
  if (!decision) return null;

  return (
    <div className="glass-panel" style={{
      padding: '20px',
      borderRadius: '14px',
      border: '1px solid rgba(0, 210, 211, 0.25)',
      background: 'linear-gradient(135deg, rgba(20, 30, 48, 0.6) 0%, rgba(4, 19, 29, 0.8) 100%)',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px', height: '32px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #00d2d3, #0284c7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Sparkles size={16} color="#04131d" />
          </div>
          <div>
            <h4 style={{ fontSize: '0.95rem', fontWeight: '800', letterSpacing: '-0.02em' }}>
              Explainable AI Decision Rationale
            </h4>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
              Deterministic Evaluation across {decision.products_considered_count || 3} Merchant Offers
            </span>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
            <Award size={11} /> Confidence: {Math.round((decision.confidence_score || 0.98) * 100)}%
          </span>
        </div>
      </div>

      {/* Why Selected Won */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.35)',
        padding: '14px 16px',
        borderRadius: '10px',
        border: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem', fontWeight: '700', color: 'var(--brand-primary)' }}>
          <Award size={15} /> Winning Deal: {decision.selected_product_name}
        </div>
        <p style={{ fontSize: '0.78rem', color: 'var(--text-main)', lineHeight: '1.5' }}>
          {decision.why_selected_won}
        </p>
      </div>

      {/* Comparisons Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div style={{ background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: '700', color: '#38bdf8' }}>
            <Tag size={13} /> Price Analysis
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: '1.4' }}>
            {decision.price_comparison_summary}
          </p>
        </div>

        <div style={{ background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.72rem', fontWeight: '700', color: '#34d399' }}>
            <Truck size={13} /> Shipping SLA
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: '1.4' }}>
            {decision.shipping_sla_summary}
          </p>
        </div>
      </div>

      {/* Policy Invariants Verified */}
      <div>
        <div style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.05em' }}>
          Mathematical Assertions Satisfied (Zero-Hallucination Gate)
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {decision.policy_checks_passed?.map((chk, idx) => (
            <div key={idx} style={{
              display: 'flex', alignItems: 'center', gap: '5px',
              background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.25)',
              padding: '4px 10px', borderRadius: '6px', fontSize: '0.72rem', color: '#34d399'
            }}>
              <CheckCircle2 size={12} /> {chk}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

