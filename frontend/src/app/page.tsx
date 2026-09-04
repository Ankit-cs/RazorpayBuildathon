"use client";

import React, { useState } from 'react';
import { ConversationalChat } from '../components/verity/ConversationalChat';
import { A2ANegotiationView } from '../components/verity/A2ANegotiationView';
import { MultiMerchantCartView } from '../components/verity/MultiMerchantCartView';
import { LiveExecutionTrace } from '../components/verity/LiveExecutionTrace';
import { PoPIBadgeModal } from '../components/verity/PoPIBadgeModal';

export default function Home() {
  const [activeTab, setActiveTab] = useState('chat');
  const [popiOpen, setPopiOpen] = useState(false);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-primary)' }}>
      {/* Header */}
      <header className="app-header">
        <div className="header-left">
          <div className="brand-logo">
            <div className="logo-pulse"></div>
            <span style={{ fontWeight: 800, color: 'var(--accent-primary)', letterSpacing: '-0.5px' }}>ProjectX</span>
            <span style={{ color: 'var(--text-dim)', marginLeft: '8px', fontSize: '0.9rem' }}>Enterprise Agentic Commerce</span>
          </div>
        </div>
        
        <div className="tab-nav">
          <button 
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            Voice Agent
          </button>
          <button 
            className={`tab-btn ${activeTab === 'negotiate' ? 'active' : ''}`}
            onClick={() => setActiveTab('negotiate')}
          >
            A2A Negotiation
          </button>
          <button 
            className={`tab-btn ${activeTab === 'cart' ? 'active' : ''}`}
            onClick={() => setActiveTab('cart')}
          >
            Multi-Merchant Cart
          </button>
          <button 
            className={`tab-btn ${activeTab === 'trace' ? 'active' : ''}`}
            onClick={() => setActiveTab('trace')}
          >
            Live Trace
          </button>
        </div>

        <div className="header-actions">
          <button className="icon-btn" onClick={() => setPopiOpen(true)} title="PoPI Verification">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '24px', display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'chat' && (
          <ConversationalChat onSelectTab={setActiveTab} onExecutePurchase={undefined} />
        )}
        {activeTab === 'negotiate' && (
          <A2ANegotiationView onSelectTab={setActiveTab} onExecutePurchase={undefined} />
        )}
        {activeTab === 'cart' && (
          <MultiMerchantCartView onExecutePurchase={undefined} onTriggerCheckout={undefined} />
        )}
        {activeTab === 'trace' && (
          <div style={{ padding: '20px', background: 'var(--bg-secondary)', borderRadius: '16px' }}>
            <h2 style={{ color: 'var(--text-primary)', marginBottom: '20px' }}>Agentic Execution Trace</h2>
            <LiveExecutionTrace executionResponse={undefined} isRunning={undefined} onTriggerCheckout={undefined} />
          </div>
        )}
      </main>

      {/* Modals */}
      <PoPIBadgeModal isOpen={popiOpen} onClose={() => setPopiOpen(false)} popiData={undefined} actualTotal={undefined} actualShipping={undefined} actualCategory={undefined} />

      {/* Footer */}
      <footer style={{
        padding: '20px 24px',
        textAlign: 'center',
        color: 'var(--text-dim)',
        fontSize: '0.75rem',
        borderTop: '1px solid var(--border-subtle)',
        marginTop: 'auto'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <span><strong>ProjectX</strong> — Enterprise AI Integration</span>
          <span>•</span>
          <span style={{ color: '#34d399' }}>Proof-of-Policy (PoPI) Invariant Gate</span>
          <span>•</span>
          <span style={{ color: '#c084fc' }}>NIST FIPS 204 Lattice Cryptography</span>
        </div>
      </footer>
    </div>
  );
}
