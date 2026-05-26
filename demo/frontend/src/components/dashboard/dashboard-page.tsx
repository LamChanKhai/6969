'use client';

import { useQuery } from '@tanstack/react-query';
import { getSystemHealth, getMetrics, getSecurityDashboard } from '@/lib/api';
import {
  Shield,
  Users,
  Upload,
  AlertTriangle,
  Cpu,
  HardDrive,
  Clock,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell,
} from 'recharts';

export default function DashboardPage() {
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: getSystemHealth,
  });

  const { data: metrics } = useQuery({
    queryKey: ['metrics'],
    queryFn: getMetrics,
    refetchInterval: 5000,
  });

  const { data: security } = useQuery({
    queryKey: ['security'],
    queryFn: getSecurityDashboard,
  });

  const metricChartData = metrics ? [
    { name: 'CPU', value: metrics.cpu_usage_percent },
    { name: 'Memory', value: metrics.memory_usage_percent },
    { name: 'Disk', value: metrics.disk_usage_percent },
  ] : [];

  const severityData = security ? Object.entries(security.events_by_severity).map(([key, value]) => ({
    name: key,
    count: value,
  })) : [];

  const severityColors: Record<string, string> = {
    critical: '#e05555',
    high: '#c8a45c',
    medium: '#5ec4b0',
    low: '#3a4460',
    info: '#2a3040',
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${mins}m`;
  };

  const statCards = [
    {
      title: 'System Status',
      value: health?.status?.toUpperCase() || '—',
      icon: Shield,
      color: 'text-success',
      sub: `v${health?.version || '—'}`,
    },
    {
      title: 'Active Users',
      value: health?.active_users ?? '—',
      icon: Users,
      color: 'text-copper',
      sub: `${health?.total_uploads ?? 0} total uploads`,
    },
    {
      title: 'Active Threats',
      value: security?.active_threats ?? '—',
      icon: AlertTriangle,
      color: security?.active_threats && security.active_threats > 0 ? 'text-alert' : 'text-success',
      sub: `${security?.total_events ?? 0} total events`,
    },
    {
      title: 'Uptime',
      value: health ? formatUptime(health.uptime_seconds) : '—',
      icon: Clock,
      color: 'text-copper',
      sub: health?.database || '—',
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">Dashboard</h2>
          <p className="text-xs text-muted-foreground mt-1">Real-time platform overview</p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <Activity className="w-3.5 h-3.5 text-copper" />
          <span className="text-muted-foreground uppercase tracking-wider">Live</span>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, i) => (
          <div key={i} className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider mb-2">{card.title}</p>
                <p className={`font-display text-2xl font-semibold ${card.color}`}>{card.value}</p>
                <p className="text-[10px] text-muted-foreground mt-1">{card.sub}</p>
              </div>
              <div className={`w-9 h-9 rounded-md bg-muted/50 flex items-center justify-center ${card.color}`}>
                <card.icon className="w-4 h-4" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Resource Usage */}
        <div className="panel p-4">
          <h3 className="font-display text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-copper" />
            Resource Usage
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metricChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3040" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#141a2e',
                    border: '1px solid #2a3040',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                  formatter={(value: number) => [`${value.toFixed(1)}%`, 'Usage']}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {metricChartData.map((entry, index) => (
                    <Cell key={index} fill={['#4a9e8e', '#5ec4b0', '#3a7e6e'][index % 3]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Security Events by Severity */}
        <div className="panel p-4">
          <h3 className="font-display text-sm font-medium text-foreground mb-4 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-alert" />
            Security Events by Severity
          </h3>
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={severityData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a3040" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#141a2e',
                    border: '1px solid #2a3040',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                  formatter={(value: number, name: string) => [value, name.charAt(0).toUpperCase() + name.slice(1)]}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {severityData.map((entry, index) => (
                    <Cell key={index} fill={severityColors[entry.name] || '#4a9e8e'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Blocked Uploads */}
        <div className="panel p-4">
          <h3 className="font-display text-sm font-medium text-foreground mb-3 flex items-center gap-2">
            <Upload className="w-4 h-4 text-copper" />
            Blocked Uploads
          </h3>
          <p className="font-display text-3xl font-semibold text-alert">
            {security?.blocked_uploads ?? 0}
          </p>
          <p className="text-[11px] text-muted-foreground mt-2">
            Files blocked by security scanner
          </p>
        </div>

        {/* Recent Events */}
        <div className="panel p-4">
          <h3 className="font-display text-sm font-medium text-foreground mb-3 flex items-center gap-2">
            <Activity className="w-4 h-4 text-copper" />
            Events (24h)
          </h3>
          <p className="font-display text-3xl font-semibold text-copper">
            {security?.events_last_24h ?? 0}
          </p>
          <p className="text-[11px] text-muted-foreground mt-2">
            Security events in last 24 hours
          </p>
        </div>

        {/* Top Vulnerabilities */}
        <div className="panel p-4">
          <h3 className="font-display text-sm font-medium text-foreground mb-3 flex items-center gap-2">
            <Shield className="w-4 h-4 text-alert" />
            Top Vulnerabilities
          </h3>
          <div className="space-y-2">
            {(security?.top_vulnerabilities || []).map((vuln, i) => (
              <div key={i} className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">{vuln.type.replace('_', ' ')}</span>
                <span className="text-xs font-mono text-foreground">{vuln.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
