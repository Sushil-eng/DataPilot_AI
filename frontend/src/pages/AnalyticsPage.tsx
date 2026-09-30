import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import { Database, Layers, Globe, CheckCircle, RefreshCw, Copy } from 'lucide-react';
import { Card, CardHeader, CardContent, StatCard, Button, Select } from '@/components';
import { getDatasets, getOverviewStats, getActivityTimeline, getDatasetAnalytics } from '@/services/api';
import type { Dataset, OverviewStats, ActivityPoint, DatasetAnalytics, FieldStatistic } from '@/services/api';

export const CHART_COLORS = ['#f97316', '#3b82f6', '#10b981', '#a855f7', '#ec4899', '#eab308', '#06b6d4', '#6366f1'];

const AnalyticsPage: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('all');
  const [overview, setOverview] = useState<OverviewStats | null>(null);
  const [activity, setActivity] = useState<ActivityPoint[]>([]);
  const [datasetAnalytics, setDatasetAnalytics] = useState<DatasetAnalytics | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initial load: Datasets, overview stats, activity timeline
  const loadInitialData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [datasetsRes, overviewRes, activityRes] = await Promise.all([
        getDatasets({ limit: 100 }).catch(() => ({ items: [] })),
        getOverviewStats().catch(() => null),
        getActivityTimeline(14).catch(() => ({ data: [] })),
      ]);
      setDatasets(datasetsRes.items || []);
      setOverview(overviewRes);
      setActivity(activityRes?.data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // When selected dataset changes
  useEffect(() => {
    if (selectedDatasetId === 'all') {
      setDatasetAnalytics(null);
      return;
    }

    const fetchDatasetAnalytics = async () => {
      setIsLoading(true);
      try {
        const data = await getDatasetAnalytics(selectedDatasetId);
        setDatasetAnalytics(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dataset analytics.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchDatasetAnalytics();
  }, [selectedDatasetId]);

  const datasetOptions = [
    { value: 'all', label: 'All Datasets (Platform Wide)' },
    ...datasets.map(d => ({ value: d.id, label: d.name })),
  ];

  return (
    <div className="space-y-8 animate-fade-in pb-12 min-w-0">
      {/* ── Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl sm:text-3xl font-bold text-dp-text tracking-tight">
            Data Analytics
          </h2>
          <p className="text-base text-dp-text-secondary mt-1">
            Generic, schema-driven analytics and statistical insights across collected datasets.
          </p>
          {error && <p className="text-xs text-dp-error mt-1">{error}</p>}
        </div>

        <div className="flex items-center gap-3">
          <div className="w-64">
            <Select
              value={selectedDatasetId}
              onChange={(e) => setSelectedDatasetId(e.target.value)}
            >
              {datasetOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>
          </div>
          <Button
            variant="outline"
            icon={<RefreshCw className="w-4 h-4" />}
            onClick={() => {
              if (selectedDatasetId === 'all') loadInitialData();
              else setSelectedDatasetId(selectedDatasetId);
            }}
            loading={isLoading}
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* ── KPIs (Platform vs Dataset) ── */}
      {selectedDatasetId === 'all' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full min-w-0">
          <StatCard
            label="Total Records"
            value={overview ? overview.total_records.toLocaleString() : '0'}
            icon={Database}
            trend="Across all datasets"
            trendDirection="up"
          />
          <StatCard
            label="Total Datasets"
            value={overview ? overview.total_datasets.toString() : '0'}
            icon={Layers}
            trend="Active schemas"
            trendDirection="neutral"
          />
          <StatCard
            label="Total Sources"
            value={overview ? overview.total_sources.toString() : '0'}
            icon={Globe}
            trend="Web endpoints crawled"
            trendDirection="neutral"
          />
          <StatCard
            label="Tasks Completed"
            value={overview ? `${overview.completed_tasks} / ${overview.total_tasks}` : '0'}
            icon={CheckCircle}
            trend="AI Workflows executed"
            trendDirection="up"
          />
        </div>
      ) : datasetAnalytics ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total Records"
            value={datasetAnalytics.record_count.toLocaleString()}
            icon={Database}
            trend={`${datasetAnalytics.valid_records} valid`}
            trendDirection="up"
          />
          <StatCard
            label="Schema Fields"
            value={datasetAnalytics.field_count.toString()}
            icon={Layers}
            trend="Dynamic attributes"
            trendDirection="neutral"
          />
          <StatCard
            label="Data Sources"
            value={datasetAnalytics.source_count.toString()}
            icon={Globe}
            trend="Unique URLs/domains"
            trendDirection="neutral"
          />
          <StatCard
            label="Duplicates Removed"
            value={datasetAnalytics.duplicates_removed.toString()}
            icon={Copy}
            trend="Deduplicated"
            trendDirection="neutral"
          />
        </div>
      ) : null}

      {/* ── Activity Timeline Chart (Always visible or platform wide) ── */}
      <Card variant="bordered" padding="md">
        <CardHeader
          title={selectedDatasetId === 'all' ? "Platform Record Activity (14 Days)" : `Data Collection Activity — ${datasetAnalytics?.dataset_name || 'Dataset'}`}
          description="Timeline of data records extracted and processed"
          className="mb-4"
        />
        <CardContent className="h-[300px]">
          {activity.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={activity} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gradCollection" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-dp-accent)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--color-dp-accent)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--color-dp-border)" vertical={false} />
                <XAxis dataKey="date" stroke="var(--color-dp-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--color-dp-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip contentStyle={{ backgroundColor: 'var(--color-dp-bg-raised)', border: '1px solid var(--color-dp-border)', borderRadius: '8px', color: 'var(--color-dp-text)' }} />
                <Area type="monotone" dataKey="records" stroke="var(--color-dp-accent)" strokeWidth={2} fillOpacity={1} fill="url(#gradCollection)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full text-dp-text-muted text-sm">
              No activity timeline data recorded yet. Run tasks to see live activity.
            </div>
          )}
        </CardContent>
      </Card>

      {/* ── Generic Schema & Field Statistics (when Dataset Selected or Platform Wide Datasets Summary) ── */}
      {selectedDatasetId !== 'all' && datasetAnalytics ? (
        <div className="space-y-6">
          <h3 className="text-xl font-bold text-dp-text tracking-tight">
            Field Statistics & Data Distributions
          </h3>

          {/* Render dynamic charts for fields */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {datasetAnalytics.field_statistics.map((fieldStat: FieldStatistic) => {
              // Bar chart for top categorical values
              if ((fieldStat.chart_type === 'bar' || fieldStat.chart_type === 'pie') && fieldStat.top_values && fieldStat.top_values.length > 0) {
                return (
                  <Card key={fieldStat.field_name} variant="bordered" padding="md">
                    <CardHeader
                      title={`Field: ${fieldStat.field_name}`}
                      description={`Top value distribution (${fieldStat.unique_count || fieldStat.top_values.length} unique values, ${fieldStat.non_null_count} filled)`}
                      className="mb-4"
                    />
                    <CardContent className="h-[280px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={fieldStat.top_values} margin={{ top: 5, right: 10, left: -10, bottom: 25 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-dp-border)" vertical={false} />
                          <XAxis
                            dataKey="value"
                            stroke="var(--color-dp-text-muted)"
                            fontSize={11}
                            tickLine={false}
                            axisLine={false}
                            interval={0}
                            angle={-20}
                            textAnchor="end"
                          />
                          <YAxis stroke="var(--color-dp-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                          <Tooltip contentStyle={{ backgroundColor: 'var(--color-dp-bg-raised)', border: '1px solid var(--color-dp-border)', borderRadius: '8px', color: 'var(--color-dp-text)' }} />
                          <Bar dataKey="count" fill="var(--color-dp-accent)" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                );
              }

              // Stat Card for Numeric stats
              if (fieldStat.chart_type === 'numeric' && (fieldStat.minimum !== null || fieldStat.average !== null)) {
                return (
                  <Card key={fieldStat.field_name} variant="bordered" padding="md">
                    <CardHeader
                      title={`Field: ${fieldStat.field_name}`}
                      description={`Numeric metrics summary (${fieldStat.non_null_count} data points)`}
                      className="mb-4"
                    />
                    <CardContent className="grid grid-cols-3 gap-4 pt-4">
                      <div className="p-4 rounded-lg bg-dp-bg-surface border border-dp-border text-center">
                        <p className="text-xs text-dp-text-muted font-medium">Minimum</p>
                        <p className="text-xl font-bold text-dp-text mt-1">{fieldStat.minimum ?? 'N/A'}</p>
                      </div>
                      <div className="p-4 rounded-lg bg-dp-bg-surface border border-dp-border text-center">
                        <p className="text-xs text-dp-text-muted font-medium">Average</p>
                        <p className="text-xl font-bold text-dp-accent mt-1">{fieldStat.average ? fieldStat.average.toFixed(2) : 'N/A'}</p>
                      </div>
                      <div className="p-4 rounded-lg bg-dp-bg-surface border border-dp-border text-center">
                        <p className="text-xs text-dp-text-muted font-medium">Maximum</p>
                        <p className="text-xl font-bold text-dp-text mt-1">{fieldStat.maximum ?? 'N/A'}</p>
                      </div>
                    </CardContent>
                  </Card>
                );
              }

              return null;
            })}

            {/* Source Distribution Chart */}
            {datasetAnalytics.source_statistics && datasetAnalytics.source_statistics.length > 0 && (
              <Card variant="bordered" padding="md">
                <CardHeader
                  title="Source Distribution"
                  description="Where data originated for this dataset"
                  className="mb-4"
                />
                <CardContent className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={datasetAnalytics.source_statistics} layout="vertical" margin={{ top: 5, right: 20, left: 20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-dp-border)" horizontal={false} />
                      <XAxis type="number" stroke="var(--color-dp-text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                      <YAxis type="category" dataKey="domain" stroke="var(--color-dp-text-muted)" fontSize={12} tickLine={false} axisLine={false} width={120} />
                      <Tooltip contentStyle={{ backgroundColor: 'var(--color-dp-bg-raised)', border: '1px solid var(--color-dp-border)', borderRadius: '8px', color: 'var(--color-dp-text)' }} />
                      <Bar dataKey="count" fill="var(--color-dp-accent)" radius={[0, 4, 4, 0]} barSize={20} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      ) : (
        /* Platform wide view — Datasets Overview Table & Summary */
        <Card variant="bordered" padding="md">
          <CardHeader
            title="Datasets Summary"
            description="Overview of schema fields and records across all dynamic datasets"
            className="mb-4"
          />
          <CardContent className="p-0 overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-dp-bg-surface text-dp-text-muted text-xs uppercase border-b border-dp-border">
                <tr>
                  <th className="px-6 py-3 font-medium">Dataset Name</th>
                  <th className="px-6 py-3 font-medium">Fields</th>
                  <th className="px-6 py-3 font-medium">Records</th>
                  <th className="px-6 py-3 font-medium">Created Date</th>
                  <th className="px-6 py-3 font-medium text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-dp-border">
                {datasets.length > 0 ? (
                  datasets.map((d) => (
                    <tr key={d.id} className="hover:bg-dp-bg-hover/50 transition-colors">
                      <td className="px-6 py-4 font-medium text-dp-text whitespace-nowrap">
                        {d.name}
                      </td>
                      <td className="px-6 py-4 text-dp-text-secondary whitespace-nowrap">
                        {d.schema ? d.schema.length : (d.dynamic_schema?.fields?.length || 0)} fields
                      </td>
                      <td className="px-6 py-4 text-dp-text-secondary whitespace-nowrap">
                        {(d.record_count || 0).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-dp-text-muted whitespace-nowrap">
                        {new Date(d.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Button variant="ghost" size="sm" onClick={() => setSelectedDatasetId(d.id)}>
                          View Analytics
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-dp-text-muted">
                      No datasets available yet. Create a workflow to generate dataset analytics.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default AnalyticsPage;
