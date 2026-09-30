import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, StatCard, TaskCard, ChartCard } from '@/components';
import { ArrowRight, Plus, Activity, Database, AlertCircle, RefreshCw, Layers, Globe } from 'lucide-react';
import { getTasks, getDatasets, getOverviewStats, getActivityTimeline } from '@/services/api';
import type { Task, Dataset, OverviewStats, ActivityPoint } from '@/services/api';


const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [activity, setActivity] = useState<ActivityPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [tasksRes, datasetsRes, overviewRes, activityRes] = await Promise.all([
        getTasks({ limit: 5 }),
        getDatasets({ limit: 5 }),
        getOverviewStats().catch(() => null),
        getActivityTimeline(7).catch(() => ({ data: [] })),
      ]);
      setTasks(tasksRes.items || []);
      setDatasets(datasetsRes.items || []);
      setOverview(overviewRes);
      setActivity(activityRes?.data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data from backend server.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const activeTasksCount = overview?.active_tasks ?? tasks.filter(t => t.status === 'pending' || t.status === 'running').length;
  const totalRecordsCount = overview?.total_records ?? datasets.reduce((sum, d) => sum + (d.record_count || 0), 0);
  const datasetCount = overview?.total_datasets ?? datasets.length;
  const totalSourcesCount = overview?.total_sources ?? 0;

  const dashboardKPIs = [
    {
      id: 'active-tasks',
      label: 'Active Tasks',
      value: activeTasksCount.toString(),
      icon: Activity,
      trend: activeTasksCount > 0 ? `${activeTasksCount} in progress` : 'All tasks completed',
      trendDirection: activeTasksCount > 0 ? 'up' : 'neutral',
    },
    {
      id: 'records-collected',
      label: 'Records Collected',
      value: totalRecordsCount.toLocaleString(),
      icon: Database,
      trend: 'Across all datasets',
      trendDirection: 'up',
    },
    {
      id: 'datasets-count',
      label: 'Datasets',
      value: datasetCount.toString(),
      icon: Layers,
      trend: `${datasetCount} available`,
      trendDirection: 'up',
    },
    {
      id: 'sources-count',
      label: 'Sources Discovered',
      value: totalSourcesCount.toString(),
      icon: Globe,
      trend: 'Crawled & extracted',
      trendDirection: 'neutral',
    },
  ];

  const activityChartData = activity.length > 0
    ? activity.map(item => ({ time: item.date, records: item.records }))
    : [
        { time: '00:00', records: 0 },
        { time: '04:00', records: 0 },
        { time: '08:00', records: 0 },
      ];

  return (
    <div className="space-y-8 animate-fade-in pb-8 w-full max-w-full min-w-0">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-dp-text tracking-tight">
            Dashboard
          </h2>
          <p className="text-sm text-dp-text-secondary mt-1">
            Overview of active research tasks, datasets, and data collection metrics.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" icon={<RefreshCw className="w-4 h-4" />} onClick={fetchData} loading={isLoading}>
            Refresh
          </Button>
          <Button icon={<Plus className="w-4 h-4" />} onClick={() => navigate('/new-task')}>
            New Task
          </Button>
        </div>
      </div>

      {/* ── Error Banner ── */}
      {error && (
        <Card variant="bordered" padding="md" className="border-dp-error/40 bg-dp-error/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-dp-error shrink-0" />
              <div>
                <h4 className="font-semibold text-dp-text text-sm">Unable to load dashboard data</h4>
                <p className="text-xs text-dp-text-secondary mt-0.5">{error}</p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={fetchData}>Retry</Button>
          </div>
        </Card>
      )}

      {/* ── KPIs ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full min-w-0">
        {dashboardKPIs.map((kpi) => (
          <StatCard
            key={kpi.id}
            label={kpi.label}
            value={isLoading ? '...' : kpi.value}
            icon={kpi.icon}
            trend={kpi.trend}
            trendDirection={kpi.trendDirection as any}
          />
        ))}
      </div>

      {/* ── Main Dashboard Content ── */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 min-w-0">
        
        {/* Left Column (Chart & Datasets) */}
        <div className="xl:col-span-2 space-y-6 min-w-0">
          {/* Chart */}
          <ChartCard
            title="Data Collection Activity"
            description="Records collected over time"
            data={activityChartData}
            dataKey="records"
            xAxisKey="time"
          />

          {/* Recent Datasets */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-dp-text">Recent Datasets</h3>
              <Button variant="ghost" size="sm" icon={<ArrowRight className="w-4 h-4" />} iconPosition="right" onClick={() => navigate('/datasets')}>
                View All
              </Button>
            </div>
            
            <Card variant="bordered" padding="none" className="overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                  <thead className="bg-dp-bg-surface text-dp-text-muted text-xs uppercase border-b border-dp-border">
                    <tr>
                      <th className="px-6 py-3 font-medium">Dataset Name</th>
                      <th className="px-6 py-3 font-medium">Fields</th>
                      <th className="px-6 py-3 font-medium">Records</th>
                      <th className="px-6 py-3 font-medium">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-dp-border">
                    {isLoading ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-8 text-center text-dp-text-muted">Loading datasets...</td>
                      </tr>
                    ) : datasets.length > 0 ? (
                      datasets.slice(0, 5).map((dataset) => (
                        <tr
                          key={dataset.id}
                          className="hover:bg-dp-bg-hover/50 transition-colors cursor-pointer"
                          onClick={() => navigate(`/datasets/${dataset.id}`)}
                        >
                          <td className="px-6 py-4 font-medium text-dp-text whitespace-nowrap">
                            {dataset.name}
                          </td>
                          <td className="px-6 py-4 text-dp-text-secondary whitespace-nowrap">
                            {dataset.schema ? dataset.schema.map(f => f.name).join(', ') : 'Dynamic'}
                          </td>
                          <td className="px-6 py-4 text-dp-text-secondary whitespace-nowrap">
                            {(dataset.record_count || 0).toLocaleString()}
                          </td>
                          <td className="px-6 py-4 text-dp-text-muted whitespace-nowrap">
                            {new Date(dataset.created_at).toLocaleDateString()}
                          </td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan={4} className="px-6 py-8 text-center text-dp-text-muted">
                          No datasets created yet. Create a new task to generate a dataset.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>

        {/* Right Column (Recent Tasks) */}
        <div className="space-y-4 min-w-0">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-dp-text">Recent Tasks</h3>
            <Button variant="ghost" size="sm" icon={<ArrowRight className="w-4 h-4" />} iconPosition="right" onClick={() => navigate('/history')}>
              View All
            </Button>
          </div>
          
          <div className="flex flex-col gap-4">
            {isLoading ? (
              <Card padding="md" variant="bordered" className="text-center text-dp-text-muted py-8">
                Loading tasks...
              </Card>
            ) : tasks.length > 0 ? (
              tasks.slice(0, 5).map((task) => (
                <div
                  key={task.id}
                  onClick={() => navigate(`/workflow/${task.id}`)}
                  className="cursor-pointer"
                >
                  <TaskCard
                    title={task.prompt}
                    status={task.status.charAt(0).toUpperCase() + task.status.slice(1)}
                    records={task.record_count}
                    sources={null}
                    progress={task.progress}
                  />
                </div>
              ))
            ) : (
              <Card padding="md" variant="bordered" className="text-center text-dp-text-muted py-8">
                No tasks available. Click "New Task" to create your first workflow.
              </Card>
            )}
          </div>
        </div>
        
      </div>
    </div>
  );
};

export default DashboardPage;
