"use client";
import React, { useState, useEffect } from 'react';
import { ShoppingCart, Store, Trash2, Plus, ArrowRight, ShieldCheck, Zap, Split, Award, CheckCircle2, TrendingDown, Percent, CreditCard } from 'lucide-react';

const SAMPLE_INITIAL_ITEMS = [
  {
    id: "ci_1",
    product_id: "nt_kb_01",
    product_name: "KeyChron K2 Pro Mechanical Keyboard",
    category: "Electronics",
    merchant_id: "merchant_novatech",
    merchant_name: "NovaTech Gear",
    price_inr: 3899.0,
    shipping_cost_inr: 150.0,
    quantity: 1,
    bundle_selected: true,
    bundle_item_name: "Walnut Palm Rest (+₹499)",
    bundle_price_inr: 499.0
  },
  {
    id: "ci_2",
    product_id: "bf_anc_01",
    product_name: "ByteForge Studio ANC Pro Headphones",
    category: "Electronics",
    merchant_id: "merchant_byteforge",
    merchant_name: "ByteForge Electronics",
    price_inr: 3999.0,
    shipping_cost_inr: 0.0,
    quantity: 1,
    bundle_selected: false,
    bundle_price_inr: 0.0
  },
  {
    id: "ci_3",
    product_id: "dd_desk_01",
    product_name: "DevDesk HyperGlide Merino Desk Mat",
    category: "Accessories",
    merchant_id: "merchant_devdesk",
    merchant_name: "DevDesk Supply Co.",
    price_inr: 449.0,
    shipping_cost_inr: 0.0,
    quantity: 1,
    bundle_selected: false,
    bundle_price_inr: 0.0
  }
];

export function MultiMerchantCartView({ onExecutePurchase, onTriggerCheckout }) {
  const [items, setItems] = useState(SAMPLE_INITIAL_ITEMS);
  const [cartOptimization, setCartOptimization] = useState(null);
  const [selectedStrategy, setSelectedStrategy] = useState("COST"); // "COST" | "SPEED"
  const [isLoading, setIsLoading] = useState(false);

  const fetchOptimization = async (currentItems) => {
    setIsLoading(true);
    try {
      const res = await fetch('/api/agent/cart/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: currentItems })
      });
      const data = await res.json();
      setCartOptimization(data);
    } catch (e) {
      console.error('Cart evaluate error:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchOptimization(items);
  }, [items]);

  const handleRemoveItem = (id) => {
    const next = items.filter(i => i.id !== id);
    setItems(next);
  };

  const handleCheckoutCart = () => {
    if (!cartOptimization) return;
    const totalAmount = selectedStrategy === "SPEED" 
      ? cartOptimization.speed_optimized_plan.total_inr 
      : cartOptimization.final_payable_inr;

    const simulatedOrder = {
      order_id: cartOptimization.cart_id,
      item_name: `Multi-Merchant Unified Cart (${cartOptimization.total_items_count} items across ${cartOptimization.merchant_breakdown?.length} sellers)`,
      total_paid_inr: totalAmount,
      merchant: `Razorpay Route Multi-Split (${cartOptimization.merchant_breakdown?.map(m => m.merchant_name).join(', ')})`,
      split_transfers: cartOptimization.split_transfers
    };

    if (onTriggerCheckout) {
      onTriggerCheckout(simulatedOrder);
    }
  };

  return (
    <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 24px 32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header Info */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '38px', height: '38px', borderRadius: '10px',
            background: 'linear-gradient(135deg, #00d2d3, #0284c7)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <ShoppingCart size={22} color="#04131d" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '800', letterSpacing: '-0.02em' }}>
              Multi-Merchant Virtual Cart & Split Settlement
            </h2>
            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              Cross-merchant basket routing powered by Razorpay Route A2A Atomic Transfers
            </p>
          </div>
        </div>

        {cartOptimization && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span className="badge badge-success" style={{ fontSize: '0.75rem', padding: '6px 12px' }}>
              <Percent size={13} /> Saved ₹{cartOptimization.combo_discount_inr} Multi-Merchant Combo Discount
            </span>
          </div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.35fr 1fr', gap: '24px' }}>
        
        {/* Left Column: Virtual Cart Items by Merchant */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Cart Items ({items.length} Products from {cartOptimization?.merchant_breakdown?.length || 3} Merchants)
          </h3>

          {cartOptimization?.merchant_breakdown?.map((group) => (
            <div key={group.merchant_id} className="glass-panel animate-slide-up" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
              
              {/* Merchant Title & Route Sub-Account */}
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '10px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Store size={16} color="var(--brand-primary)" />
                  <span style={{ fontWeight: '700', fontSize: '0.9rem' }}>{group.merchant_name}</span>
                </div>
                <div className="text-mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>
                  Route ID: <span style={{ color: '#38bdf8' }}>{group.account_id}</span>
                </div>
              </div>

              {/* Items in this merchant group */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {group.items.map((item) => (
                  <div key={item.id} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    background: 'rgba(0,0,0,0.3)', padding: '10px 14px', borderRadius: '8px',
                    border: '1px solid var(--border-subtle)'
                  }}>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '0.85rem' }}>{item.product_name}</div>
                      {item.bundle_selected && (
                        <div style={{ fontSize: '0.72rem', color: '#38bdf8', marginTop: '2px' }}>
                          + Bundle: {item.bundle_item_name}
                        </div>
                      )}
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '2px' }}>
                        Qty: {item.quantity} • Category: {item.category}
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontWeight: '700', fontSize: '0.9rem', color: '#34d399' }}>
                          ₹{((item.price_inr + (item.bundle_selected ? item.bundle_price_inr : 0)) * item.quantity).toLocaleString('en-IN')}
                        </div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                          {item.shipping_cost_inr === 0 ? 'Free Shipping' : `+₹${item.shipping_cost_inr} ship`}
                        </div>
                      </div>
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        style={{ background: 'transparent', border: 'none', color: '#f87171', cursor: 'pointer', padding: '4px' }}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Merchant Subtotal */}
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)', paddingTop: '6px' }}>
                <span>Subtotal: ₹{group.subtotal_inr.toLocaleString('en-IN')} • Shipping: ₹{group.shipping_inr}</span>
                <span style={{ fontWeight: '700', color: 'var(--text-main)' }}>
                  Merchant Total: ₹{group.merchant_total_inr.toLocaleString('en-IN')} ({group.split_transfer_share_pct}%)
                </span>
              </div>
            </div>
          ))}
        </div>

        {/* Right Column: Smart Optimizer & Razorpay Route Split Breakdown */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Smart Routing & Settlement
          </h3>

          {/* Strategy Selector */}
          <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ fontSize: '0.78rem', fontWeight: '700', color: 'var(--text-muted)' }}>
              Optimization Strategy
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
              <div
                onClick={() => setSelectedStrategy("COST")}
                style={{
                  padding: '12px', borderRadius: '8px', cursor: 'pointer',
                  background: selectedStrategy === "COST" ? 'rgba(0, 210, 211, 0.15)' : 'rgba(0,0,0,0.3)',
                  border: `1px solid ${selectedStrategy === "COST" ? 'var(--brand-primary)' : 'var(--border-subtle)'}`
                }}
              >
                <div style={{ fontWeight: '700', fontSize: '0.82rem', color: 'var(--brand-primary)' }}>
                  ◆ Lowest Cost
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  ₹{cartOptimization?.final_payable_inr?.toLocaleString('en-IN')} • 2-3 days
                </div>
              </div>

              <div
                onClick={() => setSelectedStrategy("SPEED")}
                style={{
                  padding: '12px', borderRadius: '8px', cursor: 'pointer',
                  background: selectedStrategy === "SPEED" ? 'rgba(249, 115, 22, 0.15)' : 'rgba(0,0,0,0.3)',
                  border: `1px solid ${selectedStrategy === "SPEED" ? '#f97316' : 'var(--border-subtle)'}`
                }}
              >
                <div style={{ fontWeight: '700', fontSize: '0.82rem', color: '#f97316' }}>
                  ✦ Air Express
                </div>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                  ₹{cartOptimization?.speed_optimized_plan?.total_inr?.toLocaleString('en-IN')} • 24 hours
                </div>
              </div>
            </div>
          </div>

          {/* Razorpay Route Split Settlement Table */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Split size={16} color="#38bdf8" />
                <span style={{ fontSize: '0.85rem', fontWeight: '700' }}>
                  Razorpay Route Split Transfers
                </span>
              </div>
              <span className="badge badge-primary" style={{ fontSize: '0.65rem' }}>
                Escrow-Free
              </span>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {cartOptimization?.split_transfers?.map((st, sIdx) => (
                <div key={sIdx} style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  background: 'rgba(0,0,0,0.4)', padding: '10px 12px', borderRadius: '8px',
                  border: '1px solid var(--border-subtle)', fontSize: '0.75rem'
                }}>
                  <div>
                    <div style={{ fontWeight: '700', color: '#cbd5e1' }}>{st.merchant_name}</div>
                    <div className="text-mono" style={{ fontSize: '0.68rem', color: 'var(--text-dim)' }}>
                      {st.account_id} • Fee: ₹{st.platform_fee_inr}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: '800', color: '#34d399' }}>
                      ₹{st.amount_inr.toLocaleString('en-IN')}
                    </div>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                      Net: ₹{st.net_transfer_inr}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Price Summary Calculation */}
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span>Grand Subtotal:</span>
                <span>₹{cartOptimization?.grand_subtotal_inr?.toLocaleString('en-IN')}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)' }}>
                <span>Consolidated Shipping:</span>
                <span>₹{cartOptimization?.grand_shipping_inr}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', color: '#34d399' }}>
                <span>Multi-Merchant Combo Discount:</span>
                <span>-₹{cartOptimization?.combo_discount_inr}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.05rem', fontWeight: '800', color: '#fff', marginTop: '6px' }}>
                <span>Total Payable:</span>
                <span style={{ color: '#34d399' }}>
                  ₹{(selectedStrategy === "SPEED" ? cartOptimization?.speed_optimized_plan?.total_inr : cartOptimization?.final_payable_inr)?.toLocaleString('en-IN')}
                </span>
              </div>
            </div>

            {/* Checkout Action Button */}
            <button
              onClick={handleCheckoutCart}
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '0.95rem', marginTop: '6px' }}
            >
              <CreditCard size={18} /> Checkout Unified Cart on Razorpay
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

