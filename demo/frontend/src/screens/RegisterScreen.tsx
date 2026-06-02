import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Alert } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import {
  UserPlus,
  Mail,
  Lock,
  User,
  ArrowLeft,
  ShieldCheck,
  Loader2,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'

interface RegisterForm {
  username: string
  email: string
  password: string
  confirmPassword: string
}

export default function RegisterScreen() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<RegisterForm>()

  const onSubmit = async (data: RegisterForm) => {
    setIsSubmitting(true)
    setError('')
    setSuccess('')

    try {
      const username = await fetch('/gateway/user/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: data.username,
          email: data.email,
          password: data.password,
        }),
      }).then((r) => {
        if (!r.ok) {
          return r.json().then((j) => {
            throw new Error(
              j.username?.[0] || j.detail || 'Registration failed'
            )
          })
        }
        return r.text()
      })

      setSuccess(`Account "${username}" created successfully`)

      setTimeout(async () => {
        try {
          await login({ username: data.username, password: data.password })
          navigate('/dashboard')
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : 'Auto-login failed'
          setError(msg)
          setSuccess('')
        }
        setIsSubmitting(false)
      }, 800)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed'
      setError(msg)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-secondary/50 via-background to-background">
      <div className="w-full max-w-md">
        <div className="animate-fade-in-up">
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors mb-6"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Home
          </Link>

          <Card className="border-border/60">
            <CardHeader className="pb-4">
              <div className="flex items-center gap-3 mb-2">
                <div className="h-10 w-10 rounded-lg bg-primary/15 flex items-center justify-center">
                  <UserPlus className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Create Account</CardTitle>
                  <CardDescription>
                    Register to access SuperApp
                  </CardDescription>
                </div>
              </div>
            </CardHeader>

            <CardContent>
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                {error && (
                  <Alert variant="destructive" className="animate-slide-in">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span className="text-sm">{error}</span>
                  </Alert>
                )}

                {success && (
                  <Alert variant="success" className="animate-slide-in">
                    <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                    <span className="text-sm">{success}</span>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="username">
                    <span className="flex items-center gap-1.5">
                      <User className="h-3.5 w-3.5" />
                      Username
                    </span>
                  </Label>
                  <Input
                    id="username"
                    placeholder="enter your username"
                    {...register('username', {
                      required: 'Username is required',
                      minLength: { value: 3, message: 'Minimum 3 characters' },
                    })}
                    autoComplete="username"
                  />
                  {errors.username && (
                    <p className="text-xs text-destructive">{errors.username.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">
                    <span className="flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5" />
                      Email
                    </span>
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    {...register('email', {
                      required: 'Email is required',
                      pattern: {
                        value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                        message: 'Enter a valid email',
                      },
                    })}
                    autoComplete="email"
                  />
                  {errors.email && (
                    <p className="text-xs text-destructive">{errors.email.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">
                    <span className="flex items-center gap-1.5">
                      <Lock className="h-3.5 w-3.5" />
                      Password
                    </span>
                  </Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="create a strong password"
                    {...register('password', {
                      required: 'Password is required',
                      minLength: { value: 8, message: 'Minimum 8 characters' },
                    })}
                    autoComplete="new-password"
                  />
                  {errors.password && (
                    <p className="text-xs text-destructive">{errors.password.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">
                    <span className="flex items-center gap-1.5">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Confirm Password
                    </span>
                  </Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="repeat your password"
                    {...register('confirmPassword', {
                      required: 'Please confirm your password',
                      validate: (val) =>
                        val === watch('password') || 'Passwords do not match',
                    })}
                    autoComplete="new-password"
                  />
                  {errors.confirmPassword && (
                    <p className="text-xs text-destructive">{errors.confirmPassword.message}</p>
                  )}
                </div>

                <Separator />

                <Button
                  type="submit"
                  className="w-full"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Creating Account...
                    </>
                  ) : (
                    <>
                      <UserPlus className="h-4 w-4" />
                      Register
                    </>
                  )}
                </Button>
              </form>

              <Separator className="my-4" />

              <p className="text-sm text-muted-foreground text-center">
                Already have an account?{' '}
                <Link
                  to="/login"
                  className="text-primary hover:text-primary/80 font-medium transition-colors"
                >
                  Sign in
                </Link>
              </p>

              <div className="mt-4 p-3 rounded-lg bg-secondary/40 border border-border/40">
                <Badge className="mb-2 text-muted-foreground border border-border/50 bg-transparent">
                  Demo Credentials
                </Badge>
                <div className="text-xs text-muted-foreground space-y-0.5 font-mono">
                  <p>demo_user1 / DemoPass123!</p>
                  <p>demo_user2 / DemoPass456!</p>
                  <p>demo_user3 / DemoPass789!</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
