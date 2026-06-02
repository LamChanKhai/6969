import { useAuthStore } from '@/stores/authStore'
import { Outlet, Navigate } from 'react-router-dom'

export default function AuthGuard() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
