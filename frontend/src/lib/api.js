/**
 * Centralized API Client for Django REST Backend
 * Handles Bearer token injection, automatic 401 refresh rotation, and Idempotency-Key headers
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Token Storage Keys
const ACCESS_TOKEN_KEY = 'ai_saas_access_token';
const REFRESH_TOKEN_KEY = 'ai_saas_refresh_token';

export function getTokens() {
  if (typeof window === 'undefined') return { access: null, refresh: null };
  return {
    access: localStorage.getItem(ACCESS_TOKEN_KEY),
    refresh: localStorage.getItem(REFRESH_TOKEN_KEY),
  };
}

export function saveTokens(access, refresh) {
  if (typeof window === 'undefined') return;
  if (access) localStorage.setItem(ACCESS_TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function removeTokens() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Base fetch wrapper with auth injection & 401 retry
 */
export async function apiClient(endpoint, options = {}) {
  const { access, refresh } = getTokens();
  const url = `${API_BASE_URL}${endpoint}`;

  const headers = { ...options.headers };

  // Set Authorization header if access token exists and not explicitly skipped
  if (access && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${access}`;
  }

  // Set JSON content type unless body is FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  let response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (err) {
    return {
      error: 'Cannot connect to backend server. Make sure Django is running at port 8000.',
      status: 0,
      data: null,
    };
  }

  // Handle Token Expiry (401) with automatic refresh
  if (response.status === 401 && refresh && !endpoint.includes('/auth/')) {
    try {
      const refreshRes = await fetch(`${API_BASE_URL}/auth/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });

      if (refreshRes.ok) {
        const refreshData = await refreshRes.json();
        saveTokens(refreshData.access, refreshData.refresh || refresh);

        // Retry the original request with new access token
        headers['Authorization'] = `Bearer ${refreshData.access}`;
        response = await fetch(url, { ...options, headers });
      } else {
        removeTokens();
        if (typeof window !== 'undefined') {
          window.dispatchEvent(new Event('auth-expired'));
        }
      }
    } catch {
      removeTokens();
    }
  }

  // Parse JSON response safely
  let data = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    let errorMsg = 'An unexpected error occurred.';
    if (data) {
      if (typeof data.detail === 'string') errorMsg = data.detail;
      else if (typeof data.error === 'string') errorMsg = data.error;
      else if (typeof data === 'object') {
        const firstKey = Object.keys(data)[0];
        const val = data[firstKey];
        errorMsg = Array.isArray(val) ? `${firstKey}: ${val[0]}` : String(val);
      }
    }
    return { error: errorMsg, status: response.status, data };
  }

  return { error: null, status: response.status, data };
}

/* ==========================================================================
   Auth Endpoints
   ========================================================================== */

export async function loginUser(email, password) {
  return apiClient('/auth/login/', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function registerUser(email, password, full_name, password_confirm) {
  return apiClient('/auth/register/', {
    method: 'POST',
    body: JSON.stringify({
      email,
      password,
      full_name,
      password_confirm: password_confirm || password,
    }),
  });
}

export async function getMe() {
  return apiClient('/auth/me/');
}

/* ==========================================================================
   Workspaces Endpoints
   ========================================================================== */

export async function getWorkspaces() {
  return apiClient('/workspaces/');
}

export async function createWorkspace(name) {
  return apiClient('/workspaces/', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export async function getWorkspaceMembers(workspaceId) {
  return apiClient(`/workspaces/${workspaceId}/members/`);
}

export async function addWorkspaceMember(workspaceId, email, role = 'member') {
  return apiClient(`/workspaces/${workspaceId}/members/`, {
    method: 'POST',
    body: JSON.stringify({ email, role }),
  });
}

export async function removeWorkspaceMember(workspaceId, memberId) {
  return apiClient(`/workspaces/${workspaceId}/members/${memberId}/`, {
    method: 'DELETE',
  });
}

/* ==========================================================================
   Documents Endpoints
   ========================================================================== */

export async function getDocuments(workspaceId) {
  return apiClient(`/workspaces/${workspaceId}/documents/`);
}

export async function uploadDocument(workspaceId, file) {
  const formData = new FormData();
  formData.append('file', file);

  return apiClient(`/workspaces/${workspaceId}/documents/`, {
    method: 'POST',
    body: formData,
  });
}

export async function retryDocument(workspaceId, documentId) {
  return apiClient(`/workspaces/${workspaceId}/documents/${documentId}/retry/`, {
    method: 'POST',
  });
}

export async function deleteDocument(workspaceId, documentId) {
  return apiClient(`/workspaces/${workspaceId}/documents/${documentId}/`, {
    method: 'DELETE',
  });
}

/* ==========================================================================
   Q&A Ask Endpoints (With Idempotency Key)
   ========================================================================== */

export async function askQuestion(workspaceId, question, idempotencyKey) {
  return apiClient(`/workspaces/${workspaceId}/ask/`, {
    method: 'POST',
    headers: {
      'Idempotency-Key': idempotencyKey,
    },
    body: JSON.stringify({ question }),
  });
}

export async function getRequestsHistory(workspaceId) {
  return apiClient(`/workspaces/${workspaceId}/requests/`);
}

export async function getRequestDetail(workspaceId, requestId) {
  return apiClient(`/workspaces/${workspaceId}/requests/${requestId}/`);
}

/* ==========================================================================
   Usage Quota Endpoints
   ========================================================================== */

export async function getUsage(workspaceId) {
  return apiClient(`/workspaces/${workspaceId}/usage/`);
}
