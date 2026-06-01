'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listApiKeys, createApiKey, revokeApiKey } from '@/lib/api';
import { useState } from 'react';
import {
  Key,
  Plus,
  Trash2,
  Copy,
  CheckCircle,
  Clock,
  Shield,
  Eye,
  EyeOff,
} from 'lucide-react';

export default function ApiKeysPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyExpiry, setNewKeyExpiry] = useState('');
  const [newSecret, setNewSecret] = useState<string | null>(null);
  const [showSecret, setShowSecret] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const { data: keys, isLoading } = useQuery({
    queryKey: ['apiKeys', page],
    queryFn: () => listApiKeys(page * 20, 20),
  });

  const createMutation = useMutation({
    mutationFn: ({ name, expires_at }: { name: string; expires_at?: string }) => createApiKey(name, expires_at),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
      setNewSecret(data.api_key);
      setShowSecret(false);
      setNewKeyName('');
      setNewKeyExpiry('');
      setShowCreateForm(false);
    },
  });

  const revokeMutation = useMutation({
    mutationFn: revokeApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['apiKeys'] });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({ name: newKeyName, expires_at: newKeyExpiry || undefined });
  };

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  };

  const isExpired = (expiresAt: string | null) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">API Keys</h2>
          <p className="text-xs text-muted-foreground mt-1">Manage authentication keys for programmatic access</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="btn-primary text-xs"
        >
          <Plus className="w-3.5 h-3.5" />
          New Key
        </button>
      </div>

      {/* New Secret Warning */}
      {newSecret && (
        <div className="panel p-4 border-copper/30 animate-fade-in">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-copper flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-foreground mb-1">New API Key Created</p>
              <p className="text-xs text-alert mb-2">This secret is shown only once. Copy it now or it will be lost forever.</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-muted/50 rounded-md px-3 py-2 font-mono text-xs text-foreground">
                  {showSecret ? newSecret : '•'.repeat(40)}
                </div>
                <button
                  onClick={() => setShowSecret(!showSecret)}
                  className="p-2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
                <button
                  onClick={() => handleCopy(newSecret, 'new')}
                  className="p-2 text-muted-foreground hover:text-copper transition-colors"
                >
                  {copiedId === 'new' ? <CheckCircle className="w-4 h-4 text-success" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Form */}
      {showCreateForm && (
        <div className="panel p-5 animate-fade-in">
          <h3 className="font-display text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <Key className="w-4 h-4 text-copper" />
            Generate New API Key
          </h3>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label-text">Key Name</label>
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="input-field"
                placeholder="e.g., CI/CD Pipeline, Dev Environment"
                required
                maxLength={100}
              />
            </div>
            <div>
              <label className="label-text">Expires At (optional)</label>
              <input
                type="datetime-local"
                value={newKeyExpiry}
                onChange={(e) => setNewKeyExpiry(e.target.value)}
                className="input-field"
              />
            </div>
            <div className="md:col-span-2 flex gap-2 justify-end">
              <button
                type="button"
                onClick={() => setShowCreateForm(false)}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="btn-primary text-xs"
              >
                {createMutation.isPending ? 'Generating...' : 'Generate Key'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Keys Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Name</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Prefix</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Status</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Expires</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Last Used</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Created</th>
                <th className="text-right px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : keys?.items.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">No API keys found</td></tr>
              ) : (
                keys!.items.map((key) => (
                  <tr key={key.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3 text-foreground text-sm">{key.name}</td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{key.key_prefix}</td>
                    <td className="px-4 py-3">
                      {isExpired(key.expires_at) ? (
                        <span className="badge badge-alert">Expired</span>
                      ) : key.is_active ? (
                        <span className="badge badge-success">Active</span>
                      ) : (
                        <span className="badge badge-muted">Revoked</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />
                        {formatDate(key.expires_at)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {key.last_used_at ? new Date(key.last_used_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'Never'}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      {new Date(key.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {key.is_active && (
                        <button
                          onClick={() => revokeMutation.mutate(key.id)}
                          disabled={revokeMutation.isPending}
                          className="text-muted-foreground hover:text-alert transition-colors"
                          title="Revoke key"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {keys && keys.total > 20 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-muted-foreground">
              Page {page + 1} of {Math.ceil(keys.total / 20)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * 20 >= keys.total}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
