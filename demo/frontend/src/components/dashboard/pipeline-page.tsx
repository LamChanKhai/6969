'use client';

import { useQuery } from '@tanstack/react-query';
import { getPipelineOverview } from '@/lib/api';
import {
  GitBranch,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Shield,
  Code,
  Bug,
  Rocket,
  Lock,
  Eye,
  Terminal,
} from 'lucide-react';

const stageIcons: Record<string, any> = {
  'Source Code': Code,
  'Build': Terminal,
  'SAST': Bug,
  'DAST': Shield,
  'Dependency Scan': Lock,
  'Container Scan': Eye,
  'Deploy': Rocket,
};

export default function PipelinePage() {
  const { data: pipeline, isLoading } = useQuery({
    queryKey: ['pipeline'],
    queryFn: getPipelineOverview,
    refetchInterval: 10000,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="w-4 h-4 text-success" />;
      case 'failed': return <XCircle className="w-4 h-4 text-alert" />;
      case 'running': return <Loader2 className="w-4 h-4 text-copper animate-spin" />;
      case 'pending': return <Clock className="w-4 h-4 text-muted-foreground" />;
      default: return <Clock className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success': return <span className="badge badge-success">Success</span>;
      case 'failed': return <span className="badge badge-alert">Failed</span>;
      case 'running': return <span className="badge badge-copper">Running</span>;
      case 'pending': return <span className="badge badge-muted">Pending</span>;
      default: return <span className="badge badge-muted">{status}</span>;
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return '—';
    if (seconds < 60) return `${seconds}s`;
    return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  };

  const stages = pipeline?.stages.sort((a, b) => a.stage_order - b.stage_order) || [];
  const runs = pipeline?.latest_runs || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">DevSecOps Pipeline</h2>
          <p className="text-xs text-muted-foreground mt-1">CI/CD pipeline with integrated security gates</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground uppercase tracking-wider">Overall:</span>
          {getStatusBadge(pipeline?.overall_status || 'pending')}
        </div>
      </div>

      {/* Pipeline Stages Visualization */}
      <div className="panel p-6">
        <h3 className="font-display text-sm font-medium text-foreground mb-6 flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-copper" />
          Pipeline Stages
        </h3>
        <div className="flex items-center gap-0 overflow-x-auto pb-2">
          {stages.map((stage, i) => {
            const Icon = stageIcons[stage.stage_name] || GitBranch;
            const latestRun = runs.find(r => r.stage_name === stage.stage_name);
            return (
              <div key={stage.id} className="flex items-center">
                {/* Stage Node */}
                <div className="flex flex-col items-center gap-2 min-w-[120px]">
                  <div className={`
                    w-14 h-14 rounded-lg flex items-center justify-center border-2 transition-all
                    ${latestRun?.status === 'success' ? 'border-success/30 bg-success/10' :
                      latestRun?.status === 'failed' ? 'border-alert/30 bg-alert/10' :
                      latestRun?.status === 'running' ? 'border-copper/30 bg-copper/10' :
                      'border-border bg-muted/30'}
                  `}>
                    <Icon className={`w-6 h-6 ${
                      latestRun?.status === 'success' ? 'text-success' :
                      latestRun?.status === 'failed' ? 'text-alert' :
                      latestRun?.status === 'running' ? 'text-copper' :
                      'text-muted-foreground'
                    }`} />
                  </div>
                  <div className="text-center">
                    <p className="text-xs font-medium text-foreground">{stage.stage_name}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{latestRun?.status || 'pending'}</p>
                    {latestRun?.duration_seconds && (
                      <p className="text-[10px] text-muted-foreground font-mono">
                        {formatDuration(latestRun.duration_seconds)}
                      </p>
                    )}
                  </div>
                </div>

                {/* Connector */}
                {i < stages.length - 1 && (
                  <div className="flex-1 mx-2 min-w-[20px]">
                    <div className={`h-0.5 ${
                      latestRun?.status === 'success' ? 'bg-success/40' :
                      latestRun?.status === 'failed' ? 'bg-alert/40' :
                      'bg-border'
                    }`} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Latest Runs */}
      <div className="panel overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-muted/30">
          <h3 className="font-display text-sm font-medium text-foreground flex items-center gap-2">
            <Terminal className="w-4 h-4 text-copper" />
            Latest Pipeline Runs
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Stage</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Run</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Status</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Duration</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Started</th>
              </tr>
            </thead>
            <tbody>
              {runs.length === 0 ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No runs recorded</td></tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {(() => {
                          const Icon = stageIcons[run.stage_name] || GitBranch;
                          return <Icon className="w-4 h-4 text-muted-foreground" />;
                        })()}
                        <span className="text-foreground text-sm">{run.stage_name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">#{run.run_number}</td>
                    <td className="px-4 py-3">{getStatusBadge(run.status)}</td>
                    <td className="px-4 py-3 text-muted-foreground font-mono text-xs">{formatDuration(run.duration_seconds)}</td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">
                      {new Date(run.started_at).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
