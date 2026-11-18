'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { useWorkspace } from '@/context/WorkspaceContext';
import { askQuestion, getUsage } from '@/lib/api';
import { generateUUID, formatDate, getResetTimeRemaining } from '@/lib/utils';
import {
  Sparkles,
  Send,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  X,
  FileText,
  Clock,
  RotateCcw,
  CheckCircle,
  Shield,
  Layers,
  Zap,
} from 'lucide-react';

function AskContent() {
  const params = useParams();
  const workspaceId = params?.workspaceId;
  const { refreshUsage, usage } = useWorkspace();

  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentIdempotencyKey, setCurrentIdempotencyKey] = useState('');
  const [selectedSource, setSelectedSource] = useState(null);
  const [errorBanner, setErrorBanner] = useState(null);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom of chat
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async (overrideQuestion = null, overrideKey = null) => {
    const qText = overrideQuestion || question.trim();
    if (!qText || loading) return;

    setErrorBanner(null);

    // Reuse key on retry, or generate fresh UUID
    const idempotencyKey = overrideKey || generateUUID();
    setCurrentIdempotencyKey(idempotencyKey);

    // Append user message immediately
    const userMessage = {
      id: generateUUID(),
      sender: 'user',
      text: qText,
      timestamp: new Date().toISOString(),
    };

    if (!overrideQuestion) {
      setMessages((prev) => [...prev, userMessage]);
      setQuestion('');
    }

    setLoading(true);

    const res = await askQuestion(workspaceId, qText, idempotencyKey);
    setLoading(false);

    // Refresh quota counters in background
    refreshUsage();

    if (res.error) {
      if (res.status === 429) {
        // Daily Limit Exceeded
        setErrorBanner({
          type: 'quota',
          message: res.error || 'Daily question limit reached.',
          resetsAt: res.data?.resets_at,
        });
      } else if (res.status === 503) {
        // AI Provider Outage
        setErrorBanner({
          type: 'provider_error',
          message: 'The AI service is temporarily unavailable after retry attempts.',
          canRetry: true,
          failedQuestion: qText,
          failedKey: idempotencyKey,
        });
      } else {
        setErrorBanner({
          type: 'general',
          message: res.error,
        });
      }
      return;
    }

    // Process successful or unsupported response
    const botMessage = {
      id: generateUUID(),
      sender: 'ai',
      status: res.data.status, // 'answered' or 'unsupported'
      answer: res.data.answer,
      sources: res.data.sources || [],
      usage: res.data.usage,
      latency: res.data.latency_ms,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, botMessage]);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Text formatter to convert [1], [2] citations to interactive buttons
  const renderFormattedAnswer = (text, sources) => {
    if (!text) return null;

    // Split text by citation pattern like [1], [2], etc.
    const parts = text.split(/(\[\d+\])/g);

    return (
      <div style={{ lineHeight: 1.65, fontSize: '0.925rem' }}>
        {parts.map((part, index) => {
          const match = part.match(/\[(\d+)\]/);
          if (match) {
            const num = parseInt(match[1], 10);
            const source = sources.find((s) => s.n === num || s.rank === num);

            return (
              <button
                key={index}
                type="button"
                onClick={() => setSelectedSource(source || { n: num, document: 'Unknown Source' })}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.2rem',
                  padding: '0.1rem 0.45rem',
                  margin: '0 0.2rem',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(14, 165, 233, 0.15)',
                  border: '1px solid rgba(14, 165, 233, 0.35)',
                  color: 'var(--accent-cyan)',
                  cursor: 'pointer',
                  transition: 'var(--transition)',
                  verticalAlign: 'baseline',
                }}
                title={`Click to view Source [${num}]`}
              >
                <span>[{num}]</span>
              </button>
            );
          }

          return <span key={index}>{part}</span>;
        })}
      </div>
    );
  };

  return (
    <div style={{ maxWidth: '960px', margin: '0 auto', height: 'calc(100vh - 120px)', display: 'flex', flexDirection: 'column' }}>
      {/* Top Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexShrink: 0 }}>
        <div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Sparkles size={20} color="var(--primary)" />
            <span>Grounded Document Q&A</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '0.15rem' }}>
            Answers are retrieved strictly from your uploaded workspace documents with verifiable citations.
          </p>
        </div>

        {messages.length > 0 && (
          <button
            onClick={() => {
              if (confirm('Clear current conversation view?')) setMessages([]);
            }}
            className="btn btn-ghost"
            style={{ fontSize: '0.75rem', padding: '0.35rem 0.65rem' }}
          >
            <RotateCcw size={13} />
            <span>Clear Chat</span>
          </button>
        )}
      </div>

      {/* Error / Quota Banner */}
      {errorBanner && (
        <div
          style={{
            padding: '0.85rem 1.15rem',
            borderRadius: 'var(--radius-sm)',
            background: errorBanner.type === 'quota' ? 'var(--status-failed-bg)' : 'rgba(245, 158, 11, 0.15)',
            border: `1px solid ${errorBanner.type === 'quota' ? 'rgba(239, 68, 68, 0.35)' : 'rgba(245, 158, 11, 0.35)'}`,
            color: errorBanner.type === 'quota' ? '#fca5a5' : '#fde68a',
            fontSize: '0.85rem',
            marginBottom: '1rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            flexShrink: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600 }}>{errorBanner.message}</div>
              {errorBanner.resetsAt && (
                <div style={{ fontSize: '0.75rem', opacity: 0.85, marginTop: '0.15rem' }}>
                  Daily quota resets in: {getResetTimeRemaining(errorBanner.resetsAt)} (00:00 UTC)
                </div>
              )}
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            {errorBanner.canRetry && (
              <button
                onClick={() => handleSend(errorBanner.failedQuestion, errorBanner.failedKey)}
                className="btn btn-primary"
                style={{ padding: '0.35rem 0.75rem', fontSize: '0.75rem' }}
              >
                Retry
              </button>
            )}
            <button
              onClick={() => setErrorBanner(null)}
              className="btn btn-ghost"
              style={{ padding: '0.25rem' }}
            >
              <X size={15} />
            </button>
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          paddingRight: '0.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem',
          marginBottom: '1rem',
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              textAlign: 'center',
              color: 'var(--text-secondary)',
              padding: '2rem',
            }}
          >
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: '50%',
                background: 'rgba(59, 130, 246, 0.1)',
                color: 'var(--primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: '1rem',
              }}
            >
              <Sparkles size={26} />
            </div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
              Ask your workspace documents
            </h2>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '420px', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              Type any question regarding your policies, guidelines, or reports. The system will retrieve relevant chunks and cite the exact pages.
            </p>

            {/* Example Queries */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', justifyContent: 'center', maxWidth: '540px' }}>
              {[
                'How many sick leaves do employees get per year?',
                'What is the probation period policy?',
                'Who won the 2022 World Cup? (Tests unsupported threshold)',
              ].map((ex, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setQuestion(ex)}
                  className="btn btn-secondary"
                  style={{ fontSize: '0.78rem', padding: '0.45rem 0.85rem' }}
                >
                  &ldquo;{ex}&rdquo;
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => {
            if (msg.sender === 'user') {
              return (
                <div key={msg.id} style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <div
                    style={{
                      maxWidth: '75%',
                      padding: '0.85rem 1.15rem',
                      borderRadius: 'var(--radius-md)',
                      background: 'linear-gradient(135deg, #1e3a8a, #1d4ed8)',
                      color: '#ffffff',
                      fontSize: '0.925rem',
                      lineHeight: 1.5,
                      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.2)',
                    }}
                  >
                    {msg.text}
                  </div>
                </div>
              );
            }

            // AI Answer Message
            const isUnsupported = msg.status === 'unsupported';

            return (
              <div key={msg.id} style={{ display: 'flex', justifyContent: 'flex-start', maxWidth: '85%' }}>
                <div
                  className="card"
                  style={{
                    width: '100%',
                    padding: '1.25rem',
                    background: isUnsupported ? 'rgba(30, 27, 75, 0.5)' : 'var(--bg-card)',
                    borderColor: isUnsupported ? 'rgba(139, 92, 246, 0.3)' : 'var(--border-color)',
                  }}
                >
                  {/* Status & Header */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem' }}>
                      <div
                        style={{
                          width: 24,
                          height: 24,
                          borderRadius: 'var(--radius-sm)',
                          background: isUnsupported ? 'rgba(139, 92, 246, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                          color: isUnsupported ? 'var(--status-unsupported)' : 'var(--primary)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                        }}
                      >
                        <Sparkles size={13} />
                      </div>
                      <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>
                        {isUnsupported ? 'Unsupported Question' : 'Document-Grounded Answer'}
                      </span>
                    </div>

                    {isUnsupported ? (
                      <span className="badge badge-unsupported" style={{ fontSize: '0.7rem' }}>
                        Zero-Cost (No AI Call)
                      </span>
                    ) : (
                      <span className="badge badge-ready" style={{ fontSize: '0.7rem' }}>
                        Answered with Citations
                      </span>
                    )}
                  </div>

                  {/* Render Answer Text */}
                  {isUnsupported ? (
                    <div style={{ color: '#d8b4fe', fontSize: '0.9rem', lineHeight: 1.5, padding: '0.5rem 0' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.5rem' }}>
                        <HelpCircle size={16} style={{ flexShrink: 0, marginTop: '0.15rem' }} />
                        <div>
                          <strong>{msg.answer}</strong>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                            The cosine similarity score fell below the configured workspace relevance threshold. The AI provider was not called to prevent hallucinations and save cost.
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div>{renderFormattedAnswer(msg.answer, msg.sources)}</div>
                  )}

                  {/* Citations Footer Row */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                        Verified Citations ({msg.sources.length})
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
                        {msg.sources.map((src, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => setSelectedSource(src)}
                            className="btn btn-secondary"
                            style={{
                              fontSize: '0.75rem',
                              padding: '0.25rem 0.55rem',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '0.35rem',
                              borderColor: 'rgba(14, 165, 233, 0.3)',
                            }}
                          >
                            <FileText size={12} color="var(--accent-cyan)" />
                            <span>
                              [{src.n || i + 1}] {src.document} {src.page ? `(p. ${src.page})` : ''}
                            </span>
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>
                              {src.score ? `${Math.round(src.score * 100)}%` : ''}
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}

        {/* Loading Spinner Indicator */}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div className="card" style={{ padding: '0.85rem 1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div className="badge-processing animate-pulse-dot" style={{ width: 10, height: 10, borderRadius: '50%' }}></div>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Searching workspace chunks & generating answer...
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Sticky Bottom Input Bar */}
      <div
        className="card"
        style={{
          padding: '0.75rem 1rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem',
          background: 'var(--bg-secondary)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-end' }}>
          <textarea
            ref={textareaRef}
            rows={2}
            value={question}
            onChange={(e) => setQuestion(e.target.value.slice(0, 1000))}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your uploaded documents... (Enter to send, Shift+Enter for newline)"
            className="input-field"
            style={{
              resize: 'none',
              lineHeight: 1.4,
              padding: '0.55rem 0.75rem',
              maxHeight: '120px',
            }}
          />

          <button
            type="button"
            onClick={() => handleSend()}
            disabled={loading || !question.trim()}
            className="btn btn-primary"
            style={{ padding: '0.75rem 1.15rem', height: '100%' }}
          >
            <Send size={16} />
            <span>Ask</span>
          </button>
        </div>

        {/* Bottom Helper Bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.725rem', color: 'var(--text-muted)' }}>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <span>Idempotency-Key Active</span>
            <span>•</span>
            <span>Zero-Leak Tenant Isolation</span>
          </div>
          <div>{question.length} / 1000 characters</div>
        </div>
      </div>

      {/* Slide-out Source Drawer */}
      {selectedSource && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.6)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            justifyContent: 'flex-end',
            zIndex: 60,
          }}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '480px',
              height: '100%',
              background: 'var(--bg-secondary)',
              borderLeft: '1px solid var(--border-color)',
              padding: '1.75rem',
              display: 'flex',
              flexDirection: 'column',
              boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.4)',
            }}
          >
            {/* Drawer Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', paddingBottom: '0.85rem', borderBottom: '1px solid var(--border-color)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 600 }}>Citation Source Details</h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedSource(null)}
                className="btn btn-ghost"
                style={{ padding: '0.25rem' }}
              >
                <X size={18} />
              </button>
            </div>

            {/* Source Metadata */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Document Name</div>
                <div style={{ fontWeight: 600, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                  {selectedSource.document}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <div className="card" style={{ padding: '0.65rem 0.85rem' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Citation Index</div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: 'var(--accent-cyan)' }}>
                    Source [{selectedSource.n || 1}]
                  </div>
                </div>

                <div className="card" style={{ padding: '0.65rem 0.85rem' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Page Number</div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>
                    {selectedSource.page ? `Page ${selectedSource.page}` : 'N/A'}
                  </div>
                </div>
              </div>

              {selectedSource.score && (
                <div className="card" style={{ padding: '0.65rem 0.85rem' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Cosine Similarity Score</div>
                  <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#34d399' }}>
                    {(selectedSource.score * 100).toFixed(1)}% Match
                  </div>
                </div>
              )}
            </div>

            {/* Snippet Content */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                Extracted Text Chunk Snippet
              </div>
              <div
                style={{
                  flex: 1,
                  overflowY: 'auto',
                  padding: '1rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(11, 15, 23, 0.75)',
                  border: '1px solid var(--border-color)',
                  fontSize: '0.85rem',
                  lineHeight: 1.6,
                  color: 'var(--text-secondary)',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {selectedSource.snippet || selectedSource.content || 'Snippet text not loaded.'}
              </div>
            </div>

            {/* Close Button */}
            <button
              type="button"
              onClick={() => setSelectedSource(null)}
              className="btn btn-secondary"
              style={{ width: '100%', marginTop: '1.25rem' }}
            >
              Close Drawer
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function AskPage() {
  return (
    <React.Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading Q&A engine...</div>}>
      <AskContent />
    </React.Suspense>
  );
}
