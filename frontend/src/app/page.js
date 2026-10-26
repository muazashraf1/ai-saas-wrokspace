'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { Shield, Sparkles, ArrowRight, Zap, FileText, Lock } from 'lucide-react';

export default function Home() {
  const { user, loading, demoLogin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) {
      router.push('/workspaces');
    }
  }, [user, loading, router]);

  const handleDemoLogin = async () => {
    const res = await demoLogin();
    if (res.success) {
      router.push('/workspaces');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)' }}>
          <div className="badge-processing animate-pulse-dot" style={{ width: 12, height: 12, borderRadius: '50%' }}></div>
          <span>Loading workspace environment...</span>
        </div>
      </div>
    );
  }

  return (
    <main style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem 1rem' }}>
      <div style={{ maxWidth: '640px', width: '100%', textAlign: 'center' }}>
        {/* Top Badge */}
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.35rem 0.85rem', borderRadius: '9999px', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.25)', color: '#60a5fa', fontSize: '0.8rem', fontWeight: 500, marginBottom: '1.5rem' }}>
          <Sparkles size={14} />
          <span>FalconXoft Internship • Weekend 2 Project</span>
        </div>

        {/* Main Heading */}
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, letterSpacing: '-0.03em', lineHeight: 1.2, marginBottom: '1rem' }}>
          AI SaaS Workspace
        </h1>

        <p style={{ color: 'var(--text-secondary)', fontSize: '1.05rem', lineHeight: 1.6, marginBottom: '2rem' }}>
          Secure, multi-tenant document intelligence platform powered by RAG, pgvector semantic search, verifiable citations, and transparent usage limits.
        </p>

        {/* Action Buttons */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', justifyContent: 'center', marginBottom: '2.5rem' }}>
          <button onClick={handleDemoLogin} className="btn btn-primary" style={{ padding: '0.75rem 1.5rem', fontSize: '0.95rem' }}>
            <Zap size={16} />
            <span>1-Click Demo Login (Acme HR)</span>
          </button>
          <Link href="/login" className="btn btn-secondary" style={{ padding: '0.75rem 1.25rem', fontSize: '0.95rem' }}>
            Sign In
          </Link>
          <Link href="/register" className="btn btn-ghost" style={{ padding: '0.75rem 1.25rem', fontSize: '0.95rem' }}>
            Register
            <ArrowRight size={15} />
          </Link>
        </div>

        {/* Three Value Pillars */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1rem', textAlign: 'left' }}>
          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ color: 'var(--accent-cyan)', marginBottom: '0.5rem' }}>
              <Lock size={18} />
            </div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>Tenant Isolation</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: 1.4 }}>
              Strict database and pgvector separation per workspace.
            </div>
          </div>

          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ color: 'var(--primary)', marginBottom: '0.5rem' }}>
              <FileText size={18} />
            </div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>Verifiable Citations</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: 1.4 }}>
              Every answer links to exact document chunks and page numbers.
            </div>
          </div>

          <div className="card" style={{ padding: '1rem' }}>
            <div style={{ color: 'var(--status-ready)', marginBottom: '0.5rem' }}>
              <Shield size={18} />
            </div>
            <div style={{ fontWeight: 600, fontSize: '0.9rem', marginBottom: '0.25rem' }}>Zero-Leak Guard</div>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', lineHeight: 1.4 }}>
              Prompt injection defense and automatic 429 quota protection.
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
