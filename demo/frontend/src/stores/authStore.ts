import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api, type LoginPayload, type TokenResponse } from '@/services/api'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  username: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  login: (payload: LoginPayload) => Promise<void>
  logout: () => void
  clearError: () => void
  checkAuth: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      username: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (payload: LoginPayload) => {
        set({ isLoading: true, error: null })
        try {
          const tokens: TokenResponse = await api.login(payload)
          localStorage.setItem('access_token', tokens.access)
          set({
            accessToken: tokens.access,
            refreshToken: tokens.refresh,
            username: payload.username,
            isAuthenticated: true,
            isLoading: false,
          })
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : 'Login failed'
          set({ isLoading: false, error: message })
          throw err
        }
      },

      logout: () => {
        localStorage.removeItem('access_token')
        set({
          accessToken: null,
          refreshToken: null,
          username: null,
          isAuthenticated: false,
          error: null,
        })
      },

      clearError: () => set({ error: null }),

      checkAuth: () => {
        const token = localStorage.getItem('access_token')
        if (token) {
          set({ accessToken: token, isAuthenticated: true })
        } else {
          set({ accessToken: null, isAuthenticated: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        refreshToken: state.refreshToken,
        username: state.username,
      }),
    }
  )
)
