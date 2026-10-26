'use client';

import React from 'react';
import Link from 'next/link';
import { useParams, usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { WorkspaceProvider, useWorkspace } from '@/context/WorkspaceContext';
import {
  FileText,
  MessageSquare,
  History,
  Activity,
  Users,
  Building2,
  ChevronLeft,
  Shield,
  Zap,
  LogOut,
  Sparkles,
} from 'lucide-react';

function WorkspaceLayoutInner({ children, workspaceId }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { activeWorkspace, role, usage, loading } = useWorkspace();

  const navLinks = [
    {
      name: 'Documents',
      href: `/w/${workspaceId}/documents`,
      icon: FileText,
    },
    {
      name: 'Ask AI (RAG)',
      href: `/w/${workspaceId}/ask`,
      icon: MessageSquare,
      highlight: true,
    },
    {
      name: 'Request History',
      href: `/w/${workspaceId}/history`,
      icon: History,
    },
    {
      name: 'Usage & Quotas',
      href: `/w/${workspaceId}/usage`,
      icon: Activity,
    },
    {
      name: 'Team Members',
      href: `/w/${workspaceId}/members`,
      icon: Users,
    },
  ];

  if (loading && !activeWorkspace) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: 'var(--text-secondary)' }}>
          <div className="badge-processing animate-pulse-dot" style={{ width: 12, height: 12, borderRadius: '50%' }}></div>
          <span>Loading workspace...</span>
        </div>
      </div>
    );
  }

  const questionsToday = usage?.daily_questions_used ?? 0;
  const dailyLimit = usage?.daily_questions_limit ?? 20;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: '260px',
          background: 'var(--bg-secondary)',
          borderRight: '1px solid var(--border-color)',
          display: 'flex',
          flexDirection: 'column',
          flexShrink: 0,
        }}
      >
        {/* Workspace Brand Header */}
        <div
          style={{
            padding: '1.25rem',
            borderBottom: '1px solid var(--border-color)',
          }}
        >
          <Link
            href="/workspaces"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
              marginBottom: '0.75rem',
              transition: 'var(--transition)',
            }}
          >
            <ChevronLeft size={14} />
            <span>Switch Workspace</span>
          </Link>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 'var(--radius-sm)',
                background: 'linear-gradient(135deg, var(--primary), var(--accent-cyan))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#ffffff',
                flexShrink: 0,
              }}
            >
              <Building2 size={18} />
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div
                style={{
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  color: 'var(--text-primary)',
                }}
              >
                {activeWorkspace?.name || 'Workspace'}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.15rem' }}>
                <span className="badge badge-ready" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                  {role}
                </span>
                <span className="badge badge-mock" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                  {activeWorkspace?.plan || 'Free'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <nav style={{ flex: 1, padding: '1rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            const Icon = link.icon;
            return (
              <Link
                key={link.name}
                href={link.href}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.65rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.875rem',
                  fontWeight: isActive ? 600 : 500,
                  color: isActive ? '#ffffff' : 'var(--text-secondary)',
                  background: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
                  border: isActive ? '1px solid rgba(59, 130, 246, 0.3)' : '1px solid transparent',
                  transition: 'var(--transition)',
                }}
              >
                <Icon size={18} color={isActive ? 'var(--primary)' : 'var(--text-muted)'} />
                <span>{link.name}</span>
                {link.highlight && !isActive && (
                  <span
                    style={{
                      marginLeft: 'auto',
                      fontSize: '0.65rem',
                      fontWeight: 600,
                      padding: '0.1rem 0.4rem',
                      borderRadius: 'var(--radius-full)',
                      background: 'rgba(14, 165, 233, 0.15)',
                      color: 'var(--accent-cyan)',
                    }}
                  >
                    AI
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer: Quota Summary Card */}
        <div style={{ padding: '0.85rem', borderTop: '1px solid var(--border-color)' }}>
          <div
            style={{
              padding: '0.75rem',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(30, 41, 59, 0.5)',
              border: '1px solid var(--border-color)',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.35rem' }}>
              <span style={{ color: 'var(--text-secondary)' }}>Daily Questions</span>
              <span style={{ fontWeight: 600, color: questionsToday >= dailyLimit ? 'var(--status-failed)' : 'var(--text-primary)' }}>
                {questionsToday} / {dailyLimit}
              </span>
            </div>
            {/* Progress Bar */}
            <div
              style={{
                width: '100%',
                height: 4,
                borderRadius: 'var(--radius-full)',
                background: 'rgba(255, 255, 255, 0.08)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${Math.min(100, (questionsToday / dailyLimit) * 100)}%`,
                  height: '100%',
                  background: questionsToday >= dailyLimit ? 'var(--status-failed)' : 'var(--primary)',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top Header */}
        <header
          style={{
            height: '60px',
            borderBottom: '1px solid var(--border-color)',
            background: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 1.5rem',
            position: 'sticky',
            top: 0,
            zIndex: 30,
          }}
        >
          {/* Left: Tenant Isolation Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
            <div
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.25rem 0.65rem',
                borderRadius: 'var(--radius-full)',
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.25)',
                fontSize: '0.75rem',
                color: '#34d399',
                fontWeight: 500,
              }}
            >
              <Shield size={12} />
              <span>Tenant Isolated ({activeWorkspace?.name})</span>
            </div>
          </div>

          {/* Right: Mock AI Mode Label (Mandatory per Section 9) + User Profile */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* Visible Mock AI Mode Label */}
            <div
              className="badge-mock"
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.35rem',
                padding: '0.3rem 0.75rem',
                borderRadius: 'var(--radius-full)',
                fontSize: '0.75rem',
                fontWeight: 600,
              }}
              title="Runs 100% offline with zero external API costs"
            >
              <Zap size={13} />
              <span>Mode: Mock AI (Zero-Cost RAG)</span>
            </div>

            {/* User & Logout */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {user?.full_name || user?.email}
              </span>
              <button onClick={logout} className="btn btn-ghost" style={{ padding: '0.35rem' }} title="Log out">
                <LogOut size={16} />
              </button>
            </div>
          </div>
        </header>

        {/* Sub-page Render */}
        <div style={{ flex: 1, padding: '1.75rem', overflowY: 'auto' }}>
          {children}
        </div>
      </div>
    </div>
  );
}

function WorkspaceLayoutContent({ children }) {
  const params = useParams();
  const workspaceId = params?.workspaceId;

  if (!workspaceId) {
    return <div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading workspace session...</div>;
  }

  return (
    <WorkspaceProvider workspaceId={workspaceId}>
      <WorkspaceLayoutInner workspaceId={workspaceId}>{children}</WorkspaceLayoutInner>
    </WorkspaceProvider>
  );
}

export default function WorkspaceLayout({ children }) {
  return (
    <React.Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading workspace...</div>}>
      <WorkspaceLayoutContent>{children}</WorkspaceLayoutContent>
    </React.Suspense>
  );
}
