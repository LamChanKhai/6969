'use client';

import { useQuery } from '@tanstack/react-query';
import { listRateLimits } from '@/lib/api';
import { useState } from 'react';
import {
  ShieldAlert,
  Search,
  Filter,
  Ban,
  AlertTriangle,
  Clock,
  Eye,
  ChevronDown,
  ChevronUp,
  Monitor,
  Globe,
} from 'lucide-react';

export default function RateLimitsPage() {
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAction, setFilterAction] = useState('');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const { data: events, isLoading } = useQuery({
    queryKey: ['rateLimits', page, filterAction],
    queryFn: () => listRateLimits(undefined, undefined, filterAction || undefined, page * 50, 50),
  });

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'blocked': return <span className="badge badge-alert">Blocked</span>;
      case 'throttled': return <span className="badge badge-warning">Throttled</span>;
      case 'warned': return <span className="badge badge-copper">Warned</span>;
      default: return <span className="badge badge-muted">{action}</span>;
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'blocked': return <Ban className="w-3.5 h-3.5 text-alert" />;
      case 'throttled': return <AlertTriangle className="w-3.5 h-3.5 text-warning" />;
      case 'warned': return <AlertTriangle className="w-3.5 h-3.5 text-copper" />;
      default: return <ShieldAlert className="w-3.5 h-3.5 text-muted-foreground" />;
    }
  };

  const filteredItems = events?.items.filter((e) =>
    e.ip_address.toLowerCase().includes(searchTerm.toLowerCase()) ||
    e.endpoint.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">Rate Limit Events</h2>
          <p className="text-xs text-muted-foreground mt-1">API rate limiting and abuse prevention log</p>
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
            placeholder="Search by IP or endpoint..."
          />
        </div>
        <select
          value={filterAction}
          onChange={(e) => setFilterAction(e.target.value)}
          className="input-field text-xs py-2 w-auto"
        >
          <option value="">All Actions</option>
          <option value="blocked">Blocked</option>
          <option value="throttled">Throttled</option>
          <option value="warned">Warned</option>
        </select>
        <span className="text-xs text-muted-foreground">
          {filteredItems.length} of {events?.total ?? 0} events
        </span>
      </div>

      {/* Events Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Action</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">IP Address</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Endpoint</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Requests</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Window</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Triggered</th>
                <th className="text-right px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : filteredItems.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">No rate limit events found</td></tr>
              ) : (
                filteredItems.map((event) => (
                  <tr key={event.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {getActionIcon(event.action_taken)}
                        {getActionBadge(event.action_taken)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground font-mono">
                      <div className="flex items-center gap-1.5">
                        <Globe className="w-3 h-3" />
                        {event.ip_address}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-foreground font-mono">
                      <div className="flex items-center gap-1.5">
                        <Monitor className="w-3 h-3 text-muted-foreground" />
                        {event.endpoint}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs font-mono text-foreground">
                      {event.request_count}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground">
                      <div className="flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />
                        {new Date(event.window_start).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                        {' — '}
                        {new Date(event.window_end).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(event.created_at).toLocaleString('en-US', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit',
                      })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setExpandedRow(expandedRow === event.id ? null : event.id)}
                        className="text-muted-foreground hover:text-copper transition-colors"
                      >
                        {expandedRow === event.id ? (
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
        {events && events.total > 50 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-muted-foreground">
              Page {page + 1} of {Math.ceil(events.total / 50)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * 50 >= events.total}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Expanded Detail */}
      {expandedRow && (() => {
        const event = events?.items.find(e => e.id === expandedRow);
        if (!event) return null;
        return (
          <div className="panel p-4 animate-fade-in">
            <h4 className="font-display text-xs font-medium text-foreground mb-3 uppercase tracking-wider">Rate Limit Event Details</h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-muted-foreground">Event ID:</span>
                <span className="ml-2 font-mono text-foreground">{event.id.slice(0, 12)}...</span>
              </div>
              <div>
                <span className="text-muted-foreground">Action:</span>
                <span className="ml-2 text-foreground capitalize">{event.action_taken}</span>
              </div>
              <div>
                <span className="text-muted-foreground">IP Address:</span>
                <span className="ml-2 font-mono text-foreground">{event.ip_address}</span>
              </div>
              <div>
                <span className="text-muted-foreground">User ID:</span>
                <span className="ml-2 font-mono text-foreground">{event.user_id || 'Anonymous'}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Endpoint:</span>
                <span className="ml-2 font-mono text-foreground">{event.endpoint}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Request Count:</span>
                <span className="ml-2 font-mono text-foreground">{event.request_count}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Window Start:</span>
                <span className="ml-2 font-mono text-foreground">{new Date(event.window_start).toLocaleString()}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Window End:</span>
                <span className="ml-2 font-mono text-foreground">{new Date(event.window_end).toLocaleString()}</span>
              </div>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
