import { getAuthHeader } from '@/lib/auth-api';
import {
  FileUpload,
  PaginatedResponse,
  ExtractionStatus,
  AuditLog,
  SystemHealth,
  SystemMetrics,
  SecurityDashboard,
  PipelineOverview,
  FileScanResult,
  ApiKey,
  ApiKeyWithSecret,
  RateLimitEvent,
} from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch(path: string, options: RequestInit = {}): Promise<any> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { ...getAuthHeader(), ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

// Uploads
export async function listUploads(skip = 0, limit = 50): Promise<PaginatedResponse<FileUpload>> {
  return apiFetch(`/api/v1/uploads/?skip=${skip}&limit=${limit}`);
}

export async function getUpload(id: string): Promise<FileUpload> {
  return apiFetch(`/api/v1/uploads/${id}`);
}

export async function getExtractionStatus(id: string): Promise<ExtractionStatus> {
  return apiFetch(`/api/v1/uploads/${id}/extraction-status`);
}

export async function uploadFile(file: File): Promise<FileUpload> {
  const headers = { ...getAuthHeader() };
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/v1/uploads/`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

// Audit
export async function listAuditLogs(skip = 0, limit = 50, action?: string, resourceType?: string): Promise<PaginatedResponse<AuditLog>> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (action) params.set('action', action);
  if (resourceType) params.set('resource_type', resourceType);
  return apiFetch(`/api/v1/audit/?${params}`);
}

// Monitoring
export async function getSystemHealth(): Promise<SystemHealth> {
  return apiFetch('/api/v1/monitoring/health');
}

export async function getMetrics(): Promise<SystemMetrics> {
  return apiFetch('/api/v1/monitoring/metrics');
}

export async function getSecurityDashboard(): Promise<SecurityDashboard> {
  return apiFetch('/api/v1/monitoring/security-dashboard');
}

// Pipeline
export async function getPipelineOverview(): Promise<PipelineOverview> {
  return apiFetch('/api/v1/pipeline/overview');
}

// Users
export async function listUsers(skip = 0, limit = 50): Promise<PaginatedResponse<any>> {
  return apiFetch(`/api/v1/users/?skip=${skip}&limit=${limit}`);
}

export async function updateUser(id: string, data: { email?: string; role?: string; is_active?: boolean }): Promise<any> {
  return apiFetch(`/api/v1/users/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify(data),
  });
}

// Scans
export async function listScans(uploadId?: string, scanType?: string, scanStatus?: string, skip = 0, limit = 50): Promise<PaginatedResponse<FileScanResult>> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (uploadId) params.set('upload_id', uploadId);
  if (scanType) params.set('scan_type', scanType);
  if (scanStatus) params.set('scan_status', scanStatus);
  return apiFetch(`/api/v1/scans/?${params}`);
}

export async function createScan(data: { upload_id: string; scanner_name: string; scan_type: string; scanner_version?: string; scan_status?: string; threats_found?: number; scan_details?: string; duration_ms?: number }): Promise<FileScanResult> {
  return apiFetch('/api/v1/scans/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify(data),
  });
}

// API Keys
export async function listApiKeys(skip = 0, limit = 50): Promise<PaginatedResponse<ApiKey>> {
  return apiFetch(`/api/v1/api-keys/?skip=${skip}&limit=${limit}`);
}

export async function createApiKey(name: string, expires_at?: string): Promise<ApiKeyWithSecret> {
  return apiFetch('/api/v1/api-keys/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify({ name, expires_at }),
  });
}

export async function revokeApiKey(id: string): Promise<{ detail: string; key_prefix: string }> {
  return apiFetch(`/api/v1/api-keys/${id}`, {
    method: 'DELETE',
  });
}

// Rate Limits
export async function listRateLimits(ipAddress?: string, endpoint?: string, actionTaken?: string, skip = 0, limit = 50): Promise<PaginatedResponse<RateLimitEvent>> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (ipAddress) params.set('ip_address', ipAddress);
  if (endpoint) params.set('endpoint', endpoint);
  if (actionTaken) params.set('action_taken', actionTaken);
  return apiFetch(`/api/v1/rate-limits/?${params}`);
}

// Budget & Notifications
export async function getBudgetUsage(month?: string): Promise<any> {
  const params = month ? `?month=${month}` : '';
  return apiFetch(`/api/v1/budget/usage${params}`);
}

export async function updateBudgetLimits(data: { upload_limit?: number; storage_limit_bytes?: number; api_call_limit?: number }): Promise<any> {
  return apiFetch('/api/v1/budget/usage', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
    body: JSON.stringify(data),
  });
}

export async function listNotifications(isRead?: boolean, skip = 0, limit = 20): Promise<PaginatedResponse<any>> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (isRead !== undefined) params.set('is_read', String(isRead));
  return apiFetch(`/api/v1/budget/notifications/?${params}`);
}

export async function markNotificationRead(id: string): Promise<any> {
  return apiFetch(`/api/v1/budget/notifications/${id}/read`, {
    method: 'POST',
  });
}

export async function markAllNotificationsRead(): Promise<any> {
  return apiFetch('/api/v1/budget/notifications/read-all', {
    method: 'POST',
  });
}

export async function getUnreadNotificationCount(): Promise<{ unread_count: number }> {
  return apiFetch('/api/v1/budget/notifications/unread-count');
}
