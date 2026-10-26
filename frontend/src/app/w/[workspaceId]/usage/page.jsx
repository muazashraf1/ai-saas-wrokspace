'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { getUsage } from '@/lib/api';
import { formatTokens, getResetTimeRemaining } from '@/lib/utils';
import {
  Activity,
  Zap,
  TrendingUp,
  Clock,
  Shield,
  Layers,
  Sparkles,
  CheckCircle2,
  DollarSign,
  RefreshCw,
} from 'lucide-react';

function UsageContent() {
  const params = useParams();
  const workspaceId = params?.workspaceId;

  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  const fetchUsageData = useCallback(async () => {
    setLoading(true);
    setError('');
    const res = await getUsage(workspaceId);
    if (res.data) {
      setUsage(res.data);
    } else {
      setError(res.error || 'Failed to load usage metrics.');
    }
    setLoading(false);
  }, [workspaceId]);

  useEffect(() => {
    if (workspaceId) {
      const timer = setTimeout(fetchUsageData, 0);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [workspaceId, fetchUsageData]);

  const questionsToday = usage?.daily_questions_used ?? 0;
  const dailyLimit = usage?.daily_questions_limit ?? 20;
  const questionPct = Math.min(100, Math.round((questionsToday / dailyLimit) * 100));

  const tokensMonth = usage?.monthly_tokens_used ?? 0;
  const tokenLimit = usage?.monthly_tokens_limit ?? 100000;
  const tokenPct = Math.min(100, Math.round((tokensMonth / tokenLimit) * 100));

  const estimatedCost = usage?.estimated_cost_usd ?? '0.000000';

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Activity size={22} color="var(--primary)" />
            <span>Usage Quotas & Cost Accounting</span>
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
            Transparent real-time tracking of daily queries, token consumption, and UTC quota reset windows.
          </p>
        </div>

        <button onClick={fetchUsageData} className="btn btn-ghost" style={{ fontSize: '0.8rem', padding: '0.4rem 0.75rem' }}>
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading quota metrics...
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Top 3 Cards Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem' }}>
            {/* Daily Questions Meter */}
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-sm)', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Zap size={18} />
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Daily Questions</span>
                  </div>
                  <span className="badge badge-ready">{questionPct}% Used</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.02em' }}>{questionsToday}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>/ {dailyLimit} questions</span>
                </div>

                {/* Progress Bar */}
                <div style={{ width: '100%', height: 8, borderRadius: 'var(--radius-full)', background: 'rgba(255, 255, 255, 0.08)', overflow: 'hidden', marginBottom: '0.85rem' }}>
                  <div
                    style={{
                      width: `${questionPct}%`,
                      height: '100%',
                      background: questionPct >= 100 ? 'var(--status-failed)' : 'linear-gradient(90deg, var(--primary), var(--accent-cyan))',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                <Clock size={13} />
                <span>Resets in: {getResetTimeRemaining(usage?.resets_at)} (00:00 UTC)</span>
              </div>
            </div>

            {/* Monthly Token Meter */}
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-sm)', background: 'rgba(14, 165, 233, 0.1)', color: 'var(--accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <TrendingUp size={18} />
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Monthly Token Budget</span>
                  </div>
                  <span className="badge badge-mock">{tokenPct}% Used</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.02em' }}>{formatTokens(tokensMonth)}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '1rem' }}>/ {formatTokens(tokenLimit)} tokens</span>
                </div>

                {/* Progress Bar */}
                <div style={{ width: '100%', height: 8, borderRadius: 'var(--radius-full)', background: 'rgba(255, 255, 255, 0.08)', overflow: 'hidden', marginBottom: '0.85rem' }}>
                  <div
                    style={{
                      width: `${tokenPct}%`,
                      height: '100%',
                      background: 'linear-gradient(90deg, var(--accent-cyan), #34d399)',
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>

              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Includes prompt context tokens + generated answer tokens
              </div>
            </div>

            {/* Accumulated Cost Card */}
            <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: 34, height: 34, borderRadius: 'var(--radius-sm)', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--status-ready)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <DollarSign size={18} />
                    </div>
                    <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Estimated Cost</span>
                  </div>
                  <span className="badge badge-ready">Real-time</span>
                </div>

                <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem', marginBottom: '0.75rem' }}>
                  <span style={{ fontSize: '2rem', fontWeight: 700, letterSpacing: '-0.02em', color: '#34d399' }}>
                    ${parseFloat(estimatedCost).toFixed(4)}
                  </span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>USD</span>
                </div>

                <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: 1.4 }}>
                  Calculated from verified vendor pricing tables saved in usage_records table.
                </p>
              </div>

              <div style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 500 }}>
                ⚡ Mock Provider active: $0.00 actual billing
              </div>
            </div>
          </div>

          {/* Plan Limits Card */}
          <div className="card" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '1.5rem' }}>
              <div>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Shield size={18} color="var(--primary)" />
                  <span>Current Subscription Tier: {usage?.plan?.toUpperCase() || 'FREE'}</span>
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                  Default plan limits assigned to your workspace account
                </p>
              </div>

              <button onClick={() => setShowUpgradeModal(true)} className="btn btn-primary">
                <Sparkles size={16} />
                <span>Upgrade to Pro Plan</span>
              </button>
            </div>

            {/* Features Table */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
              <div style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Daily Query Allowance</div>
                <div style={{ fontWeight: 600, fontSize: '1.05rem', marginTop: '0.25rem' }}>{dailyLimit.toLocaleString()} Questions / day</div>
              </div>

              <div style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Monthly Token Limit</div>
                <div style={{ fontWeight: 600, fontSize: '1.05rem', marginTop: '0.25rem' }}>{tokenLimit.toLocaleString()} Tokens</div>
              </div>

              <div style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Maximum File Size</div>
                <div style={{ fontWeight: 600, fontSize: '1.05rem', marginTop: '0.25rem' }}>{usage?.max_file_mb_limit ?? 10} MB per file</div>
              </div>

              <div style={{ padding: '1rem', borderRadius: 'var(--radius-sm)', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', textTransform: 'uppercase' }}>Vector Index Search</div>
                <div style={{ fontWeight: 600, fontSize: '1.05rem', marginTop: '0.25rem' }}>HNSW Cosine Operator</div>
              </div>
            </div>
          </div>

          {usage?.member_usage?.length > 0 && (
            <div className="card" style={{ padding: '1.75rem' }}>
              <h3 style={{ fontSize: '1.05rem', fontWeight: 600, marginBottom: '1rem' }}>Workspace Member Usage</h3>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ color: 'var(--text-muted)', textAlign: 'left' }}>
                      <th style={{ padding: '0.65rem' }}>Member</th>
                      <th style={{ padding: '0.65rem' }}>Role</th>
                      <th style={{ padding: '0.65rem' }}>Questions today</th>
                      <th style={{ padding: '0.65rem' }}>Tokens this month</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usage.member_usage.map((member) => (
                      <tr key={member.user_id} style={{ borderTop: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.65rem' }}>{member.full_name || member.email}</td>
                        <td style={{ padding: '0.65rem', textTransform: 'capitalize' }}>{member.role}</td>
                        <td style={{ padding: '0.65rem' }}>{member.daily_questions_used}</td>
                        <td style={{ padding: '0.65rem' }}>{formatTokens(member.monthly_tokens_used)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Upgrade Modal */}
      {showUpgradeModal && (
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
          <div className="card" style={{ maxWidth: '440px', width: '100%', padding: '2rem', textAlign: 'center' }}>
            <div style={{ width: 48, height: 48, borderRadius: '50%', background: 'rgba(59, 130, 246, 0.1)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem auto' }}>
              <Sparkles size={24} />
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>Pro Plan Subscription</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', lineHeight: 1.5, marginBottom: '1.5rem' }}>
              As per the Project Plan specifications (Section 2.3), real payment gateways are marked as <strong>Proposed</strong>. In production, this integrates with Stripe billing to increase quotas to 200 questions/day and 2,000,000 tokens/month.
            </p>
            <button onClick={() => setShowUpgradeModal(false)} className="btn btn-primary" style={{ width: '100%' }}>
              Understood
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function UsagePage() {
  return (
    <React.Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading usage dashboard...</div>}>
      <UsageContent />
    </React.Suspense>
  );
}
