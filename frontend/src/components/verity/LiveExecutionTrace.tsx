"use client";
import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, ArrowRight, ShieldCheck, CreditCard, Sparkles, RefreshCw, ExternalLink, Lock, Shield, Cpu, ChevronDown, ChevronUp, BookOpen, Award } from 'lucide-react';
import { PoPIBadgeModal } from './PoPIBadgeModal';
import { ExplainableDecisionCard } from './ExplainableDecisionCard';

export function LiveExecutionTrace({ executionResponse, isRunning, onTriggerCheckout }) {
  const [popiModalOpen, setPopiModalOpen] = useState(false);
  const [showRAGSnippets, setShowRAGSnippets] = useState(false);

  if (isRunning) {
    return (
      <div className="glass-panel" style={{ padding: '40px 30px', minHeight: '420px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '16px' }}>
        <div style={{
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          border: '3px solid rgba(0, 210, 211, 0.2)',
          borderTopColor: 'var(--brand-primary)',
          animation: 'spin 1s linear infinite'
        }} />
        <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
        <p style={{ fontWeight: '700', color: 'var(--brand-primary)', fontSize: '1rem' }}>
          Autonomous Buyer Agent Transacting...
        </p>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Retrieving RAG knowledge, bargaining via A2A, generating PoPI commitment & routing on Razorpay
        </p>
      </div>
    );
  }

  if (!executionResponse) {
    return (
      <div className="glass-panel" style={{ padding: '40px 24px', minHeight: '420px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', gap: '12px' }}>
        <div style={{
          width: '50px',
          height: '50px',
          borderRadius: '14px',
          background: 'rgba(255,255,255,0.04)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--text-dim)'
        }}>
          <Sparkles size={24} />
        </div>
        <h3 style={{ fontSize: '1.05rem', fontWeight: '700', color: 'var(--text-muted)' }}>
          Autonomous Execution Trace & PoPI Gate
        </h3>
        <p style={{ fontSize: '0.82rem', color: 'var(--text-dim)', maxWidth: '340px', lineHeight: '1.5' }}>
          Run an autonomous purchase directive on the left to watch the Buyer Agent discover products, verify PoPI invariants, sign NIST lattice signatures, and create verified Razorpay test orders.
        </p>
      </div>
    );
  }

  const { success, status, execution_steps, final_order, recovery_plan, popi_attestation, explainable_decision, rag_context_snippets, audit_summary } = executionResponse;

  return (
    <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Execution Status Banner */}
      <div style={{
        padding: '14px 18px',
        borderRadius: '12px',
        background: success ? 'rgba(16, 185, 129, 0.12)' : 'rgba(245, 158, 11, 0.12)',
        border: `1px solid ${success ? 'rgba(16, 185, 129, 0.3)' : 'rgba(245, 158, 11, 0.3)'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '10px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {success ? (
            <CheckCircle2 size={22} color="#34d399" />
          ) : (
            <AlertTriangle size={22} color="#fbbf24" />
          )}
          <div>
            <div style={{ fontWeight: '700', fontSize: '0.9rem', color: success ? '#34d399' : '#fbbf24' }}>
              {status === 'ORDER_COMPLETED' && 'Autonomous Purchase Verified & Gated'}
              {status === 'RECOVERED_WITH_COUNTER_OFFER' && 'Graceful Failure Recovery Formulated'}
              {status === 'SECURITY_BLOCKED' && 'Adversarial Prompt-Injection Intercepted'}
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-main)', marginTop: '2px' }}>
              {audit_summary}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {popi_attestation && (
            <button
              onClick={() => setPopiModalOpen(true)}
              className="badge badge-primary"
              style={{ cursor: 'pointer', border: '1px solid var(--brand-primary)' }}
            >
              <ShieldCheck size={12} /> Inspect PoPI Token
            </button>
          )}
          <span className={`badge ${success ? 'badge-success' : 'badge-warning'}`}>
            {status}
          </span>
        </div>
      </div>

      {/* Step by Step Timeline */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <h4 style={{ fontSize: '0.85rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Execution Step Timeline
        </h4>

        {execution_steps?.map((step) => {
          const isPassed = step.status === 'COMPLETED';
          const isRecovered = step.status === 'RECOVERED';
          const isFailed = step.status === 'FAILED';

          return (
            <div
              key={step.step_number}
              style={{
                background: 'rgba(0, 0, 0, 0.3)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '10px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px'
              }}
            >
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: isPassed ? 'rgba(16, 185, 129, 0.2)' : isRecovered ? 'rgba(0, 210, 211, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                color: isPassed ? '#34d399' : isRecovered ? 'var(--brand-primary)' : '#f87171',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: '700',
                flexShrink: 0,
                marginTop: '2px'
              }}>
                {step.step_number}
              </div>

              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: '700', fontSize: '0.88rem' }}>{step.title}</span>
                  <span className="text-mono" style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                    [{step.actor}]
                  </span>
                </div>
                <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '4px', lineHeight: '1.4' }}>
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Explainable Decision Card */}
      {explainable_decision && (
        <ExplainableDecisionCard decision={explainable_decision} finalOrder={final_order} />
      )}

      {/* Final Razorpay Order Summary Card & Checkout Trigger */}
      {final_order && (
        <div style={{
          background: 'rgba(0, 0, 0, 0.45)',
          border: '1px solid rgba(0, 210, 211, 0.3)',
          borderRadius: '14px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <CreditCard size={18} color="#38bdf8" />
              <span style={{ fontWeight: '700', fontSize: '0.9rem' }}>Razorpay Test Order Ready</span>
            </div>
            <span className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--brand-primary)', background: 'rgba(0,210,211,0.1)', padding: '2px 8px', borderRadius: '4px' }}>
              {final_order.order_id}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '0.78rem' }}>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Product: </span>
              <span style={{ fontWeight: '600' }}>{final_order.item_name}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Merchant: </span>
              <span style={{ fontWeight: '600' }}>{final_order.merchant}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Base Price: </span>
              <span>₹{final_order.base_price_inr?.toLocaleString('en-IN')}</span>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Shipping: </span>
              <span>₹{final_order.shipping_cost_inr}</span>
            </div>
          </div>

          <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '10px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Total Payable:</span>
              <div style={{ fontSize: '1.25rem', fontWeight: '800', color: '#34d399' }}>
                ₹{final_order.total_paid_inr?.toLocaleString('en-IN')}
              </div>
            </div>
            <button
              onClick={() => onTriggerCheckout && onTriggerCheckout(final_order)}
              className="btn-primary"
              style={{ padding: '10px 20px', fontSize: '0.88rem' }}
            >
              <CreditCard size={16} /> Open Razorpay Test Checkout
            </button>
          </div>
        </div>
      )}

      {/* Recovery Counter-Offer Card */}
      {recovery_plan && (
        <div style={{
          background: 'rgba(245, 158, 11, 0.1)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          borderRadius: '14px',
          padding: '20px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fbbf24', fontWeight: '700', fontSize: '0.9rem' }}>
            <AlertTriangle size={18} /> Automated In-Stock Counter-Offer Formulated
          </div>
          <p style={{ fontSize: '0.78rem', color: '#cbd5e1', lineHeight: '1.4' }}>
            {recovery_plan.reason}
          </p>
          {recovery_plan.alternative_product && (
            <div style={{
              background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px',
              border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
            }}>
              <div>
                <div style={{ fontWeight: '700', fontSize: '0.85rem' }}>{recovery_plan.alternative_product.name}</div>
                <div style={{ fontSize: '0.72rem', color: '#34d399', marginTop: '2px' }}>
                  In Budget Alternative: ₹{recovery_plan.alternative_product.price_inr}
                </div>
              </div>
              <button
                onClick={() => onTriggerCheckout && onTriggerCheckout({
                  order_id: `order_rec_${Date.now()}`,
                  item_name: recovery_plan.alternative_product.name,
                  total_paid_inr: recovery_plan.alternative_product.total_inr || recovery_plan.alternative_product.price_inr,
                  merchant: 'NovaTech Gear'
                })}
                className="btn-primary"
                style={{ padding: '8px 16px', fontSize: '0.78rem' }}
              >
                Accept Counter-Offer
              </button>
            </div>
          )}
        </div>
      )}

      {/* PoPI Inspector Modal */}
      {popi_attestation && (
        <PoPIBadgeModal
          isOpen={popiModalOpen}
          onClose={() => setPopiModalOpen(false)}
          popiData={popi_attestation}
          actualTotal={final_order?.total_paid_inr}
          actualShipping={final_order?.shipping_cost_inr}
          actualCategory="Electronics"
        />
      )}
    </div>
  );
}

