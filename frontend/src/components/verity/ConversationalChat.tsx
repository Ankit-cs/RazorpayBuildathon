"use client";
import React, { useState, useEffect, useRef } from 'react';
import { Bot, Send, Sparkles, User, ShoppingBag, ArrowRight, ShieldCheck, Zap, RefreshCw, Layers, Mic, MicOff, Volume2, VolumeX, Radio, ArrowLeftRight, CreditCard, Award } from 'lucide-react';

export function ConversationalChat({ onExecutePurchase, onSelectTab }) {
  const [messages, setMessages] = useState([
    {
      id: 'init_1',
      role: 'agent',
      content: "✦ System Initialized: **VERITY** — Autonomous AI Buyer & Procurement Agent on Razorpay Rails.\n\nI dynamically navigate federated merchant catalogs, negotiate multi-round concessions with seller agents, and enforce strict mathematical spending invariants (PoPI) before checkouts.\n\n**Sample Directives:**\n• *\"Buy a wireless mechanical keyboard under ₹4,500\"*\n• *\"Negotiate the best deal for ANC headphones\"*\n• *\"What is the warranty policy for KeyChron keyboards?\"*",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      data: null
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [budget, setBudget] = useState(5000);
  const [isListening, setIsListening] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [detectedSentiment, setDetectedSentiment] = useState("BALANCED");
  const chatEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const speakText = (text) => {
    if (!ttsEnabled || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*_#`✦•▪]/g, '').slice(0, 200);
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
  };

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech Recognition API is not supported in this browser. Please use Chrome/Edge.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      setInput(transcript);
      setIsListening(false);
      handleSend(transcript);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;
    recognition.start();
  };

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Real-time sentiment detection
  useEffect(() => {
    const l = input.toLowerCase();
    if (l.includes('urgent') || l.includes('asap') || l.includes('fast') || l.includes('emergency')) {
      setDetectedSentiment("⚡ HIGH URGENCY");
    } else if (l.includes('cheap') || l.includes('budget') || l.includes('lowest') || l.includes('discount')) {
      setDetectedSentiment("◆ STRICT BUDGET");
    } else if (input.trim().length > 0) {
      setDetectedSentiment("✦ BALANCED QUALITY");
    } else {
      setDetectedSentiment("NORMAL");
    }
  }, [input]);

  const handleSend = async (textToSend) => {
    const text = typeof textToSend === 'string' ? textToSend : input;
    if (!text.trim() || isTyping) return;

    const userMsg = {
      id: 'user_' + Date.now(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const res = await fetch('/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, budget: parseFloat(budget) })
      });
      const data = await res.json();

      const agentMsg = {
        id: 'agent_' + Date.now(),
        role: 'agent',
        content: data.content,
        intent: data.intent,
        data: data.data,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, agentMsg]);
      speakText(data.content);
    } catch (e) {
      setMessages(prev => [...prev, {
        id: 'err_' + Date.now(),
        role: 'agent',
        content: "▪ Communication error with the agent service. Please ensure FastAPI is running on port 8000.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleQuickPurchase = (promptText, maxBudget = 4500) => {
    onExecutePurchase({
      user_prompt: promptText,
      spending_policy: {
        max_budget_inr: maxBudget,
        max_shipping_inr: 200,
        allowed_categories: ['Electronics', 'Peripherals', 'Accessories'],
        require_warranty: true,
        allow_bundle_upsell: true
      },
      include_upsell_bundle: true,
      force_failure_simulation: null
    });
    if (onSelectTab) onSelectTab('studio');
  };

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', padding: '0 24px 28px' }}>
      <div className="glass-panel animate-slide-up" style={{ height: '78vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* Chat Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          background: 'rgba(0, 0, 0, 0.25)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '32px', height: '32px', borderRadius: '8px',
              background: 'linear-gradient(135deg, #00d2d3, #0284c7)',
              display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <Bot size={18} color="#04131d" />
            </div>
            <div>
              <div style={{ fontWeight: '700', fontSize: '0.92rem' }}>VERITY Autonomous Assistant</div>
              <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>
                Conversational Commerce & Voice Procurement Engine
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {detectedSentiment !== "NORMAL" && (
              <span className="badge badge-primary" style={{ fontSize: '0.68rem' }}>
                Intent: {detectedSentiment}
              </span>
            )}
            <button
              onClick={() => setTtsEnabled(!ttsEnabled)}
              style={{ background: 'transparent', border: 'none', color: ttsEnabled ? 'var(--brand-primary)' : 'var(--text-dim)', cursor: 'pointer' }}
              title={ttsEnabled ? "TTS Audio Enabled" : "TTS Audio Muted"}
            >
              {ttsEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
            </button>
          </div>
        </div>

        {/* Messages Scroll Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((m) => {
            const isUser = m.role === 'user';
            return (
              <div
                key={m.id}
                style={{
                  display: 'flex',
                  gap: '10px',
                  alignSelf: isUser ? 'flex-end' : 'flex-start',
                  maxWidth: '82%'
                }}
              >
                {!isUser && (
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%',
                    background: 'rgba(0, 210, 211, 0.2)', color: 'var(--brand-primary)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                  }}>
                    <Bot size={15} />
                  </div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <div style={{
                    background: isUser ? 'linear-gradient(135deg, #0284c7, #0369a1)' : 'rgba(20, 30, 48, 0.75)',
                    color: isUser ? '#fff' : 'var(--text-main)',
                    padding: '12px 16px',
                    borderRadius: isUser ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                    fontSize: '0.86rem',
                    lineHeight: '1.5',
                    border: isUser ? 'none' : '1px solid var(--border-subtle)',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {m.content}

                    {/* Quick Action Button for Purchase Intent */}
                    {m.intent === 'PURCHASE_INTENT' && m.data?.product && (
                      <div style={{ marginTop: '12px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                        <button
                          onClick={() => handleQuickPurchase(m.data.prompt, m.data.budget)}
                          className="btn-primary"
                          style={{ padding: '6px 14px', fontSize: '0.75rem' }}
                        >
                          <ShieldCheck size={14} /> Buy with Bounded Policy
                        </button>
                        <button
                          onClick={() => onSelectTab && onSelectTab('negotiate')}
                          className="btn-secondary"
                          style={{ padding: '6px 14px', fontSize: '0.75rem' }}
                        >
                          <ArrowLeftRight size={14} /> Run A2A Negotiation
                        </button>
                      </div>
                    )}
                  </div>
                  <span suppressHydrationWarning style={{ fontSize: '0.68rem', color: 'var(--text-dim)', alignSelf: isUser ? 'flex-end' : 'flex-start' }}>
                    {m.timestamp}
                  </span>
                </div>

                {isUser && (
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%',
                    background: 'rgba(255, 255, 255, 0.1)', color: '#fff',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                  }}>
                    <User size={15} />
                  </div>
                )}
              </div>
            );
          })}
          {isTyping && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
              <Sparkles size={14} className="pulse-active" /> VERITY is deliberating with catalogs...
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input Bar */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'rgba(0, 0, 0, 0.35)',
          display: 'flex',
          alignItems: 'center',
          gap: '10px'
        }}>
          <button
            onClick={toggleListening}
            style={{
              width: '42px', height: '42px', borderRadius: '10px',
              background: isListening ? 'rgba(239, 68, 68, 0.25)' : 'rgba(255, 255, 255, 0.06)',
              border: isListening ? '1px solid #f87171' : '1px solid var(--border-subtle)',
              color: isListening ? '#f87171' : 'var(--brand-primary)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              cursor: 'pointer', flexShrink: 0
            }}
            title="Click to speak (Voice Shopping)"
          >
            {isListening ? <Radio size={18} className="pulse-active" /> : <Mic size={18} />}
          </button>

          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSend(); }}
            placeholder="Type or speak a purchase directive (e.g. 'Find me the best keyboard under ₹4,000')..."
            style={{
              flex: 1, padding: '12px 16px', borderRadius: '10px',
              background: 'rgba(0,0,0,0.5)', border: '1px solid var(--border-subtle)',
              color: 'var(--text-main)', fontSize: '0.88rem', outline: 'none'
            }}
          />

          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isTyping}
            className="btn-primary"
            style={{ padding: '12px 18px', flexShrink: 0 }}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

