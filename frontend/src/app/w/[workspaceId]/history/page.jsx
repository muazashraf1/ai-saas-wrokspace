'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { getRequestsHistory, getRequestDetail } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import {
  History,
  Clock,
  Sparkles,
  HelpCircle,
  XCircle,
  CheckCircle2,
  Cpu,
  FileText,
  X,
  Search,
  RefreshCw,
} from 'lucide-react';

function HistoryContent() {
  const params = useParams();
  const workspaceId = params?.workspaceId;

  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError('');
    const res = await getRequestsHistory(workspaceId);
    if (res.data) {
      setRequests(res.data);
    } else {
      setError(res.error || 'Failed to load request history.');
    }
    setLoading(false);
  }, [workspaceId]);

  useEffect(() => {
    if (workspaceId) {
      const timer = setTimeout(fetchHistory, 0);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [workspaceId, fetchHistory]);

  const handleOpenDetail = async (reqId) => {
    setDetailLoading(true);
    const res = await getRequestDetail(workspaceId, reqId);
    setDetailLoading(false);
    if (res.data) {
      setSelectedRequest(res.data);
    }
  };

  const filtered = requests.filter((r) =>
    r.question?.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <History size={22} color="var(--primary)" />
            <span>Request History & Audit Log</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Permanent record of questions, grounded answers, latency, consumed tokens, and citations.
          </p>
        </div>

        <button onClick={fetchHistory} className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}>
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Search Input */}
      <div style={{ marginBottom: '1.25rem', position: 'relative' }}>
        <input
          type="text"
          placeholder="Search through past questions..."
          value={filterQuery}
          onChange={(e) => setFilterQuery(e.target.value)}
          className="input-field"
          style={{ paddingLeft: '2.25rem' }}
        />
        <Search size={16} style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
      </div>

      {/* List / Table */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading audit records...
        </div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3.5rem 1.5rem', color: 'var(--text-secondary)' }}>
          <History size={36} color="var(--text-muted)" style={{ margin: '0 auto 0.75rem auto' }} />
          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>No request history found</div>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Questions you ask on the Ask page will automatically be logged here with complete citation forensics.
          </div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {filtered.map((req) => {
            const isAnswered = req.status === 'answered';
            const isUnsupported = req.status === 'unsupported';
            const isFailed = req.status === 'failed';

            return (
              <div
                key={req.id}
                onClick={() => handleOpenDetail(req.id)}
                className="card"
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '1rem 1.25rem',
                }}
              >
                {/* Left: Question & Time */}
                <div style={{ minWidth: 0, flex: 1, paddingRight: '1rem' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.925rem', color: 'var(--text-primary)', marginBottom: '0.35rem' }}>
                    &ldquo;{req.question}&rdquo;
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span>{formatDate(req.created_at)}</span>
                    <span>•</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Clock size={12} />
                      {req.latency_ms || 0} ms
                    </span>
                    <span>•</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                      <Cpu size={12} />
                      {(req.prompt_tokens || 0) + (req.completion_tokens || 0)} tokens
                    </span>
                  </div>
                </div>

                {/* Right: Status Badge */}
                <div style={{ flexShrink: 0 }}>
                  {isAnswered && (
                    <span className="badge badge-ready">
                      <CheckCircle2 size={12} />
                      <span>Answered</span>
                    </span>
                  )}
                  {isUnsupported && (
                    <span className="badge badge-unsupported">
                      <HelpCircle size={12} />
                      <span>Unsupported (Zero Cost)</span>
                    </span>
                  )}
                  {isFailed && (
                    <span className="badge badge-failed">
                      <XCircle size={12} />
                      <span>Failed</span>
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Detail Modal */}
      {selectedRequest && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '1.5rem',
            zIndex: 60,
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: '680px',
              width: '100%',
              maxHeight: '85vh',
              overflowY: 'auto',
              background: 'var(--bg-secondary)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              padding: '1.75rem',
            }}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem', paddingBottom: '0.75rem', borderBottom: '1px solid var(--border-color)' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Request Forensic Detail</h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: #{selectedRequest.id} • {formatDate(selectedRequest.created_at)}</div>
              </div>
              <button onClick={() => setSelectedRequest(null)} className="btn btn-ghost" style={{ padding: '0.25rem' }}>
                <X size={18} />
              </button>
            </div>

            {/* Metrics Chips */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '0.65rem', marginBottom: '1.25rem' }}>
              <div className="card" style={{ padding: '0.65rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Status</div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem', textTransform: 'capitalize' }}>{selectedRequest.status}</div>
              </div>
              <div className="card" style={{ padding: '0.65rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>AI Provider</div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{selectedRequest.provider || 'mock'}</div>
              </div>
              <div className="card" style={{ padding: '0.65rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Latency</div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{selectedRequest.latency_ms || 0} ms</div>
              </div>
              <div className="card" style={{ padding: '0.65rem' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Tokens</div>
                <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{(selectedRequest.prompt_tokens || 0) + (selectedRequest.completion_tokens || 0)}</div>
              </div>
            </div>

            {/* Question */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>User Question</div>
              <div style={{ padding: '0.75rem', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-color)', fontSize: '0.9rem' }}>
                {selectedRequest.question}
              </div>
            </div>

            {/* Answer */}
            <div style={{ marginBottom: '1.25rem' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.35rem' }}>AI Generated Answer</div>
              <div style={{ padding: '0.85rem', borderRadius: 'var(--radius-sm)', background: 'rgba(11, 15, 23, 0.7)', border: '1px solid var(--border-color)', fontSize: '0.875rem', lineHeight: 1.6 }}>
                {selectedRequest.answer || 'No answer recorded.'}
              </div>
            </div>

            {/* Sources / Citations */}
            {selectedRequest.sources && selectedRequest.sources.length > 0 && (
              <div style={{ marginBottom: '1.5rem' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                  Cited Sources ({selectedRequest.sources.length})
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {selectedRequest.sources.map((src, i) => (
                    <div
                      key={i}
                      style={{
                        padding: '0.65rem 0.85rem',
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(14, 165, 233, 0.05)',
                        border: '1px solid rgba(14, 165, 233, 0.2)',
                        fontSize: '0.8rem',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 600, color: 'var(--accent-cyan)', marginBottom: '0.2rem' }}>
                        <span>Source [{src.n || i + 1}]: {src.document}</span>
                        <span>{src.score != null ? `${(src.score * 100).toFixed(1)}% match` : ''}</span>
                      </div>
                      {src.page && <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Page {src.page}</div>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button onClick={() => setSelectedRequest(null)} className="btn btn-secondary" style={{ width: '100%' }}>
              Close Detail
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function HistoryPage() {
  return (
    <React.Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading history...</div>}>
      <HistoryContent />
    </React.Suspense>
  );
}
