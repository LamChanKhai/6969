'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/store/auth-store';
import {
  Shield,
  Activity,
  Upload,
  GitBranch,
  Users,
  FileText,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Lock,
  ScanLine,
  Key,
  Gauge,
} from 'lucide-react';

const navItems = [
  { name: 'Dashboard', href: '/dashboard', icon: Activity },
  { name: 'Uploads', href: '/dashboard/uploads', icon: Upload },
  { name: 'Pipeline', href: '/dashboard/pipeline', icon: GitBranch },
  { name: 'Monitoring', href: '/dashboard/monitoring', icon: Shield },
  { name: 'Scan Results', href: '/dashboard/scans', icon: ScanLine },
  { name: 'API Keys', href: '/dashboard/api-keys', icon: Key },
];

const adminItems = [
  { name: 'Users', href: '/dashboard/users', icon: Users },
  { name: 'Audit Log', href: '/dashboard/audit', icon: FileText },
  { name: 'Rate Limits', href: '/dashboard/rate-limits', icon: Gauge },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, router]);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const allNav = [...navItems, ...(user?.role === 'admin' ? adminItems : [])];

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50 w-64 bg-midnight-light border-r border-border
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-5 py-5 border-b border-border">
            <div className="w-8 h-8 rounded-md bg-copper/20 flex items-center justify-center">
              <Shield className="w-4 h-4 text-copper" />
            </div>
            <div>
              <h1 className="font-display text-sm font-semibold text-foreground tracking-wide">CSCV2025</h1>
              <p className="text-[10px] text-muted-foreground uppercase tracking-widest">Secure Platform</p>
            </div>
            <button
              className="ml-auto lg:hidden text-muted-foreground"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Nav */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {allNav.map((item) => {
              const isActive = pathname === item.href || pathname?.startsWith(item.href + '/');
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-all duration-200 group
                    ${isActive
                      ? 'bg-copper/10 text-copper font-medium'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
                    }
                  `}
                >
                  <item.icon className={`w-4 h-4 ${isActive ? 'text-copper' : 'text-muted-foreground group-hover:text-foreground'}`} />
                  <span>{item.name}</span>
                  {isActive && <ChevronRight className="w-3 h-3 ml-auto opacity-50" />}
                </Link>
              );
            })}
          </nav>

          {/* User section */}
          <div className="border-t border-border p-4 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-full bg-steel flex items-center justify-center text-xs font-display font-semibold text-copper">
                {user?.username?.charAt(0)?.toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground truncate">{user?.username}</p>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
                  {user?.role}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 w-full px-3 py-2 text-xs text-muted-foreground hover:text-alert transition-colors rounded-md hover:bg-muted/50"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-14 border-b border-border bg-midnight-light/80 backdrop-blur-sm flex items-center px-4 lg:px-6 gap-4">
          <button
            className="lg:hidden text-muted-foreground"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Lock className="w-3 h-3" />
            <span className="uppercase tracking-wider">Secure Session</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <span className="text-xs text-muted-foreground font-mono">
              {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
            </span>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6 noise-overlay">
          <div className="relative z-10 max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
