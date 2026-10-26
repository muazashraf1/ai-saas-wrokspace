'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { getWorkspaces, createWorkspace } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import {
  Building2,
  Plus,
  ArrowRight,
  LogOut,
  Shield,
  Layers,
  Sparkles,
  Users,
  AlertCircle,
  X,
} from 'lucide-react';

export default function WorkspacesPage() {
  const { user, loading: authLoading, logout } = useAuth();
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [creating, setCreating] = useState(false);
  const [modalError, setModalError] = useState('');
  const router = useRouter();

  const fetchWorkspaces = useCallback(async () => {
    setLoading(true);
    setError('');
    const res = await getWorkspaces();
    if (res.data) {
      setWorkspaces(res.data);
    } else {
      setError(res.error || 'Failed to load workspaces.');
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login');
      return undefined;
    }

    if (user) {
      const timer = setTimeout(fetchWorkspaces, 0);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [user, authLoading, router, fetchWorkspaces]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!newWorkspaceName.trim()) return;

    setCreating(true);
    setModalError('');

    const res = await createWorkspace(newWorkspaceName.trim());
    if (res.data) {
      setNewWorkspaceName('');
      setShowCreateModal(false);
      // Navigate to the newly created workspace
      router.push(`/w/${res.data.id}/documents`);
    } else {
      setModalError(res.error || 'Failed to create workspace.');
      setCreating(false);
    }
  };

  if (authLoading || (loading && workspaces.length === 0)) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)' }}>
          <div className="badge-processing animate-pulse-dot" style={{ width: 12, height: 12, borderRadius: '50%' }}></div>
          <span>Loading your workspaces...</span>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Bar */}
      <header
        style={{
          borderBottom: '1px solid var(--border-color)',
          background: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(12px)',
          position: 'sticky',
          top: 0,
          zIndex: 40,
        }}
      >
        <div
          style={{
            maxWidth: '1200px',
            margin: '0 auto',
            padding: '0.875rem 1.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          {/* Logo & Brand */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, var(--primary), var(--accent-cyan))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
              }}
            >
              <Shield size={18} />
            </div>
            <div>
              <div style={{ fontWeight: 600, fontSize: '0.95rem', letterSpacing: '-0.01em' }}>
                AI SaaS Workspace
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Tenant Isolation Active</div>
            </div>
          </div>

          {/* User Profile & Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div style={{ textAlign: 'right', display: 'none', mdDisplay: 'block' }}>
              <div style={{ fontSize: '0.85rem', fontWeight: 500 }}>{user?.full_name || user?.email}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{user?.email}</div>
            </div>
            <button onClick={logout} className="btn btn-ghost" title="Sign out">
              <LogOut size={16} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main style={{ flex: 1, maxWidth: '1200px', margin: '0 auto', padding: '2.5rem 1.5rem', width: '100%' }}>
        {/* Title & Action */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '1rem',
            marginBottom: '2rem',
          }}
        >
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 700, letterSpacing: '-0.02em', marginBottom: '0.35rem' }}>
              Your Workspaces
            </h1>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Select a workspace to manage documents, search chunks, and ask questions
            </p>
          </div>

          <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
            <Plus size={16} />
            <span>Create Workspace</span>
          </button>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.875rem',
              borderRadius: 'var(--radius-sm)',
              background: 'var(--status-failed-bg)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              fontSize: '0.85rem',
              marginBottom: '1.5rem',
            }}
          >
            <AlertCircle size={16} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {/* Workspaces Grid */}
        {workspaces.length === 0 ? (
          <div
            className="card"
            style={{
              textAlign: 'center',
              padding: '4rem 1.5rem',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
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
                marginBottom: '1.25rem',
              }}
            >
              <Building2 size={26} />
            </div>
            <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '0.5rem' }}>
              No Workspaces Found
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', maxWidth: '420px', marginBottom: '1.5rem' }}>
              You do not belong to any workspaces yet. Create your first workspace to start uploading documents and asking questions.
            </p>
            <button onClick={() => setShowCreateModal(true)} className="btn btn-primary">
              <Plus size={16} />
              <span>Create Your First Workspace</span>
            </button>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
              gap: '1.25rem',
            }}
          >
            {workspaces.map((ws) => (
              <div
                key={ws.id}
                onClick={() => router.push(`/w/${ws.id}/documents`)}
                className="card"
                style={{
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  padding: '1.5rem',
                }}
              >
                <div>
                  {/* Card Header with Badges */}
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 'var(--radius-sm)',
                        background: 'rgba(14, 165, 233, 0.1)',
                        color: 'var(--accent-cyan)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <Building2 size={20} />
                    </div>

                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <span className="badge badge-ready" style={{ textTransform: 'uppercase' }}>
                        {ws.current_user_role || 'Member'}
                      </span>
                      <span className="badge badge-mock" style={{ textTransform: 'uppercase' }}>
                        {ws.plan || 'Free'}
                      </span>
                    </div>
                  </div>

                  {/* Workspace Name */}
                  <h2 style={{ fontSize: '1.15rem', fontWeight: 600, letterSpacing: '-0.01em', marginBottom: '0.4rem' }}>
                    {ws.name}
                  </h2>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '1.5rem' }}>
                    <Users size={14} />
                    <span>{ws.member_count || 1} team member{ws.member_count > 1 ? 's' : ''}</span>
                    <span>•</span>
                    <span>Created {formatDate(ws.created_at)}</span>
                  </div>
                </div>

                {/* Enter Action */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    paddingTop: '0.75rem',
                    borderTop: '1px solid var(--border-color)',
                    color: 'var(--primary)',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                  }}
                >
                  <span>Open Workspace</span>
                  <ArrowRight size={16} />
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Modal: Create Workspace */}
      {showCreateModal && (
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
            zIndex: 50,
          }}
        >
          <div
            className="card"
            style={{
              maxWidth: '460px',
              width: '100%',
              padding: '1.75rem',
              background: 'var(--bg-secondary)',
              border: '1px solid rgba(255, 255, 255, 0.12)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Building2 size={20} color="var(--primary)" />
                <h3 style={{ fontSize: '1.15rem', fontWeight: 600 }}>Create New Workspace</h3>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn btn-ghost"
                style={{ padding: '0.25rem' }}
              >
                <X size={18} />
              </button>
            </div>

            {modalError && (
              <div
                style={{
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--status-failed-bg)',
                  border: '1px solid rgba(239, 68, 68, 0.3)',
                  color: '#fca5a5',
                  fontSize: '0.8rem',
                  marginBottom: '1rem',
                }}
              >
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: '1.25rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                  Workspace Name
                </label>
                <input
                  type="text"
                  required
                  autoFocus
                  placeholder="e.g. Acme Engineering or Marketing Docs"
                  value={newWorkspaceName}
                  onChange={(e) => setNewWorkspaceName(e.target.value)}
                  className="input-field"
                />
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                  You will automatically become the Workspace Owner.
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !newWorkspaceName.trim()}
                  className="btn btn-primary"
                >
                  {creating ? 'Creating...' : 'Create & Enter'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
