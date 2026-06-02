import { Link } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Rocket,
  Shield,
  Upload,
  Search,
  Activity,
  ArrowRight,
  LogIn,
  UserPlus,
  LayoutDashboard,
} from 'lucide-react'

export default function LandingScreen() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  const features = [
    {
      icon: <Shield className="h-5 w-5" />,
      title: 'JWT Authentication',
      desc: 'Secure token-based auth with refresh cycle',
    },
    {
      icon: <Upload className="h-5 w-5" />,
      title: 'File Transport',
      desc: 'ZIP validation and cross-service transfer',
    },
    {
      icon: <Search className="h-5 w-5" />,
      title: 'User Search',
      desc: 'Filter and paginate across user records',
    },
    {
      icon: <Activity className="h-5 w-5" />,
      title: 'Health Monitoring',
      desc: 'Real-time service status checks',
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,_rgba(42,138,122,0.12),transparent)]" />

      <header className="relative z-10 border-b border-border/50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Rocket className="h-4 w-4 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold tracking-tight">SuperApp</span>
            <Badge className="bg-primary/20 text-primary border-0 text-[10px] font-semibold uppercase tracking-wider">
              Demo
            </Badge>
          </div>
          <nav className="flex items-center gap-2">
            {isAuthenticated ? (
              <Link to="/dashboard">
                <Button size="sm" variant="outline">
                  <LayoutDashboard className="h-4 w-4" />
                  Dashboard
                </Button>
              </Link>
            ) : (
              <>
                <Link to="/login">
                  <Button size="sm" variant="ghost">
                    <LogIn className="h-4 w-4" />
                    Sign In
                  </Button>
                </Link>
                <Link to="/register">
                  <Button size="sm">
                    <UserPlus className="h-4 w-4" />
                    Register
                  </Button>
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <main className="relative z-10">
        <section className="max-w-6xl mx-auto px-6 pt-20 pb-24">
          <div className="max-w-3xl">
            <div className="animate-fade-in-up stagger-1">
              <Badge className="bg-accent/15 text-accent border-accent/20 mb-6">
                Two-Microservice Architecture
              </Badge>
            </div>

            <h1 className="animate-fade-in-up stagger-2 text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] mb-6">
              Gateway-first platform for{' '}
              <span className="text-primary">secure file operations</span>
            </h1>

            <p className="animate-fade-in-up stagger-3 text-lg text-muted-foreground leading-relaxed mb-10 max-w-2xl">
              Django REST gateway orchestrates cross-service file transport with
              PHP storage backend. JWT-authenticated endpoints, ZIP validation,
              and automated 7z extraction — all containerized.
            </p>

            <div className="animate-fade-in-up stagger-4 flex flex-wrap gap-3">
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button size="lg" className="gap-2">
                    Go to Dashboard
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/register">
                    <Button size="lg" className="gap-2">
                      Get Started
                      <ArrowRight className="h-4 w-4" />
                    </Button>
                  </Link>
                  <Link to="/login">
                    <Button size="lg" variant="outline" className="gap-2">
                      <LogIn className="h-4 w-4" />
                      Sign In
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 pb-24">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {features.map((feature, i) => (
              <div
                key={feature.title}
                className={`animate-fade-in-up stagger-${i + 2} p-5 rounded-lg border border-border/50 bg-card/50 hover:bg-card/80 hover:border-primary/20 transition-all duration-300`}
              >
                <div className="h-9 w-9 rounded-md bg-primary/10 flex items-center justify-center text-primary mb-3">
                  {feature.icon}
                </div>
                <h3 className="font-semibold mb-1">{feature.title}</h3>
                <p className="text-sm text-muted-foreground">{feature.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="max-w-6xl mx-auto px-6 pb-24">
          <div className="animate-fade-in-up stagger-5 rounded-xl border border-border/50 bg-card/30 overflow-hidden">
            <div className="px-6 py-4 border-b border-border/50 flex items-center gap-2">
              <div className="h-3 w-3 rounded-full bg-destructive/70" />
              <div className="h-3 w-3 rounded-full bg-accent/70" />
              <div className="h-3 w-3 rounded-full bg-primary/70" />
              <span className="ml-2 text-xs text-muted-foreground font-mono">
                terminal
              </span>
            </div>
            <div className="p-6 font-mono text-sm space-y-2">
              <p className="text-muted-foreground">
                <span className="text-primary">$</span> docker compose up
              </p>
              <p className="text-muted-foreground/70">
                [+] Running 2/2
              </p>
              <p>
                <span className="text-primary"> ✔</span>{' '}
                <span className="text-muted-foreground">Container app1 Started</span>
              </p>
              <p>
                <span className="text-primary"> ✔</span>{' '}
                <span className="text-muted-foreground">Container app2 Started</span>
              </p>
              <p className="text-muted-foreground/50 mt-4">
                <span className="text-accent">→</span> Gateway listening on :8000
              </p>
              <p className="text-muted-foreground/50">
                <span className="text-accent">→</span> Storage service ready
              </p>
            </div>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t border-border/50 mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between text-xs text-muted-foreground">
          <span>SuperApp Demo Phase — SA-DEMO-2025</span>
          <div className="flex items-center gap-4">
            <span>Django + uWSGI</span>
            <span>PHP + Apache</span>
            <span>Docker Compose</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
