'use client';

import { useAuthStore } from '@/store/auth-store';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Shield, Lock, User, AlertCircle } from 'lucide-react';

export const dynamic = 'force-dynamic';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, setError } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(username, password);
      router.push('/dashboard');
    } catch {
      // error already set in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 noise-overlay">
      <div className="relative z-10 w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-lg bg-copper/10 border border-copper/20 mb-4 glow-copper">
            <Shield className="w-7 h-7 text-copper" />
          </div>
          <h1 className="font-display text-2xl font-semibold text-foreground tracking-wide">CSCV2025</h1>
          <p className="text-sm text-muted-foreground mt-1">Secure Platform — Sign In</p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="panel p-6 space-y-5">
          {/* Demo credentials hint */}
          <div className="bg-copper/5 border border-copper/15 rounded-md p-3">
            <p className="text-xs text-copper font-medium mb-1">Demo Credentials</p>
            <p className="text-[11px] text-muted-foreground font-mono">admin / Admin@1234</p>
            <p className="text-[11px] text-muted-foreground font-mono">operator / Oper@tor1</p>
            <p className="text-[11px] text-muted-foreground font-mono">viewer / View@er1</p>
          </div>

          {error && (
            <div className="flex items-center gap-2 text-alert text-xs bg-alert/10 border border-alert/20 rounded-md px-3 py-2">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="label-text">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                value={username}
                onChange={(e) => { setUsername(e.target.value); setError(null); }}
                className="input-field pl-10"
                placeholder="Enter username"
                autoFocus
              />
            </div>
          </div>

          <div>
            <label className="label-text">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(null); }}
                className="input-field pl-10"
                placeholder="Enter password"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !username || !password}
            className="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                Authenticating...
              </span>
            ) : 'Sign In'}
          </button>

          <p className="text-center text-xs text-muted-foreground">
            Don&apos;t have an account?{' '}
            <a href="/register" className="text-copper hover:underline">Register</a>
          </p>
        </form>
      </div>
    </div>
  );
}
