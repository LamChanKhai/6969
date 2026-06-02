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
  LogIn,
  User,
  Lock,
  ArrowLeft,
  AlertCircle,
} from 'lucide-react'

interface LoginForm {
  username: string
  password: string
}

export default function LoginScreen() {
  const navigate = useNavigate()
  const login = useAuthStore((s) => s.login)
  const [error, setError] = useState('')

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>()

  const onSubmit = async (data: LoginForm) => {
    setError('')
    try {
      await login(data)
      navigate('/dashboard')
    } catch {
      setError('Invalid username or password')
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
                  <LogIn className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <CardTitle>Sign In</CardTitle>
                  <CardDescription>
                    Enter your credentials to continue
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
                    {...register('username', { required: 'Username is required' })}
                    autoComplete="username"
                  />
                  {errors.username && (
                    <p className="text-xs text-destructive">{errors.username.message}</p>
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
                    placeholder="enter your password"
                    {...register('password', { required: 'Password is required' })}
                    autoComplete="current-password"
                  />
                  {errors.password && (
                    <p className="text-xs text-destructive">{errors.password.message}</p>
                  )}
                </div>

                <Separator />

                <Button type="submit" className="w-full">
                  <LogIn className="h-4 w-4" />
                  Sign In
                </Button>
              </form>

              <Separator className="my-4" />

              <p className="text-sm text-muted-foreground text-center">
                Don&apos;t have an account?{' '}
                <Link
                  to="/register"
                  className="text-primary hover:text-primary/80 font-medium transition-colors"
                >
                  Register
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
