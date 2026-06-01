'use client';

import { useQuery } from '@tanstack/react-query';
import { getMetrics, getSystemHealth } from '@/lib/api';
import {
  Cpu,
  HardDrive,
  MemoryStick,
  Network,
  Activity,
  Clock,
  Server,
  Gauge,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
} from 'recharts';

export default function MonitoringPage() {
  const { data: metrics, isLoading: loading1 } = useQuery({
    queryKey: ['metrics'],
    queryFn: getMetrics,
    refetchInterval: 3000,
  });

  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: getSystemHealth,
  });

  const radialData = metrics ? [
    { name: 'CPU', value: metrics.cpu_usage_percent, fill: '#4a9e8e' },
    { name: 'Memory', value: metrics.memory_usage_percent, fill: '#5ec4b0' },
    { name: 'Disk', value: metrics.disk_usage_percent, fill: '#3a7e6e' },
  ] : [];

  const gaugeCards = [
    {
      title: 'CPU Usage',
      value: metrics?.cpu_usage_percent ?? 0,
      icon: Cpu,
      color: '#4a9e8e',
    },
    {
      title: 'Memory',
      value: metrics?.memory_usage_percent ?? 0,
      icon: MemoryStick,
      color: '#5ec4b0',
    },
    {
      title: 'Disk',
      value: metrics?.disk_usage_percent ?? 0,
      icon: HardDrive,
      color: '#3a7e6e',
    },
  ];

  const systemInfo = [
    { label: 'Version', value: health?.version || '—', icon: Server },
    { label: 'Database', value: health?.database || '—', icon: Activity },
    { label: 'Storage Path', value: health?.storage_path || '—', icon: HardDrive },
    { label: 'Active Connections', value: metrics?.active_connections ?? '—', icon: Network },
    { label: 'Requests/min', value: metrics?.requests_per_minute?.toFixed(1) ?? '—', icon: Gauge },
    { label: 'Avg Response', value: metrics?.avg_response_time_ms ? `${metrics.avg_response_time_ms.toFixed(0)}ms` : '—', icon: Clock },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">Monitoring</h2>
          <p className="text-xs text-muted-foreground mt-1">Real-time system health & metrics</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
          <span className="text-muted-foreground uppercase tracking-wider">Live Updates</span>
        </div>
      </div>

      {/* Gauge Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {gaugeCards.map((card, i) => (
          <div key={i} className="panel p-4 flex items-center gap-4">
            <div className="w-20 h-20 flex-shrink-0">
              <ResponsiveContainer width="100%" height="100%">
                <RadialBarChart
                  cx="50%"
                  cy="50%"
                  innerRadius={30}
                  outerRadius={45}
                  startAngle={90}
                  endAngle={-270}
                  data={[{ value: card.value, fill: card.color }]}
                >
                  <RadialBar
                    dataKey="value"
                    name="value"
                    startAngle={90}
                    endAngle={-270}
                    background={{ fill: '#1e2640' }}
                    cornerRadius={4}
                  />
                </RadialBarChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-mono font-semibold text-foreground">{Math.round(card.value)}%</span>
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <card.icon className="w-4 h-4 text-copper" />
                <span className="text-sm font-medium text-foreground">{card.title}</span>
              </div>
              <p className="text-[11px] text-muted-foreground">
                {card.value > 80 ? 'High usage' : card.value > 50 ? 'Moderate' : 'Normal'}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* System Info */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="panel p-4">
          <h3 className="font-display text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <Server className="w-4 h-4 text-copper" />
            System Information
          </h3>
          <div className="space-y-3">
            {systemInfo.map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <item.icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{item.label}</p>
                  <p className="text-sm text-foreground font-mono truncate">{item.value}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Uptime Bar */}
        <div className="panel p-4">
          <h3 className="font-display text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <Clock className="w-4 h-4 text-copper" />
            Service Status
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-foreground">API Service</span>
                <span className="badge badge-success">Operational</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-copper rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-foreground">Database</span>
                <span className="badge badge-success">Connected</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-copper rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-foreground">Storage</span>
                <span className="badge badge-success">Available</span>
              </div>
              <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-copper rounded-full" style={{ width: '100%' }} />
              </div>
            </div>
            <div className="pt-2 border-t border-border">
              <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-1">Uptime</p>
              <p className="font-display text-lg font-semibold text-copper">
                {health ? (() => {
                  const d = Math.floor(health.uptime_seconds / 86400);
                  const h = Math.floor((health.uptime_seconds % 86400) / 3600);
                  const m = Math.floor((health.uptime_seconds % 3600) / 60);
                  return `${d}d ${h}h ${m}m`;
                })() : '—'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
