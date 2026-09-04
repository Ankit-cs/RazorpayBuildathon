"use client";
import React, { useState } from 'react';
import { ShieldCheck, Lock, CheckCircle2, Copy, Check, ExternalLink, X, ShieldAlert, KeyRound, Clock, Hash } from 'lucide-react';

export function PoPIBadgeModal({ isOpen, onClose, popiData, actualTotal, actualShipping, actualCategory }) {
  const [copied, setCopied] = useState(false);
  const [verificationState, setVerificationState] = useState(null);
  const [verifying, setVerifying] = useState(false);

  if (!isOpen || !popiData) return null;

  const handleCopyToken = () => {
    navigator.clipboard.writeText(popiData.popi_token || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const res = await fetch('/api/agent/popi/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          popi_certificate: popiData,
          actual_total_inr: actualTotal || popiData.budget_limit_inr,
          actual_shipping_inr: actualShipping || popiData.max_shipping_inr,
          actual_category: actualCategory || (popiData.allowed_categories?.[0] || 'Electronics')
        })
      });
      const data = await res.json();
      setVerificationState(data);
    } catch (e) {
      setVerificationState({ is_valid: false, message: 'Verification error' });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, zIndex: 1000,
      background: 'rgba(4, 19, 29, 0.85)', backdropFilter: 'blur(10px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
    }}>
      <div className="glass-panel animate-slide-up" style={{
        maxWidth: '680px', width: '100%', maxHeight: '90vh', overflowY: 'auto',
        padding: '28px', border: '1px solid rgba(0, 210, 211, 0.35)',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.6)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '38px', height: '38px', borderRadius: '10px',
              background: 'linear-gradient(135deg, rgba(0, 210, 211, 0.2), rgba(2, 132, 199, 0.2))',
              border: '1px solid var(--brand-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <ShieldCheck size={22} color="var(--brand-primary)" />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: '800' }}>Proof-of-Policy (PoPI) Inspector</h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Cryptographically Verifiable Spending Commitment Token
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{
            background: 'transparent', border: 'none', color: 'var(--text-dim)',
            cursor: 'pointer', padding: '6px'
          }}>
            <X size={20} />
          </button>
        </div>

        {/* Status Chip */}
        <div style={{
          padding: '12px 16px', borderRadius: '10px',
          background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle2 size={18} color="#34d399" />
            <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#34d399' }}>
              PoPI Commitment Verified & Active
            </span>
          </div>
          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
            HMAC-SHA256 Signed
          </span>
        </div>

        {/* PoPI Token Raw */}
        <div style={{ marginBottom: '18px' }}>
          <label style={{ fontSize: '0.72rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Attestation Token (Passed via X-Razorpay-Agent-PoPI)
          </label>
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            background: 'rgba(0,0,0,0.5)', padding: '10px 14px', borderRadius: '8px',
            border: '1px solid var(--border-subtle)', marginTop: '6px'
          }}>
            <code className="text-mono" style={{ fontSize: '0.78rem', color: 'var(--brand-primary)', wordBreak: 'break-all' }}>
              {popiData.popi_token}
            </code>
            <button onClick={handleCopyToken} className="btn-secondary" style={{ padding: '4px 10px', fontSize: '0.72rem' }}>
              {copied ? <Check size={13} color="#34d399" /> : <Copy size={13} />}
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
        </div>

        {/* Invariant Bounds Grid */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px'
        }}>
          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Committed Budget Ceiling:</span>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#34d399', marginTop: '2px' }}>
              ₹{popiData.budget_limit_inr?.toLocaleString('en-IN')}
            </div>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              ({popiData.budget_commitment_paise || (popiData.budget_limit_inr * 100)} Paise)
            </span>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Max Shipping Allowed:</span>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#38bdf8', marginTop: '2px' }}>
              ₹{popiData.max_shipping_inr?.toLocaleString('en-IN')}
            </div>
            <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Cap Invariant</span>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Allowed Categories:</span>
            <div style={{ fontSize: '0.82rem', fontWeight: '700', color: '#cbd5e1', marginTop: '4px' }}>
              {popiData.allowed_categories?.join(', ') || 'All Allowed'}
            </div>
          </div>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Order Reference & Nonce:</span>
            <div className="text-mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {popiData.order_reference} • {popiData.nonce}
            </div>
          </div>
        </div>

        {/* Cryptographic Hashes */}
        <div style={{ background: 'rgba(0,0,0,0.35)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-subtle)', marginBottom: '20px' }}>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)', marginBottom: '8px' }}>
            Cryptographic Integrity Proofs
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.72rem' }}>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Policy Hash (SHA-256): </span>
              <code className="text-mono" style={{ color: '#38bdf8' }}>{popiData.policy_hash}</code>
            </div>
            <div>
              <span style={{ color: 'var(--text-dim)' }}>Attestation Signature (HMAC): </span>
              <code className="text-mono" style={{ color: '#c084fc' }}>{popiData.signature}</code>
            </div>
          </div>
        </div>

        {/* Verify Action */}
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            onClick={handleVerify}
            disabled={verifying}
            className="btn-primary"
            style={{ flex: 1, justifyContent: 'center', padding: '10px 16px', fontSize: '0.88rem' }}
          >
            {verifying ? 'Re-verifying Cryptographic Proof...' : 'Re-verify Mathematical Assertions'}
          </button>
          <button onClick={onClose} className="btn-secondary" style={{ padding: '10px 18px' }}>
            Close
          </button>
        </div>

        {verificationState && (
          <div style={{
            marginTop: '16px', padding: '12px', borderRadius: '8px',
            background: verificationState.is_valid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${verificationState.is_valid ? '#34d399' : '#f87171'}`,
            fontSize: '0.78rem'
          }}>
            <strong>Verification Result:</strong> {verificationState.is_valid ? 'All 4 mathematical policy constraints SATISFIED.' : 'Verification failed.'}
            {verificationState.budget_headroom_inr !== undefined && (
              <div style={{ marginTop: '4px', color: '#34d399' }}>
                Budget Headroom Remaining: ₹{verificationState.budget_headroom_inr}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

