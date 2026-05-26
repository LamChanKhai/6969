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
