'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { getWorkspaces, getUsage } from '@/lib/api';

const WorkspaceContext = createContext({
  activeWorkspace: null,
  workspaces: [],
  role: 'member',
  usage: null,
  loading: true,
  refreshUsage: async () => {},
  refreshWorkspaces: async () => {},
});

export function WorkspaceProvider({ workspaceId, children }) {
  const [activeWorkspace, setActiveWorkspace] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [role, setRole] = useState('member');
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const loadWorkspaceData = useCallback(async () => {
    setLoading(true);
    const wsRes = await getWorkspaces();
    if (wsRes.data) {
      setWorkspaces(wsRes.data);
      const current = wsRes.data.find((w) => String(w.id) === String(workspaceId));
      if (current) {
        setActiveWorkspace(current);
        setRole(current.current_user_role || 'member');
      } else {
        // User not a member of this workspace
        router.push('/workspaces');
        return;
      }
    } else {
      router.push('/workspaces');
      return;
    }

    // Load usage
    const usageRes = await getUsage(workspaceId);
    if (usageRes.data) {
      setUsage(usageRes.data);
    }
    setLoading(false);
  }, [workspaceId, router]);

  useEffect(() => {
    if (workspaceId) {
      const timer = setTimeout(loadWorkspaceData, 0);
      return () => clearTimeout(timer);
    }
    return undefined;
  }, [workspaceId, loadWorkspaceData]);

  const refreshUsage = async () => {
    if (!workspaceId) return;
    const usageRes = await getUsage(workspaceId);
    if (usageRes.data) {
      setUsage(usageRes.data);
    }
  };

  const refreshWorkspaces = async () => {
    const wsRes = await getWorkspaces();
    if (wsRes.data) {
      setWorkspaces(wsRes.data);
      const current = wsRes.data.find((w) => String(w.id) === String(workspaceId));
      if (current) {
        setActiveWorkspace(current);
        setRole(current.current_user_role || 'member');
      }
    }
  };

  return (
    <WorkspaceContext.Provider
      value={{
        activeWorkspace,
        workspaces,
        role,
        usage,
        loading,
        refreshUsage,
        refreshWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}
