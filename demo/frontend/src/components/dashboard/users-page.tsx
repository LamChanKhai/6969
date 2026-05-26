'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listUsers, updateUser } from '@/lib/api';
import { useState } from 'react';
import {
  Users,
  Shield,
  UserCheck,
  UserX,
  Search,
  Edit,
  AlertCircle,
} from 'lucide-react';

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingUser, setEditingUser] = useState<string | null>(null);
  const [editRole, setEditRole] = useState('');
  const [editActive, setEditActive] = useState(true);

  const { data: users, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: () => listUsers(page * 20, 20),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setEditingUser(null);
    },
  });

  const handleSave = (userId: string) => {
    updateMutation.mutate({ id: userId, data: { role: editRole, is_active: editActive } });
  };

  const handleCancel = () => setEditingUser(null);

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin': return <span className="badge badge-alert">Admin</span>;
      case 'operator': return <span className="badge badge-copper">Operator</span>;
      case 'viewer': return <span className="badge badge-muted">Viewer</span>;
      default: return <span className="badge badge-muted">{role}</span>;
    }
  };

  const filteredItems = users?.items.filter((u) =>
    u.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="font-display text-xl font-semibold text-foreground">User Management</h2>
          <p className="text-xs text-muted-foreground mt-1">Manage platform access and roles</p>
        </div>
      </div>

      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
            placeholder="Search users..."
          />
        </div>
        <span className="text-xs text-muted-foreground">
          {filteredItems.length} of {users?.total ?? 0} users
        </span>
      </div>

      {/* Users Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">User</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Email</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Role</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Status</th>
                <th className="text-left px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Created</th>
                <th className="text-right px-4 py-3 text-xs text-muted-foreground uppercase tracking-wider font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Loading...</td></tr>
              ) : filteredItems.length === 0 ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">No users found</td></tr>
              ) : (
                filteredItems.map((user: any) => (
                  <tr key={user.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors">
                    {editingUser === user.id ? (
                      <>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-full bg-steel flex items-center justify-center text-xs font-display font-semibold text-copper">
                              {user.username.charAt(0).toUpperCase()}
                            </div>
                            <span className="text-foreground text-sm">{user.username}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">{user.email}</td>
                        <td className="px-4 py-3">
                          <select
                            value={editRole}
                            onChange={(e) => setEditRole(e.target.value)}
                            className="input-field text-xs py-1"
                          >
                            <option value="viewer">Viewer</option>
                            <option value="operator">Operator</option>
                            <option value="admin">Admin</option>
                          </select>
                        </td>
                        <td className="px-4 py-3">
                          <select
                            value={editActive ? 'active' : 'inactive'}
                            onChange={(e) => setEditActive(e.target.value === 'active')}
                            className="input-field text-xs py-1"
                          >
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                          </select>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">
                          {new Date(user.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </td>
                        <td className="px-4 py-3 text-right flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleSave(user.id)}
                            disabled={updateMutation.isPending}
                            className="btn-primary text-xs py-1 px-3"
                          >
                            Save
                          </button>
                          <button
                            onClick={handleCancel}
                            className="btn-secondary text-xs py-1 px-3"
                          >
                            Cancel
                          </button>
                        </td>
                      </>
                    ) : (
                      <>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-full bg-steel flex items-center justify-center text-xs font-display font-semibold text-copper">
                              {user.username.charAt(0).toUpperCase()}
                            </div>
                            <span className="text-foreground text-sm">{user.username}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">{user.email}</td>
                        <td className="px-4 py-3">{getRoleBadge(user.role)}</td>
                        <td className="px-4 py-3">
                          {user.is_active ? (
                            <span className="badge badge-success">Active</span>
                          ) : (
                            <span className="badge badge-alert">Inactive</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">
                          {new Date(user.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <button
                            onClick={() => {
                              setEditingUser(user.id);
                              setEditRole(user.role);
                              setEditActive(user.is_active);
                            }}
                            className="text-muted-foreground hover:text-copper transition-colors"
                          >
                            <Edit className="w-4 h-4" />
                          </button>
                        </td>
                      </>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {users && users.total > 20 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <button
              onClick={() => setPage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="btn-secondary text-xs disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-xs text-muted-foreground">
              Page {page + 1} of {Math.ceil(users.total / 20)}
            </span>
            <button
              onClick={() => setPage(page + 1)}
              disabled={(page + 1) * 20 >= users.total}
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
