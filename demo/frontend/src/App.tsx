import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuthStore } from '@/stores/authStore'
import { useEffect } from 'react'
import LandingScreen from '@/screens/LandingScreen'
import LoginScreen from '@/screens/LoginScreen'
import RegisterScreen from '@/screens/RegisterScreen'
import DashboardScreen from '@/screens/DashboardScreen'
import AuthGuard from '@/components/AuthGuard'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
})

function AppInit() {
  const checkAuth = useAuthStore((s) => s.checkAuth)

  useEffect(() => {
    checkAuth()
  }, [checkAuth])

  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppInit />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingScreen />} />
          <Route path="/login" element={<LoginScreen />} />
          <Route path="/register" element={<RegisterScreen />} />
          <Route element={<AuthGuard />}>
            <Route path="/dashboard" element={<DashboardScreen />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
