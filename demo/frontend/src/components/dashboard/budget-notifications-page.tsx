'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getBudgetUsage,
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
  getUnreadNotificationCount,
} from '@/lib/api';
import {
  Bell,
  Upload,
  HardDrive,
  Activity,
  AlertTriangle,
  Check,
  Info,
  BarChart3,
  Settings,
  Loader2,
} from 'lucide-react';

export default function BudgetNotificationsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'budget' | 'notifications'>('budget');

  const { data: budget, isLoading: loadingBudget } = useQuery({
    queryKey: ['budget-usage'],
    queryFn: getBudgetUsage,
    refetchInterval: 10000,
  });

  const { data: notifications, isLoading: loadingNotifs } = useQuery({
    queryKey: ['notifications', activeTab],
    queryFn: () => listNotifications(),
  });

  const { data: unreadData } = useQuery({
    queryKey: ['unread-count'],
    queryFn: getUnreadNotificationCount,
    refetchInterval: 15000,
  });

  const markReadMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: markAllNotificationsRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-count'] });
    },
  });

  const usageBars = budget ? [
    {
      label: 'Uploads',
      percentage: budget.upload_usage,
      value: `${budget.upload_count} files`,
      limit: `${budget.upload_limit} files`,
      icon: Upload,
    },
    {
      label: 'Storage',
      percentage: budget.storage_usage,
      value: `${(budget.storage_used_bytes / (1024 * 1024)).toFixed(1)} MB`,
      limit: `${(budget.storage_limit_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`,
      icon: HardDrive,
    },
    {
      label: 'API Calls',
      percentage: budget.api_call_usage,
      value: `${budget.api_call_count.toLocaleString()}`,
      limit: `${budget.api_call_limit.toLocaleString()}`,
      icon: Activity,
    },
  ] : [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">Budget & Notifications</h2>
          <p className="text-xs text-muted-foreground mt-1">Monthly usage tracking and alerts</p>
        </div>
        <div className="flex items-center gap-2">
          {unreadData?.unread_count && unreadData.unread_count > 0 && (
            <span className="badge badge-alert flex items-center gap-1.5">
              <Bell className="w-3 h-3" />
              {unreadData.unread_count} unread
            </span>
          )}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-1 bg-muted/30 rounded-lg p-1 w-fit">
        <button
          onClick={() => setActiveTab('budget')}
          className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all ${
            activeTab === 'budget'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <BarChart3 className="w-3.5 h-3.5" />
          Monthly Budget
        </button>
        <button
          onClick={() => setActiveTab('notifications')}
          className={`flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all ${
            activeTab === 'notifications'
              ? 'bg-background text-foreground shadow-sm'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Bell className="w-3.5 h-3.5" />
          Notifications
          {unreadData?.unread_count && unreadData.unread_count > 0 && (
            <span className="w-4 h-4 rounded-full bg-alert text-white text-[10px] flex items-center justify-center">
              {unreadData.unread_count}
            </span>
          )}
        </button>
      </div>

      {/* Budget Tab */}
      {activeTab === 'budget' && (
        <div className="space-y-4">
          {loadingBudget ? (
            <div className="panel p-8 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-copper animate-spin" />
              <span className="ml-2 text-sm text-muted-foreground">Loading budget data...</span>
            </div>
          ) : !budget ? (
            <div className="panel p-8 text-center text-muted-foreground">
              No budget data available
            </div>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Month:</span>
                  <span className="badge" style={{ minWidth: '90px', justifyContent: 'center' }}>
                    {budget.month}
                  </span>
                </div>
                {budget.budget_exceeded && (
                  <span className="badge badge-alert flex items-center gap-1.5">
                    <AlertTriangle className="w-3 h-3" />
                    Budget Exceeded
                  </span>
                )}
              </div>

              <div className="panel p-4 space-y-5">
                {usageBars.map((bar, i) => {
                  const Icon = bar.icon;
                  const pct = Math.min(bar.percentage, 100);
                  const isWarning = bar.percentage >= 80 && bar.percentage < 100;
                  const isExceeded = bar.percentage >= 100;
                  const barColor = isExceeded ? 'bg-alert' : isWarning ? 'bg-copper' : 'bg-success';

                  return (
                    <div key={i}>
                      <div className="flex items-center justify-between mb-2">
                        <span className="flex items-center gap-2 text-xs text-foreground">
                          <Icon className="w-3.5 h-3.5 text-copper" />
                          {bar.label}
                        </span>
                        <span className="text-xs font-mono text-muted-foreground">
                          {bar.value} / {bar.limit}
                        </span>
                      </div>
                      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full ${barColor} rounded-full transition-all duration-500`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <p className={`text-[10px] mt-1 ${
                        isExceeded ? 'text-alert' : isWarning ? 'text-copper' : 'text-muted-foreground'
                      }`}>
                        {bar.percentage.toFixed(1)}% used
                      </p>
                    </div>
                  );
                })}
              </div>

              {budget.budget_exceeded && (
                <div className="panel p-4 border-l-2 border-l-alert">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-alert flex-shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-sm font-medium text-alert">Monthly Budget Limit Reached</h4>
                      <p className="text-xs text-muted-foreground mt-1">
                        Your monthly budget limit has been exceeded. Please contact your administrator to increase your limits or wait until the next billing cycle.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {notifications?.total ?? 0} total notifications
            </span>
            {unreadData?.unread_count && unreadData.unread_count > 0 && (
              <button
                onClick={() => markAllReadMutation.mutate()}
                className="text-xs text-copper hover:underline flex items-center gap-1"
              >
                <Check className="w-3 h-3" />
                Mark all read
              </button>
            )}
          </div>

          {loadingNotifs ? (
            <div className="panel p-8 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-copper animate-spin" />
            </div>
          ) : !notifications?.items?.length ? (
            <div className="panel p-8 text-center">
              <Bell className="w-8 h-8 text-muted-foreground mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No notifications yet</p>
            </div>
          ) : (
            <div className="space-y-2">
              {notifications.items.map((notif: any) => {
                const { icon: Icon, color, bg } = getNotificationStyle(notif.notification_type);

                return (
                  <div
                    key={notif.id}
                    className={`panel p-4 transition-all ${
                      !notif.is_read ? 'border-l-2 border-l-copper' : ''
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <div className={`w-8 h-8 rounded-md ${bg} ${color} flex items-center justify-center flex-shrink-0 mt-0.5`}>
                        <Icon className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <h4 className={`text-sm font-medium ${notif.is_read ? 'text-muted-foreground' : 'text-foreground'}`}>
                            {notif.title}
                          </h4>
                          {!notif.is_read && (
                            <button
                              onClick={() => markReadMutation.mutate(notif.id)}
                              className="text-muted-foreground hover:text-copper transition-colors flex-shrink-0"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                          {notif.message}
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-2">
                          {new Date(notif.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function getNotificationStyle(type: string) {
  switch (type) {
    case 'budget_exceeded':
      return { icon: AlertTriangle, color: 'text-alert', bg: 'bg-alert/10' };
    case 'budget_warning':
      return { icon: AlertTriangle, color: 'text-copper', bg: 'bg-copper/10' };
    default:
      return { icon: Info, color: 'text-copper', bg: 'bg-copper/10' };
  }
}
