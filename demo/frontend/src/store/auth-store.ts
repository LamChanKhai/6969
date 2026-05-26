import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, User, loginApi, registerApi, getMeApi } from '@/lib/auth-api';

interface StoreState extends AuthState {
  error: string | null;
  setError: (error: string | null) => void;
}

export const useAuthStore = create<StoreState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      setError: (error) => set({ error }),

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          const data = await loginApi(username, password);
          localStorage.setItem('access_token', data.access_token);
          localStorage.setItem('refresh_token', data.refresh_token);
          const user = await getMeApi();
          set({
            accessToken: data.access_token,
            refreshToken: data.refresh_token,
            user,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (err: any) {
          const message = err.detail || err.message || 'Login failed';
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      register: async (username: string, email: string, password: string) => {
        set({ isLoading: true, error: null });
        try {
          await registerApi(username, email, password);
          set({ isLoading: false });
        } catch (err: any) {
          const message = err.detail || err.message || 'Registration failed';
          set({ isLoading: false, error: message });
          throw err;
        }
      },

      logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
        });
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      },

      setUser: (user: User) => set({ user, isAuthenticated: true }),

      setTokens: (access: string, refresh: string) => {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        set({ accessToken: access, refreshToken: refresh });
      },

      clear: () => {
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          isAuthenticated: false,
          error: null,
        });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
