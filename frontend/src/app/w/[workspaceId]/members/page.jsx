'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import { useWorkspace } from '@/context/WorkspaceContext';
import { useAuth } from '@/context/AuthContext';
import {
  getWorkspaceMembers,
  addWorkspaceMember,
  removeWorkspaceMember,
} from '@/lib/api';
import { formatDate } from '@/lib/utils';
import {
  Users,
  UserPlus,
  Shield,
  Trash2,
  AlertCircle,
  CheckCircle2,
  Mail,
  User,
  Crown,
} from 'lucide-react';

function MembersContent() {
  const params = useParams();
  const workspaceId = params?.workspaceId;
  const { role: currentUserRole } = useWorkspace();
  const { user: currentUser } = useAuth();

  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('member');
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [removingId, setRemovingId] = useState(null);

  const isAdminOrOwner = currentUserRole === 'owner' || currentUserRole === 'admin';

  const fetchMembers = useCallback(async () => {
    setLoading(true);
    setError('');
    const res = await getWorkspaceMembers(workspaceId);
    if (res.data) {
      setMembers(res.data);
    } else {
      setError(res.error || 'Failed to load team members.');
    }
    setLoading(false);
  }, [workspaceId]);

  useEffect(() => {
    if (workspaceId) {
      const timer = setTimeout(fetchMembers, 0);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [workspaceId, fetchMembers]);

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;

    setError('');
    setSuccess('');
    setInviting(true);

    const res = await addWorkspaceMember(workspaceId, inviteEmail.trim(), inviteRole);
    setInviting(false);

    if (res.error) {
      setError(res.error);
    } else {
      setSuccess(`User "${inviteEmail}" has been added to the workspace as ${inviteRole}.`);
      setInviteEmail('');
      fetchMembers();
    }
  };

  const handleRemove = async (memberId, memberEmail, memberRole) => {
    if (memberRole === 'owner') {
      alert('The workspace owner cannot be removed.');
      return;
    }

    if (!confirm(`Are you sure you want to remove "${memberEmail}" from this workspace?`)) {
      return;
    }

    setRemovingId(memberId);
    setError('');
    const res = await removeWorkspaceMember(workspaceId, memberId);
    setRemovingId(null);

    if (res.error) {
      setError(res.error);
    } else {
      setSuccess(`Member removed from workspace.`);
      fetchMembers();
    }
  };

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Users size={22} color="var(--primary)" />
          <span>Team Members & RBAC</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: '0.2rem' }}>
          Manage workspace membership, invite teammates, and control access permissions.
        </p>
      </div>

      {/* Alert Banners */}
      {error && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--status-failed-bg)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#fca5a5',
            fontSize: '0.85rem',
            marginBottom: '1.25rem',
          }}
        >
          <AlertCircle size={16} style={{ flexShrink: 0 }} />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.85rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--status-ready-bg)',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            color: '#6ee7b7',
            fontSize: '0.85rem',
            marginBottom: '1.25rem',
          }}
        >
          <CheckCircle2 size={16} style={{ flexShrink: 0 }} />
          <span>{success}</span>
        </div>
      )}

      {/* Invite Member Section (Owner & Admin only) */}
      {isAdminOrOwner ? (
        <div className="card" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.35rem' }}>
            <UserPlus size={18} color="var(--primary)" />
            <span>Add Teammate to Workspace</span>
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '1.25rem' }}>
            Enter the registered email of the user to assign them to this isolated workspace.
          </p>

          <form onSubmit={handleInvite} style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', alignItems: 'flex-end' }}>
            <div style={{ flex: 2, minWidth: '220px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                User Email
              </label>
              <input
                type="email"
                required
                placeholder="colleague@company.com"
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                className="input-field"
              />
            </div>

            <div style={{ flex: 1, minWidth: '140px' }}>
              <label style={{ display: 'block', fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '0.35rem' }}>
                Role
              </label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="input-field"
                style={{ cursor: 'pointer' }}
              >
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={inviting || !inviteEmail.trim()}
              className="btn btn-primary"
              style={{ padding: '0.625rem 1.25rem' }}
            >
              <UserPlus size={15} />
              <span>{inviting ? 'Adding...' : 'Add Member'}</span>
            </button>
          </form>
        </div>
      ) : (
        <div
          style={{
            padding: '0.85rem 1.25rem',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(255, 255, 255, 0.03)',
            border: '1px solid var(--border-color)',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            marginBottom: '1.75rem',
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
        >
          <Shield size={16} color="var(--text-muted)" />
          <span>You have <strong>Member</strong> privileges. Only workspace Owners and Admins can invite new members.</span>
        </div>
      )}

      {/* Members Table */}
      <div>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 600, marginBottom: '1rem' }}>
          Current Members ({members.length})
        </h2>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            Loading members...
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
            {members.map((m) => {
              const isOwner = m.role === 'owner';
              const isAdmin = m.role === 'admin';
              const memberEmail = m.user?.email || '';
              const memberName = m.user?.full_name || '';
              const isSelf = currentUser?.email === memberEmail;

              return (
                <div
                  key={m.id}
                  className="card"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.85rem 1.25rem',
                  }}
                >
                  {/* Left: Avatar & Email */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
                    <div
                      style={{
                        width: 38,
                        height: 38,
                        borderRadius: '50%',
                        background: isOwner ? 'rgba(245, 158, 11, 0.15)' : 'rgba(59, 130, 246, 0.1)',
                        color: isOwner ? '#fbbf24' : 'var(--primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                      }}
                    >
                      {isOwner ? <Crown size={18} /> : <User size={18} />}
                    </div>

                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>{memberName || memberEmail}</span>
                        {isSelf && (
                          <span style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)' }}>(You)</span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: '0.5rem', marginTop: '0.15rem' }}>
                        <span>{memberEmail}</span>
                        <span>•</span>
                        <span>Joined {formatDate(m.created_at)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Right: Role Badge & Action */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span
                      className={`badge ${isOwner ? 'badge-processing' : isAdmin ? 'badge-mock' : 'badge-ready'}`}
                      style={{ textTransform: 'capitalize' }}
                    >
                      {m.role}
                    </span>

                    {isAdminOrOwner && !isOwner && !isSelf && (
                      <button
                        onClick={() => handleRemove(m.id, memberEmail, m.role)}
                        disabled={removingId === m.id}
                        className="btn btn-danger"
                        style={{ padding: '0.35rem 0.55rem' }}
                        title="Remove Member"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

export default function MembersPage() {
  return (
    <React.Suspense fallback={<div style={{ padding: '2rem', color: 'var(--text-secondary)' }}>Loading team members...</div>}>
      <MembersContent />
    </React.Suspense>
  );
}
