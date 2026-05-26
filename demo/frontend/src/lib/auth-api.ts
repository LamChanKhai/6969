import { jwtDecode } from 'jwt-decode';

export interface User {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  is_active: boolean;
  created_at: string;
}

export interface JwtPayload {
  sub: string;
  username: string;
  role: string;
  is_superuser: boolean;
  exp: number;
  iat: number;
  type: string;
}

export interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
  setTokens: (access: string, refresh: string) => void;
  clear: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function getTokenFromStorage(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

function getRefreshFromStorage(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('refresh_token');
}

export function getUserFromToken(): User | null {
  const token = getTokenFromStorage();
  if (!token) return null;
  try {
    const decoded = jwtDecode<JwtPayload>(token);
    return {
      id: decoded.sub,
      username: decoded.username,
      email: '',
      role: decoded.role as 'admin' | 'operator' | 'viewer',
      is_active: true,
      created_at: new Date(decoded.iat * 1000).toISOString(),
    };
  } catch {
    return null;
  }
}

export function getAuthHeader(): Record<string, string> {
  const token = getTokenFromStorage();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function api(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    headers: { 'Content-Type': 'application/json', ...getAuthHeader(), ...options.headers },
    ...options,
  });
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      window.location.href = '/login';
    }
  }
  return res;
}

export async function loginApi(username: string, password: string): Promise<{ access_token: string; refresh_token: string }> {
  const res = await api('/api/v1/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  return res.json();
}

export async function registerApi(username: string, email: string, password: string): Promise<User> {
  const res = await api('/api/v1/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, email, password }),
  });
  return res.json();
}

export async function getMeApi(): Promise<User> {
  const res = await api('/api/v1/auth/me');
  return res.json();
}

export async function refreshTokens(): Promise<boolean> {
  const refresh = getRefreshFromStorage();
  if (!refresh) return false;
  try {
    const res = await api('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return true;
  } catch {
    return false;
  }
}
