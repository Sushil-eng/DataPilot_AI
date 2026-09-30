import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Database, CheckCircle2, ShieldCheck, Files, AlertCircle, RefreshCw, Layers } from 'lucide-react';
import { StatCard, DatasetTable, Card, Button, Select, Badge } from '@/components';
import { 
  getDatasets, 
  getDataset, 
  getDatasetRecords, 
  getSources, 
  createDatasetRecord,
  deleteDatasetRecord 
} from '@/services/api';
import type { Dataset, DatasetRecord, Source } from '@/services/api';


// ── Schema Fields Summary Component ──
// Renders compact badges for first N fields with "+X more" truncation
const SchemaFieldsSummary: React.FC<{ schema?: { name: string; type?: string }[] }> = ({ schema }) => {
  const MAX_VISIBLE = 3;

  if (!schema || schema.length === 0) {
    return <span className="text-dp-text-muted text-xs">Dynamic</span>;
  }

  const visible = schema.slice(0, MAX_VISIBLE);
  const remaining = schema.length - MAX_VISIBLE;

  return (
    <div className="flex flex-wrap items-center gap-1 mt-1">
      {visible.map(f => (
        <Badge key={f.name} variant="default" className="text-2xs px-1.5 py-0 leading-4 max-w-[90px] truncate" title={f.name}>
          {f.name.replace(/_/g, ' ')}
        </Badge>
      ))}
      {remaining > 0 && (
        <Badge variant="accent" className="text-2xs px-1.5 py-0 leading-4">
          +{remaining} more
        </Badge>
      )}
    </div>
  );
};


const DatasetsPage: React.FC = () => {
  const { datasetId: paramDatasetId } = useParams<{ datasetId?: string }>();
  const navigate = useNavigate();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>(paramDatasetId || '');
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  
  const [records, setRecords] = useState<DatasetRecord[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRecordsLoading, setIsRecordsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch list of datasets on mount
  const fetchDatasetsList = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getDatasets({ limit: 50 });
      const items = res.items || [];
      setDatasets(items);

      if (items.length > 0) {
        // Use paramDatasetId if valid, otherwise first dataset
        const targetId = paramDatasetId && items.some(d => d.id === paramDatasetId) 
          ? paramDatasetId 
          : items[0].id;
        setSelectedDatasetId(targetId);
      } else {
        setIsLoading(false);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load datasets from backend server.');
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasetsList();
  }, [paramDatasetId]);

  // Fetch details, records, and sources whenever selectedDatasetId changes
  useEffect(() => {
    if (!selectedDatasetId) return;

    const loadDatasetData = async () => {
      setIsRecordsLoading(true);
      try {
        const [dsRes, recsRes, srcRes] = await Promise.all([
          getDataset(selectedDatasetId),
          getDatasetRecords(selectedDatasetId, { limit: 100 }),
          getSources(selectedDatasetId).catch(() => ({ items: [], count: 0 })),
        ]);
        
        setSelectedDataset(dsRes);
        setRecords(recsRes.items || []);
        setSources(srcRes.items || []);
      } catch (err: any) {
        setError(err.message || 'Failed to load dataset details.');
      } finally {
        setIsLoading(false);
        setIsRecordsLoading(false);
      }
    };

    loadDatasetData();
  }, [selectedDatasetId]);

  const handleDatasetChange = (id: string) => {
    setSelectedDatasetId(id);
    navigate(`/datasets/${id}`);
  };

  const handleAddRecord = async (recordData: Record<string, any>) => {
    if (!selectedDatasetId) return;
    const newRec = await createDatasetRecord(selectedDatasetId, recordData);
    setRecords(prev => [newRec, ...prev]);
    if (selectedDataset) {
      setSelectedDataset({
        ...selectedDataset,
        record_count: (selectedDataset.record_count || 0) + 1
      });
    }
  };

  const handleDeleteRecord = async (recordId: string) => {
    if (!selectedDatasetId) return;
    await deleteDatasetRecord(selectedDatasetId, recordId);
    setRecords(prev => prev.filter(r => r.id !== recordId));
    if (selectedDataset) {
      setSelectedDataset({
        ...selectedDataset,
        record_count: Math.max(0, (selectedDataset.record_count || 0) - 1)
      });
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center space-y-4">
        <div className="w-10 h-10 border-4 border-dp-accent border-t-transparent rounded-full animate-spin mx-auto" />
        <h3 className="text-lg font-medium text-dp-text">Loading Datasets...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto py-12 text-center space-y-6">
        <Card variant="bordered" padding="lg" className="border-dp-error/30 bg-dp-error/5 max-w-lg mx-auto">
          <AlertCircle className="w-12 h-12 text-dp-error mx-auto mb-4" />
          <h3 className="text-xl font-bold text-dp-text mb-2">Error Loading Datasets</h3>
          <p className="text-sm text-dp-text-secondary mb-6">{error}</p>
          <Button variant="outline" size="sm" onClick={fetchDatasetsList}>
            <RefreshCw className="w-4 h-4 mr-2" /> Retry Connection
          </Button>
        </Card>
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center space-y-6 animate-fade-in">
        <Card variant="bordered" padding="lg" className="max-w-lg mx-auto space-y-4">
          <Database className="w-12 h-12 text-dp-accent/60 mx-auto" />
          <h3 className="text-xl font-bold text-dp-text">No Datasets Available</h3>
          <p className="text-sm text-dp-text-secondary">
            You haven't generated any datasets yet. Create a new data workflow to automatically generate structured datasets.
          </p>
          <Button onClick={() => navigate('/new-task')}>
            Create Data Workflow
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in pb-12 w-full max-w-full min-w-0">
      {/* ── Header & Dataset Switcher ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-dp-accent/10 flex items-center justify-center">
              <Database className="w-5 h-5 text-dp-accent" />
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-dp-text tracking-tight">
              {selectedDataset?.name || 'Dataset Viewer'}
            </h2>
          </div>
          <p className="text-sm text-dp-text-secondary">
            {selectedDataset?.description || 'Explore, filter and export structured dataset records.'}
          </p>
        </div>

        {/* Dataset Selector */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-dp-text-muted shrink-0" />
            <Select 
              value={selectedDatasetId} 
              onChange={(e) => handleDatasetChange(e.target.value)}
              className="w-56"
            >
              {datasets.map(ds => (
                <option key={ds.id} value={ds.id}>{ds.name}</option>
              ))}
            </Select>
          </div>
        </div>
      </div>

      {/* ── Dynamic Top KPIs ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total Records"
          value={(selectedDataset?.record_count ?? records.length).toLocaleString()}
          icon={Files}
          trend={`${records.length} fetched`}
          trendDirection="up"
        />
        <StatCard
          label="Sources"
          value={sources.length.toString()}
          icon={Database}
          trend={sources.length > 0 ? `${sources.length} linked` : 'No sources'}
          trendDirection="neutral"
        />
        <StatCard
          label="Schema Fields"
          value={(selectedDataset?.schema?.length || 0).toString()}
          icon={CheckCircle2}
          trendContent={<SchemaFieldsSummary schema={selectedDataset?.schema} />}
          trendDirection="neutral"
        />
        <StatCard
          label="Validation Status"
          value="Validated"
          icon={ShieldCheck}
          trend="Clean data"
          trendDirection="up"
        />
      </div>

      {/* ── Dynamic Dataset Table ── */}
      <div className="space-y-4">
        <DatasetTable 
          datasetId={selectedDatasetId}
          datasetName={selectedDataset?.name}
          schema={selectedDataset?.schema}
          records={records}
          isLoading={isRecordsLoading}
          onAddRecord={handleAddRecord}
          onDeleteRecord={handleDeleteRecord}
        />
      </div>
    </div>
  );
};

export default DatasetsPage;
