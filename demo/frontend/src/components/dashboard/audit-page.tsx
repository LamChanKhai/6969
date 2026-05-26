'use client';

import { useQuery } from '@tanstack/react-query';
import { listAuditLogs } from '@/lib/api';
import { useState } from 'react';
import {
  FileText,
  Search,
  Filter,
  Shield,
  User,
  Upload,
  Lock,
  Clock,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const actionIcons: Record<string, any> = {
  login: Lock,
  logout: Lock,
  register: User,
  file_upload: Upload,
  security_event: Shield,
  user_update: User,
};

export default function AuditPage() {
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAction, setFilterAction] = useState<string>('');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const { data: logs, isLoading } = useQuery({
    queryKey: ['audit', page, filterAction],
    queryFn: () => listAuditLogs(page * 50, 50, filterAction || undefined),
  });

  const getActionIcon = (action: string) => {
    const Icon = actionIcons[action] || FileText;
    return <Icon className="w-3.5 h-3.5 text-muted-foreground" />;
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'login': return <span className="badge badge-success">Login</span>;
      case 'logout': return <span className="badge badge-muted">Logout</span>;
      case 'register': return <span className="badge badge-copper">Register</span>;
      case 'file_upload': return <span className="badge badge-copper">Upload</span>;
      case 'security_event': return <span className="badge badge-alert">Security</span>;
      default: return <span className="badge badge-muted">{action}</span>;
    }
  };

  const filteredItems = logs?.items.filter((log) =>
    log.details.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">Audit Logs</h2>
          <p className="text-xs text-muted-foreground mt-1">Complete activity trail for compliance</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
            placeholder="Search logs..."
          />
        </div>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          className="input-field text-xs py-2 w-auto"
        >
          <option value="">All Actions</option>
          <option value="login">Login</option>
          <option value="logout">Logout</option>
          <option value="register">Register</option>
          <option value="file_upload">File Upload</option>
          <option value="security_event">Security Event</option>
        </select>
        <span className="text-xs text-muted-foreground">
          {filteredItems.length} of {logs?.total ?? 0} entries
        </span>
      </div>

      {/* Logs Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Action</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Resource</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Details</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">IP Address</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Timestamp</th>
                <th className="text-right px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : filteredItems.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No logs found</td></tr>
              ) : (
                filteredItems.map((log) => (
                  <tr key={log.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {getActionIcon(log.action)}
                        {getActionBadge(log.action)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground font-mono">
                      {log.resource_type}
                      {log.resource_id ? `:${log.resource_id.slice(0, 8)}` : ''}
                    </td>
                    <td className="px-4 py-3 text-xs text-foreground max-w-xs truncate">{log.details}</td>
                    <td className="px-4 py-3 text-xs text-muted-foreground font-mono">
                      {log.ip_address || '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setExpandedRow(expandedRow === log.id ? null : log.id)}
                        className="text-muted-foreground hover:text-copper transition-colors"
                      >
                        {expandedRow === log.id ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {logs && logs.total > 50 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-muted-foreground">
              Page {page + 1} of {Math.ceil(logs.total / 50)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * 50 >= logs.total}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Expanded Row Detail */}
      {expandedRow && (() => {
        const log = logs?.items.find(l => l.id === expandedRow);
        if (!log) return null;
        return (
          <div className="panel p-4 animate-fade-in">
            <h4 className="font-display text-xs font-medium text-foreground mb-3 uppercase tracking-wider">Log Details</h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-muted-foreground">ID:</span>
                <span className="ml-2 font-mono text-foreground">{log.id}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Action:</span>
                <span className="ml-2 text-foreground">{log.action}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Resource Type:</span>
                <span className="ml-2 text-foreground">{log.resource_type}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Resource ID:</span>
                <span className="ml-2 font-mono text-foreground">{log.resource_id || '—'}</span>
              </div>
              <div className="col-span-2">
                <span className="text-muted-foreground">Details:</span>
                <p className="mt-1 text-foreground bg-muted/50 rounded-md p-2 font-mono text-xs">{log.details}</p>
              </div>
              <div>
                <span className="text-muted-foreground">IP Address:</span>
                <span className="ml-2 font-mono text-foreground">{log.ip_address || '—'}</span>
              </div>
              <div>
                <span className="text-muted-foreground">User Agent:</span>
                <span className="ml-2 font-mono text-foreground truncate">{log.user_agent || '—'}</span>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
