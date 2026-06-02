const API_BASE = ''

export interface RegisterPayload {
  username: string
  email: string
  password: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface TokenResponse {
  access: string
  refresh: string
}

export interface RefreshPayload {
  refresh: string
}

export interface User {
  id?: string
  username: string
  email: string
}

export interface SearchPayload {
  [key: string]: string
}

export interface HealthResponse {
  status: 'OK' | 'ERR'
}

export interface TransportResponse {
  status: 'OK' | 'INVALID'
}

async function request<T>(
  endpoint: string,
  options: { method?: string; body?: unknown; headers?: Record<string, string> } = {}
): Promise<T> {
  const { body, headers: customHeaders = {}, method = 'POST' } = options

  const headers: Record<string, string> = { ...customHeaders }

  if (body && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  } else {
    delete headers['Content-Type']
  }

  const token = localStorage.getItem('access_token')
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const resolvedBody =
    body instanceof FormData ? body : body ? JSON.stringify(body) : undefined

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method,
    headers,
    body: resolvedBody,
  })

  if (!res.ok) {
    const errorText = await res.text().catch(() => '')
    let message = `Request failed with status ${res.status}`
    try {
      const json = JSON.parse(errorText)
      message = json.detail || json.message || JSON.stringify(json)
    } catch {
      message = errorText || message
    }
    throw new Error(message)
  }

  const text = await res.text()
  if (!text) return undefined as T
  try {
    return JSON.parse(text) as T
  } catch {
    return text as unknown as T
  }
}

async function getReq<T>(endpoint: string): Promise<T> {
  const token = localStorage.getItem('access_token')

  const headers: Record<string, string> = {}
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${API_BASE}${endpoint}`, { headers })

  if (!res.ok) {
    throw new Error(`Request failed with status ${res.status}`)
  }

  const text = await res.text()
  return text as unknown as T
}

export const api = {
  register: (payload: RegisterPayload) =>
    request<string>('/gateway/user/', { body: payload }),

  login: (payload: LoginPayload) =>
    request<TokenResponse>('/auth/token/', { body: payload }),

  refresh: (payload: RefreshPayload) =>
    request<TokenResponse>('/auth/refresh-token/', { body: payload }),

  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return request<TransportResponse>('/gateway/transport/', {
      body: formData,
    })
  },

  health: (module = '/health.php') =>
    getReq<string>(`/gateway/health/?module=${encodeURIComponent(module)}`),

  searchUsers: (payload: SearchPayload, offset = 0) =>
    request<User[]>(`/gateway/user/find/?offset=${offset}`, { body: payload }),
}
