/**
 * Utility helper functions for AI SaaS Workspace Frontend
 */

/**
 * Generates standard RFC4122 v4 UUID for Idempotency-Key headers
 */
export function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Formats ISO date string into readable user friendly format
 */
export function formatDate(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  }).format(date);
}

/**
 * Formats bytes to KB / MB
 */
export function formatBytes(bytes, decimals = 1) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`;
}

/**
 * Formats token count with commas (e.g. 12,450)
 */
export function formatTokens(num) {
  if (num === null || num === undefined) return '0';
  return new Intl.NumberFormat('en-US').format(num);
}

/**
 * Calculates remaining hours/minutes until UTC midnight reset
 */
export function getResetTimeRemaining(resetsAtIso) {
  const target = resetsAtIso ? new Date(resetsAtIso) : new Date(Date.now() + 86400000);
  const diff = target.getTime() - Date.now();
  if (diff <= 0) return 'resets shortly';
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  return `${hours}h ${mins}m`;
}
