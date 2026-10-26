'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getTokens, saveTokens, removeTokens, loginUser, registerUser, getMe } from '@/lib/api';

const AuthContext = createContext({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  demoLogin: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Load user profile on mount if token is saved
  useEffect(() => {
    async function loadUser() {
      const { access } = getTokens();
      if (!access) {
        setLoading(false);
        return;
      }

      const { data, error } = await getMe();
      if (data && !error) {
        setUser(data);
      } else {
        removeTokens();
        setUser(null);
      }
      setLoading(false);
    }

    loadUser();
  }, []);

  useEffect(() => {
    const handleAuthExpired = () => {
      removeTokens();
      setUser(null);
      router.push('/login');
    };
    window.addEventListener('auth-expired', handleAuthExpired);
    return () => window.removeEventListener('auth-expired', handleAuthExpired);
  }, [router]);

  const login = async (email, password) => {
    const { data, error } = await loginUser(email, password);
    if (error) {
      return { success: false, error };
    }

    saveTokens(data.access, data.refresh);
    
    // Fetch profile
    const profile = await getMe();
    if (profile.data) {
      setUser(profile.data);
    }
    return { success: true };
  };

  const register = async (email, password, full_name, password_confirm) => {
    const { data, error } = await registerUser(email, password, full_name, password_confirm || password);
    if (error) {
      return { success: false, error };
    }

    if (data?.tokens?.access) {
      saveTokens(data.tokens.access, data.tokens.refresh);
      setUser(data.user);
      return { success: true };
    }

    return await login(email, password);
  };

  const demoLogin = async () => {
    return login('demo@example.com', 'Password123!');
  };

  const logout = () => {
    removeTokens();
    setUser(null);
    router.push('/login');
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, demoLogin, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
