import { useState, useCallback } from 'react'
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import { useAuthStore } from '@/stores/authStore'
import { api, type User } from '@/services/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Alert } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  LogOut,
  UploadCloud,
  Activity,
  Search,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileArchive,
  UserSearch,
  RefreshCw,
  X,
  ChevronRight,
  LogIn,
  Clock,
} from 'lucide-react'

export default function DashboardScreen() {
  const username = useAuthStore((s) => s.username)
  const logout = useAuthStore((s) => s.logout)

  const [healthStatus, setHealthStatus] = useState<'idle' | 'loading' | 'ok' | 'err'>('idle')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [uploadStatus, setUploadStatus] = useState<{
    state: 'idle' | 'loading' | 'success' | 'error' | 'invalid'
    message?: string
  }>({ state: 'idle' })
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<User[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [dragOver, setDragOver] = useState(false)

  const checkHealth = useCallback(async () => {
    setHealthStatus('loading')
    try {
      const result = (await api.health()) as string
      setHealthStatus(result === 'OK' ? 'ok' : 'err')
    } catch {
      setHealthStatus('err')
    }
  }, [])

  const handleFileSelect = (file: File) => {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      setUploadStatus({ state: 'error', message: 'Only .zip files are accepted' })
      return
    }
    setSelectedFile(file)
    setUploadStatus({ state: 'idle' })
  }

  const handleUpload = async () => {
    if (!selectedFile) return
    setUploadStatus({ state: 'loading' })
    try {
      const result = await api.upload(selectedFile)
      const statusText =
        typeof result === 'string' ? result : result?.status ?? String(result)
      if (statusText.includes('Invalid')) {
        setUploadStatus({ state: 'invalid', message: 'ZIP contains disallowed file types' })
      } else {
        setUploadStatus({ state: 'success', message: 'File uploaded and extracted successfully' })
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setUploadStatus({ state: 'error', message: msg })
    }
    setSelectedFile(null)
  }

  const removeFile = () => {
    setSelectedFile(null)
    setUploadStatus({ state: 'idle' })
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) return
    setSearchLoading(true)
    setSearchError('')
    try {
      const results = await api.searchUsers({ username: searchQuery })
      const users = Array.isArray(results) ? results : []
      setSearchResults(users)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Search failed'
      setSearchError(msg)
      setSearchResults([])
    } finally {
      setSearchLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,_rgba(42,138,122,0.08),transparent)]" />

      <header className="relative z-10 border-b border-border/50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Activity className="h-4 w-4 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight">SuperApp</h1>
              <p className="text-xs text-muted-foreground">
                Dashboard — {username}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Badge className="bg-primary/15 text-primary border-0 text-xs">
              <Clock className="h-3 w-3 mr-1" />
              Session Active
            </Badge>
            <Button size="sm" variant="outline" onClick={logout}>
              <LogOut className="h-4 w-4" />
              Sign Out
            </Button>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-6xl mx-auto px-6 py-8">
        <div className="animate-fade-in-up mb-8">
          <h2 className="text-2xl font-bold mb-1">Operations Console</h2>
          <p className="text-muted-foreground text-sm">
            Manage uploads, check services, and search users
          </p>
        </div>

        <Tabs defaultValue="upload" className="animate-fade-in-up stagger-2">
          <TabsList className="bg-secondary/50 border border-border/50 mb-8">
            <TabsTrigger value="upload" className="gap-2">
              <UploadCloud className="h-4 w-4" />
              File Upload
            </TabsTrigger>
            <TabsTrigger value="health" className="gap-2">
              <Activity className="h-4 w-4" />
              Health Check
            </TabsTrigger>
            <TabsTrigger value="search" className="gap-2">
              <Search className="h-4 w-4" />
              User Search
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <UploadCloud className="h-5 w-5 text-primary" />
                    Upload ZIP Archive
                  </CardTitle>
                  <CardDescription>
                    Supported: .txt, .docx, .png, .jpg, .jpeg
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div
                    className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer ${
                      dragOver
                        ? 'border-primary bg-primary/5'
                        : 'border-border/50 hover:border-primary/40 hover:bg-secondary/30'
                    }`}
                    onDragOver={(e) => {
                      e.preventDefault()
                      setDragOver(true)
                    }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={(e) => {
                      e.preventDefault()
                      setDragOver(false)
                      const file = e.dataTransfer.files[0]
                      if (file) handleFileSelect(file)
                    }}
                    onClick={() => {
                      const input = document.createElement('input')
                      input.type = 'file'
                      input.accept = '.zip'
                      input.onchange = (e: Event) => {
                        const file = (e.target as HTMLInputElement).files?.[0]
                        if (file) handleFileSelect(file)
                      }
                      input.click()
                    }}
                  >
                    <FileArchive className="h-10 w-10 mx-auto text-muted-foreground mb-3" />
                    <p className="text-sm font-medium mb-1">
                      Drop ZIP file here or click to browse
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Max practical size: ~1MB
                    </p>
                  </div>

                  {selectedFile && (
                    <div className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 border border-border/40 animate-slide-in">
                      <div className="flex items-center gap-2 min-w-0">
                        <FileArchive className="h-4 w-4 text-primary shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-medium truncate">
                            {selectedFile.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {(selectedFile.size / 1024).toFixed(1)} KB
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={removeFile}
                          className="h-7 w-7 p-0"
                        >
                          <X className="h-3.5 w-3.5" />
                        </Button>
                        <Button size="sm" onClick={handleUpload}>
                          {uploadStatus.state === 'loading' ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <UploadCloud className="h-3.5 w-3.5" />
                          )}
                          Upload
                        </Button>
                      </div>
                    </div>
                  )}

                  {uploadStatus.state === 'success' && (
                    <Alert variant="success" className="animate-slide-in">
                      <CheckCircle2 className="h-4 w-4 shrink-0 mt-0.5" />
                      <span className="text-sm">{uploadStatus.message}</span>
                    </Alert>
                  )}

                  {uploadStatus.state === 'invalid' && (
                    <Alert variant="destructive" className="animate-slide-in">
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                      <span className="text-sm">{uploadStatus.message}</span>
                    </Alert>
                  )}

                  {uploadStatus.state === 'error' && (
                    <Alert variant="destructive" className="animate-slide-in">
                      <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                      <span className="text-sm">{uploadStatus.message}</span>
                    </Alert>
                  )}
                </CardContent>
              </Card>

              <Card className="border-border/60">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-accent" />
                    Upload Status
                  </CardTitle>
                  <CardDescription>
                    Real-time operation feedback
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="p-4 rounded-lg bg-secondary/30 border border-border/40">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-sm font-medium">Service</span>
                        <Badge
                          className={
                            uploadStatus.state === 'loading'
                              ? 'bg-accent/15 text-accent border-0'
                              : uploadStatus.state === 'success'
                                ? 'bg-primary/15 text-primary border-0'
                                : uploadStatus.state === 'error' ||
                                    uploadStatus.state === 'invalid'
                                  ? 'bg-destructive/15 text-destructive border-0'
                                  : 'bg-secondary text-muted-foreground border-0'
                          }
                        >
                          {uploadStatus.state === 'loading'
                            ? 'Processing'
                            : uploadStatus.state === 'success'
                              ? 'Completed'
                              : uploadStatus.state === 'error' ||
                                  uploadStatus.state === 'invalid'
                                ? 'Failed'
                                : 'Idle'}
                        </Badge>
                      </div>
                      <Separator className="mb-3" />
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Gateway</span>
                          <span className="font-mono">app1 :8000</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Storage</span>
                          <span className="font-mono">app2 (internal)</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Auth</span>
                          <span className="font-mono">JWT Bearer</span>
                        </div>
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-secondary/30 border border-border/40">
                      <h4 className="text-sm font-medium mb-2">Pipeline</h4>
                      <div className="space-y-2">
                        {[
                          { step: 'Client → Gateway', done: uploadStatus.state !== 'idle' && uploadStatus.state !== 'error' },
                          { step: 'ZIP Validation', done: uploadStatus.state === 'success' },
                          { step: 'Forward to App2', done: uploadStatus.state === 'success' },
                          { step: '7z Extraction', done: uploadStatus.state === 'success' },
                        ].map((item, i) => (
                          <div
                            key={item.step}
                            className="flex items-center gap-2 text-sm animate-slide-in"
                            style={{ animationDelay: `${i * 50}ms` }}
                          >
                            <ChevronRight
                              className={`h-3.5 w-3.5 ${
                                item.done ? 'text-primary' : 'text-muted-foreground/40'
                              }`}
                            />
                            <span
                              className={
                                item.done
                                  ? 'text-foreground'
                                  : 'text-muted-foreground/60'
                              }
                            >
                              {item.step}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="health">
            <Card className="border-border/60 max-w-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-primary" />
                  Service Health Check
                </CardTitle>
                <CardDescription>
                  Probe App2 via the App1 gateway
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <Button onClick={checkHealth} disabled={healthStatus === 'loading'}>
                    {healthStatus === 'loading' ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Checking...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4" />
                        Check Health
                      </>
                    )}
                  </Button>

                  {healthStatus === 'ok' && (
                    <Badge className="bg-primary/15 text-primary border-0 animate-slide-in">
                      <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
                      OK
                    </Badge>
                  )}
                  {healthStatus === 'err' && (
                    <Badge className="bg-destructive/15 text-destructive border-0 animate-slide-in">
                      <AlertCircle className="h-3.5 w-3.5 mr-1" />
                      Error
                    </Badge>
                  )}
                </div>

                <div className="p-4 rounded-lg bg-secondary/30 border border-border/40 font-mono text-sm">
                  <p className="text-muted-foreground mb-1">Endpoint</p>
                  <p>GET /gateway/health/?module=/health.php</p>
                  <Separator className="my-3" />
                  <p className="text-muted-foreground mb-1">Response</p>
                  <p
                    className={
                      healthStatus === 'ok'
                        ? 'text-primary'
                        : healthStatus === 'err'
                          ? 'text-destructive'
                          : 'text-muted-foreground/50'
                    }
                  >
                    {healthStatus === 'ok'
                      ? '"OK"'
                      : healthStatus === 'err'
                        ? '"ERR"'
                        : '—'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="search">
            <Card className="border-border/60 max-w-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserSearch className="h-5 w-5 text-primary" />
                  Find Users
                </CardTitle>
                <CardDescription>
                  Search across registered accounts
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <div className="flex-1 space-y-2">
                    <Label htmlFor="search">Username or Email</Label>
                    <Input
                      id="search"
                      placeholder="search users..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    />
                  </div>
                  <div className="flex items-end">
                    <Button
                      onClick={handleSearch}
                      disabled={searchLoading || !searchQuery.trim()}
                    >
                      {searchLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Search className="h-4 w-4" />
                      )}
                      Search
                    </Button>
                  </div>
                </div>

                {searchError && (
                  <Alert variant="destructive" className="animate-slide-in">
                    <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                    <span className="text-sm">{searchError}</span>
                  </Alert>
                )}

                {searchResults.length > 0 && (
                  <div className="space-y-2 animate-slide-in">
                    <p className="text-sm text-muted-foreground">
                      {searchResults.length} result{searchResults.length !== 1 ? 's' : ''} found
                    </p>
                    <div className="rounded-lg border border-border/50 divide-y divide-border/30">
                      {searchResults.map((user, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-3 bg-secondary/20"
                        >
                          <div className="flex items-center gap-3">
                            <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                              <LogIn className="h-4 w-4 text-primary" />
                            </div>
                            <div>
                              <p className="text-sm font-medium">{user.username}</p>
                              <p className="text-xs text-muted-foreground">
                                {user.email}
                              </p>
                            </div>
                          </div>
                          <Badge className="bg-secondary text-muted-foreground border-0">
                            {user.id ? 'Active' : 'Pending'}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {searchResults.length === 0 && !searchError && searchQuery.trim() !== '' && (
                  <Alert className="animate-slide-in">
                    <Search className="h-4 w-4 shrink-0 mt-0.5" />
                    <span className="text-sm">No users match &ldquo;{searchQuery}&rdquo;</span>
                  </Alert>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      <footer className="relative z-10 border-t border-border/50 mt-auto">
        <div className="max-w-6xl mx-auto px-6 py-6 flex items-center justify-between text-xs text-muted-foreground">
          <span>SuperApp Demo Phase — SA-DEMO-2025</span>
          <div className="flex items-center gap-4">
            <span>Gateway: app1 (Django)</span>
            <span>Storage: app2 (PHP)</span>
          </div>
        </div>
      </footer>
    </div>
  )
}
