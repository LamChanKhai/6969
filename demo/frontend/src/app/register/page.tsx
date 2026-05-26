'use client';

import { useAuthStore } from '@/store/auth-store';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { Shield, Lock, User, Mail, AlertCircle, Eye, EyeOff } from 'lucide-react';

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading, error, setError } = useAuthStore();
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [mismatch, setMismatch] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMismatch(false);

    if (password !== confirmPassword) {
      setMismatch(true);
      return;
    }

    try {
      await register(username, email, password);
      router.push('/login');
    } catch {
      // error set in store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 noise-overlay">
      <div className="relative z-10 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-lg bg-copper/10 border border-copper/20 mb-4 glow-copper">
            <Shield className="w-7 h-7 text-copper" />
          </div>
          <h1 className="font-display text-2xl font-semibold text-foreground tracking-wide">CSCV2025</h1>
          <p className="text-sm text-muted-foreground mt-1">Create Account</p>
        </div>

        <form onSubmit={handleSubmit} className="panel p-6 space-y-5">
          {error && (
            <div className="flex items-center gap-2 text-alert text-xs bg-alert/10 border border-alert/20 rounded-md px-3 py-2">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {mismatch && (
            <div className="flex items-center gap-2 text-alert text-xs bg-alert/10 border border-alert/20 rounded-md px-3 py-2">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
              <span>Passwords do not match</span>
            </div>
          )}

          <div>
            <label className="label-text">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field pl-10"
                placeholder="Choose username"
                minLength={3}
                required
              />
            </div>
          </div>

          <div>
            <label className="label-text">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-field pl-10"
                placeholder="you@example.com"
                required
              />
            </div>
          </div>

          <div>
            <label className="label-text">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => { setPassword(e.target.value); setMismatch(false); }}
                className="input-field pl-10 pr-10"
                placeholder="Min 8 chars, upper + lower + digit"
                minLength={8}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div>
            <label className="label-text">Confirm Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type={showPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => { setConfirmPassword(e.target.value); setMismatch(false); }}
                className={`input-field pl-10 ${mismatch ? 'border-alert' : ''}`}
                placeholder="Re-enter password"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading || !username || !email || !password}
            className="btn-primary w-full disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                Creating Account...
              </span>
            ) : 'Create Account'}
          </button>

          <p className="text-center text-xs text-muted-foreground">
            Already have an account?{' '}
            <a href="/login" className="text-copper hover:underline">Sign In</a>
          </p>
        </form>
      </div>
    </div>
  );
}
