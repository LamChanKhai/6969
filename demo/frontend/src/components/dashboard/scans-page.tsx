'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listScans, createScan } from '@/lib/api';
import { useState } from 'react';
import {
  Shield,
  Search,
  Filter,
  Plus,
  CheckCircle,
  Clock,
  AlertTriangle,
  Terminal,
  ChevronDown,
  ChevronUp,
  FileText,
  Code,
  Lock,
} from 'lucide-react';

export default function ScansPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterType, setFilterType] = useState('');
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    upload_id: '',
    scanner_name: '',
    scan_type: 'static',
    scan_status: 'pending',
    threats_found: 0,
    scan_details: '',
  });

  const { data: scans, isLoading } = useQuery({
    queryKey: ['scans', page, filterStatus, filterType],
    queryFn: () => listScans(undefined, filterType || undefined, filterStatus || undefined, page * 50, 50),
  });

  const createMutation = useMutation({
    mutationFn: createScan,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      setShowCreateForm(false);
      setFormData({ upload_id: '', scanner_name: '', scan_type: 'static', scan_status: 'pending', threats_found: 0, scan_details: '' });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed': return <span className="badge badge-success">Completed</span>;
      case 'passed': return <span className="badge badge-success">Passed</span>;
      case 'failed': return <span className="badge badge-alert">Failed</span>;
      case 'threats_found': return <span className="badge badge-alert">Threats Found</span>;
      case 'running': return <span className="badge badge-copper">Running</span>;
      case 'pending': return <span className="badge badge-muted">Pending</span>;
      default: return <span className="badge badge-muted">{status}</span>;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'static': return <Code className="w-3.5 h-3.5 text-muted-foreground" />;
      case 'dynamic': return <Shield className="w-3.5 h-3.5 text-muted-foreground" />;
      case 'dependency': return <Lock className="w-3.5 h-3.5 text-muted-foreground" />;
      default: return <FileText className="w-3.5 h-3.5 text-muted-foreground" />;
    }
  };

  const filteredItems = scans?.items.filter((s) =>
    s.scanner_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    s.scan_type.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">File Scan Results</h2>
          <p className="text-xs text-muted-foreground mt-1">Security scan results and threat analysis</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="btn-primary text-xs"
        >
          <Plus className="w-3.5 h-3.5" />
          New Scan
        </button>
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="panel p-5 animate-fade-in">
          <h3 className="font-display text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-copper" />
            Create Scan Result
          </h3>
          <form onSubmit={handleCreate} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label-text">Upload ID</label>
              <input
                type="text"
                value={formData.upload_id}
                onChange={(e) => setFormData({ ...formData, upload_id: e.target.value })}
                className="input-field"
                placeholder="UUID of uploaded file"
                required
              />
            </div>
            <div>
              <label className="label-text">Scanner Name</label>
              <input
                type="text"
                value={formData.scanner_name}
                onChange={(e) => setFormData({ ...formData, scanner_name: e.target.value })}
                className="input-field"
                placeholder="e.g., ClamAV, SonarQube"
                required
              />
            </div>
            <div>
              <label className="label-text">Scan Type</label>
              <select
                value={formData.scan_type}
                onChange={(e) => setFormData({ ...formData, scan_type: e.target.value })}
                className="input-field"
              >
                <option value="static">Static Analysis (SAST)</option>
                <option value="dynamic">Dynamic Analysis (DAST)</option>
                <option value="dependency">Dependency Scan</option>
                <option value="malware">Malware Scan</option>
              </select>
            </div>
            <div>
              <label className="label-text">Status</label>
              <select
                value={formData.scan_status}
                onChange={(e) => setFormData({ ...formData, scan_status: e.target.value })}
                className="input-field"
              >
                <option value="pending">Pending</option>
                <option value="running">Running</option>
                <option value="completed">Completed</option>
                <option value="passed">Passed</option>
                <option value="failed">Failed</option>
              </select>
            </div>
            <div>
              <label className="label-text">Threats Found</label>
              <input
                type="number"
                value={formData.threats_found}
                onChange={(e) => setFormData({ ...formData, threats_found: parseInt(e.target.value) || 0 })}
                className="input-field"
                min={0}
              />
            </div>
            <div>
              <label className="label-text">Details</label>
              <input
                type="text"
                value={formData.scan_details}
                onChange={(e) => setFormData({ ...formData, scan_details: e.target.value })}
                className="input-field"
                placeholder="Optional scan details"
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
                {createMutation.isPending ? 'Creating...' : 'Create Scan'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
            placeholder="Search scans..."
          />
        </div>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="input-field text-xs py-2 w-auto"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="passed">Passed</option>
          <option value="failed">Failed</option>
        </select>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="input-field text-xs py-2 w-auto"
        >
          <option value="">All Types</option>
          <option value="static">Static Analysis</option>
          <option value="dynamic">Dynamic Analysis</option>
          <option value="dependency">Dependency</option>
          <option value="malware">Malware</option>
        </select>
        <span className="text-xs text-muted-foreground">
          {filteredItems.length} of {scans?.total ?? 0} scans
        </span>
      </div>

      {/* Scans Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Scanner</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Type</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Status</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Threats</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Duration</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Scanned</th>
                <th className="text-right px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : filteredItems.length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">No scans found</td></tr>
              ) : (
                filteredItems.map((scan) => (
                  <tr key={scan.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {getTypeIcon(scan.scan_type)}
                        <span className="text-foreground text-sm">{scan.scanner_name}</span>
                        {scan.scanner_version && (
                          <span className="text-[10px] text-muted-foreground font-mono">v{scan.scanner_version}</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground capitalize">{scan.scan_type.replace('_', ' ')}</td>
                    <td className="px-4 py-3">{getStatusBadge(scan.scan_status)}</td>
                    <td className="px-4 py-3">
                      {scan.threats_found > 0 ? (
                        <span className="badge badge-alert">{scan.threats_found}</span>
                      ) : (
                        <span className="badge badge-success">0</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground font-mono">
                      {scan.duration_ms ? `${scan.duration_ms}ms` : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-muted-foreground whitespace-nowrap">
                      {new Date(scan.created_at).toLocaleString('en-US', {
                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
                      })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setExpandedRow(expandedRow === scan.id ? null : scan.id)}
                        className="text-muted-foreground hover:text-copper transition-colors"
                      >
                        {expandedRow === scan.id ? (
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
        {scans && scans.total > 50 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-muted-foreground">
              Page {page + 1} of {Math.ceil(scans.total / 50)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * 50 >= scans.total}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Expanded Detail */}
      {expandedRow && (() => {
        const scan = scans?.items.find(s => s.id === expandedRow);
        if (!scan) return null;
        return (
          <div className="panel p-4 animate-fade-in">
            <h4 className="font-display text-xs font-medium text-foreground mb-3 uppercase tracking-wider">Scan Details</h4>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-muted-foreground">Scanner:</span>
                <span className="ml-2 text-foreground">{scan.scanner_name}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Version:</span>
                <span className="ml-2 font-mono text-foreground">{scan.scanner_version || '—'}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Type:</span>
                <span className="ml-2 text-foreground capitalize">{scan.scan_type.replace('_', ' ')}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Upload ID:</span>
                <span className="ml-2 font-mono text-foreground">{scan.upload_id.slice(0, 8)}...</span>
              </div>
              <div>
                <span className="text-muted-foreground">Duration:</span>
                <span className="ml-2 font-mono text-foreground">{scan.duration_ms ? `${scan.duration_ms}ms` : '—'}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Threats:</span>
                <span className={`ml-2 font-mono font-semibold ${scan.threats_found > 0 ? 'text-alert' : 'text-success'}`}>
                  {scan.threats_found}
                </span>
              </div>
              {scan.scan_details && (
                <div className="col-span-2">
                  <span className="text-muted-foreground">Details:</span>
                  <p className="mt-1 text-foreground bg-muted/50 rounded-md p-2 font-mono text-xs">{scan.scan_details}</p>
                </div>
              )}
            </div>
          </div>
        );
      })()}
    </div>
  );
}
