import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Eye, Trash2, ChevronLeft, ChevronRight, X, AlertCircle, RefreshCw, Plus } from 'lucide-react';
import { Card, Button, Input, Select, StatusBadge } from '@/components';
import { getTasks, deleteTask } from '@/services/api';
import type { Task } from '@/services/api';


const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [currentPage, setCurrentPage] = useState(1);
  const rowsPerPage = 10;

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal state for Delete & Re-run
  const [modal, setModal] = useState<{ type: 'rerun' | 'delete' | null; task: Task | null }>({ type: null, task: null });
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchTasks = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getTasks({ limit: 100 });
      setTasks(res.items || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load task history from backend server.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const filtered = useMemo(() => {
    let result = tasks;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(r => r.prompt.toLowerCase().includes(q));
    }
    if (statusFilter !== 'All') {
      result = result.filter(r => r.status.toLowerCase() === statusFilter.toLowerCase());
    }
    return result;
  }, [tasks, searchQuery, statusFilter]);

  const totalPages = Math.ceil(filtered.length / rowsPerPage);
  const paginated = filtered.slice((currentPage - 1) * rowsPerPage, currentPage * rowsPerPage);

  const handleDeleteTask = async () => {
    if (!modal.task) return;
    setIsDeleting(true);
    try {
      await deleteTask(modal.task.id);
      setTasks(prev => prev.filter(t => t.id !== modal.task!.id));
      setModal({ type: null, task: null });
    } catch (err: any) {
      alert("Failed to delete task: " + err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-8 animate-fade-in pb-12 min-w-0">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-dp-text tracking-tight">
            Workflow History
          </h2>
          <p className="text-base text-dp-text-secondary mt-1">
            View, track and manage previous data collection tasks.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" icon={<RefreshCw className="w-4 h-4" />} onClick={fetchTasks} loading={isLoading}>
            Refresh
          </Button>
          <Button icon={<Plus className="w-4 h-4" />} onClick={() => navigate('/new-task')}>
            New Task
          </Button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <Card variant="bordered" padding="md" className="border-dp-error/40 bg-dp-error/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-dp-error shrink-0" />
              <div>
                <h4 className="font-semibold text-dp-text text-sm">Error Loading History</h4>
                <p className="text-xs text-dp-text-secondary mt-0.5">{error}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={fetchTasks}>Retry</Button>
          </div>
        </Card>
      )}

      {/* ── Table Card ── */}
      <Card variant="bordered" padding="none" className="overflow-hidden bg-dp-bg-raised">
        {/* Toolbar */}
        <div className="p-4 border-b border-dp-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <Input
            icon={<Search className="w-4 h-4" />}
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
            fullWidth={false}
            className="w-full sm:w-64"
          />
          <Select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
            fullWidth={false}
            className="w-40"
          >
            <option value="All">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </Select>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left whitespace-nowrap">
            <thead className="bg-dp-bg-surface text-dp-text-muted text-xs uppercase border-b border-dp-border">
              <tr>
                <th className="px-6 py-3 font-medium">Task Prompt</th>
                <th className="px-6 py-3 font-medium">Created</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Progress</th>
                <th className="px-6 py-3 font-medium">Records</th>
                <th className="px-6 py-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-dp-border">
              {isLoading ? (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-dp-text-muted">Loading workflow history...</td></tr>
              ) : paginated.length > 0 ? paginated.map((row) => (
                <tr key={row.id} className="hover:bg-dp-bg-hover/50 transition-colors">
                  <td className="px-6 py-4 font-medium text-dp-text max-w-md truncate" title={row.prompt}>
                    {row.prompt}
                  </td>
                  <td className="px-6 py-4 text-dp-text-secondary">
                    {new Date(row.created_at).toLocaleDateString()} {new Date(row.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={row.status.charAt(0).toUpperCase() + row.status.slice(1)} />
                  </td>
                  <td className="px-6 py-4 text-dp-accent font-semibold">
                    {row.progress}%
                  </td>
                  <td className="px-6 py-4 text-dp-text-secondary">
                    {(row.record_count || 0).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-end gap-2">
                      <button 
                        onClick={() => navigate(`/workflow/${row.id}`)} 
                        className="p-1.5 rounded text-dp-text-muted hover:text-dp-accent hover:bg-dp-bg-surface transition-colors cursor-pointer" 
                        title="View Workflow"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => setModal({ type: 'delete', task: row })} 
                        className="p-1.5 rounded text-dp-text-muted hover:text-dp-error hover:bg-dp-bg-surface transition-colors cursor-pointer" 
                        title="Delete Task"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={6} className="px-6 py-12 text-center text-dp-text-muted">No workflows found.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="p-4 border-t border-dp-border flex items-center justify-between bg-dp-bg-surface/50">
          <span className="text-sm text-dp-text-secondary">
            Showing <span className="font-medium text-dp-text">{filtered.length}</span> workflows
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" icon={<ChevronLeft className="w-4 h-4" />} disabled={currentPage === 1} onClick={() => setCurrentPage(p => Math.max(1, p - 1))} />
            <span className="text-sm text-dp-text-secondary px-2">Page {currentPage} of {totalPages || 1}</span>
            <Button variant="outline" size="sm" icon={<ChevronRight className="w-4 h-4" />} disabled={currentPage >= totalPages || totalPages === 0} onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} />
          </div>
        </div>
      </Card>

      {/* ── Confirmation Modal ── */}
      {modal.type && modal.task && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in" onClick={() => setModal({ type: null, task: null })}>
          <div className="bg-dp-bg-raised border border-dp-border rounded-[var(--radius-card)] p-6 max-w-md w-full mx-4 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-dp-text">
                Delete Task & Dataset
              </h3>
              <button onClick={() => setModal({ type: null, task: null })} className="p-1 rounded text-dp-text-muted hover:text-dp-text hover:bg-dp-bg-hover transition-colors cursor-pointer">
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-sm text-dp-text-secondary mb-6">
              Are you sure you want to delete "{modal.task.prompt}"? This will permanently delete the task, workflow, dataset, records, and sources.
            </p>
            <div className="flex items-center justify-end gap-3">
              <Button variant="ghost" size="sm" onClick={() => setModal({ type: null, task: null })}>Cancel</Button>
              <Button
                variant="danger"
                size="sm"
                loading={isDeleting}
                onClick={handleDeleteTask}
              >
                Delete
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryPage;
