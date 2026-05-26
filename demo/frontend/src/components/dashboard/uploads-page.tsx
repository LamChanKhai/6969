'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listUploads, uploadFile, getExtractionStatus } from '@/lib/api';
import { useState } from 'react';
import {
  Upload,
  FileText,
  Shield,
  ShieldAlert,
  CheckCircle,
  AlertTriangle,
  Clock,
  Trash2,
  Eye,
  Search,
  Filter,
  Archive,
  Download,
} from 'lucide-react';

export default function UploadsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUpload, setSelectedUpload] = useState<string | null>(null);

  const { data: uploads, isLoading } = useQuery({
    queryKey: ['uploads', page],
    queryFn: () => listUploads(page * 20, 20),
  });

  const uploadMutation = useMutation({
    mutationFn: uploadFile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['uploads'] });
    },
  });

  const { data: extractionStatus } = useQuery({
    queryKey: ['extraction', selectedUpload],
    queryFn: () => getExtractionStatus(selectedUpload!),
    enabled: !!selectedUpload,
  });

  const handleFileDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      await uploadMutation.mutateAsync(file);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await uploadMutation.mutateAsync(file);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'passed': return <span className="badge badge-success">Passed</span>;
      case 'blocked': return <span className="badge badge-alert">Blocked</span>;
      case 'scanning': return <span className="badge badge-warning">Scanning</span>;
      case 'completed': return <span className="badge badge-success">Completed</span>;
      case 'extracting': return <span className="badge badge-copper">Extracting</span>;
      case 'failed': return <span className="badge badge-alert">Failed</span>;
      case 'not_applicable': return <span className="badge badge-muted">N/A</span>;
      default: return <span className="badge badge-muted">{status}</span>;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const filteredItems = uploads?.items.filter((u) =>
    u.original_filename.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">File Uploads</h2>
          <p className="text-xs text-muted-foreground mt-1">Security-scanned file management</p>
        </div>
      </div>

      {/* Upload Zone */}
      <div
        className="panel p-8 border-2 border-dashed border-border hover:border-copper/30 transition-colors cursor-pointer"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleFileDrop}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept=".txt,.docx,.png,.jpg,.jpeg,.pdf,.xlsx,.zip"
        />
        <div className="flex flex-col items-center gap-3">
          {uploadMutation.isPending ? (
            <>
              <span className="w-10 h-10 border-2 border-copper/30 border-t-copper rounded-full animate-spin" />
              <p className="text-sm text-copper">Uploading & scanning...</p>
            </>
          ) : (
            <>
              <div className="w-12 h-12 rounded-lg bg-copper/10 flex items-center justify-center">
                <Upload className="w-6 h-6 text-copper" />
              </div>
              <p className="text-sm text-foreground">Drop a file here or click to browse</p>
              <p className="text-xs text-muted-foreground">
                Supported: TXT, DOCX, PNG, JPG, PDF, XLSX, ZIP (max 50MB)
              </p>
            </>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
            placeholder="Search files..."
          />
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Filter className="w-3.5 h-3.5" />
          <span>{filteredItems.length} of {uploads?.total ?? 0} files</span>
        </div>
      </div>

      {/* Files Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">File</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Size</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Scan</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Extraction</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Uploaded</th>
                <th className="text-right px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : filteredItems.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No files found</td></tr>
              ) : (
                filteredItems.map((upload) => (
                  <tr key={upload.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-muted-foreground" />
                        <span className="text-foreground text-sm">{upload.original_filename}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{formatFileSize(upload.file_size)}</td>
                    <td className="px-4 py-3">{getStatusBadge(upload.security_scan_status)}</td>
                    <td className="px-4 py-3">{getStatusBadge(upload.extraction_status)}</td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">
                      {new Date(upload.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => setSelectedUpload(selectedUpload === upload.id ? null : upload.id)}
                        className="text-muted-foreground hover:text-copper transition-colors"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {uploads && uploads.total > 20 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-muted-foreground">
              Page {page + 1} of {Math.ceil(uploads.total / 20)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * 20 >= uploads.total}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Extraction Details */}
      {selectedUpload && extractionStatus && (
        <div className="panel p-4 animate-fade-in">
          <h3 className="font-display text-sm font-medium text-foreground mb-3 flex items-center gap-2">
            <Archive className="w-4 h-4 text-copper" />
            Extraction Events — {extractionStatus.status}
          </h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {extractionStatus.events.length === 0 ? (
              <p className="text-xs text-muted-foreground">No events recorded</p>
            ) : (
              extractionStatus.events.map((event, i) => (
                <div key={i} className="flex items-start gap-3 p-2 rounded-md bg-muted/30">
                  <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                    event.status === 'success' ? 'bg-success' :
                    event.status === 'error' ? 'bg-alert' :
                    event.status === 'warning' ? 'bg-warning' : 'bg-muted-foreground'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-foreground">{event.message}</p>
                    <p className="text-[10px] text-muted-foreground font-mono truncate">{event.file_path}</p>
                  </div>
                  <span className="text-[10px] text-muted-foreground flex-shrink-0">
                    {new Date(event.created_at).toLocaleTimeString()}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
