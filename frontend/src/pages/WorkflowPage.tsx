import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { 
  CheckCircle2, 
  Loader2, 
  AlertCircle,
  ArrowRight,
  RefreshCw,
  XCircle,
  Sparkles,
  Filter,
  FileText,
  Target,
  Layers,
  AlertTriangle,
  FileDown,
  Database,
  Check
} from 'lucide-react';
import { Card, Button, StatusBadge } from '@/components';
import { DatasetTable } from '@/components/DatasetTable';
import { cn } from '@/utils/cn';
import { 
  getWorkflow, 
  getTask, 
  getTasks,
  getDatasets, 
  getSources, 
  getDatasetRecords,
  downloadDatasetExport 
} from '@/services/api';
import type { Task, Workflow, Dataset, Source, AIRequirements, DatasetRecord } from '@/services/api';

// Helper to capitalize intent strings (e.g. job_search -> Job Search)
const formatIntentLabel = (intent?: string): string => {
  if (!intent) return 'Data Collection';
  return intent
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
};

// Helper to format field names nicely
const formatFieldName = (name: string): string => {
  return name
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
};

/**
 * Calculates adaptive polling interval (in milliseconds) based on the current step and workflow metadata.
 * 
 * Rules:
 * - Data Search: 20 seconds (20000ms)
 * - Source Discovery: 15 seconds (15000ms)
 * - Data Extraction: 10 seconds (10000ms)
 * - Data Normalisation: 7 seconds (7000ms)
 * - Filter Application: 5 seconds (5000ms)
 * - Data Validation: 5 seconds (5000ms)
 * - Deduplication: 5 seconds (5000ms)
 * - Source Attachment: 5 seconds (5000ms)
 * - Dataset Storage: 5 seconds (5000ms)
 * - Groq / AI response generation: 4 seconds (4000ms)
 * - Generic running / unknown step: 10 seconds (10000ms)
 */
export const getAdaptivePollingInterval = (
  currentStep?: string,
  runningStep?: { id?: string; name?: string; tool?: string } | null
): number => {
  const tokens = [
    currentStep || '',
    runningStep?.id || '',
    runningStep?.name || '',
    runningStep?.tool || ''
  ].join(' ').toLowerCase();

  if (tokens.includes('source_discovery') || (tokens.includes('source') && (tokens.includes('discov') || tokens.includes('ident')))) {
    return 15000;
  }
  if (tokens.includes('search')) {
    return 20000;
  }
  if (tokens.includes('extract')) {
    return 10000;
  }
  if (tokens.includes('normalis') || tokens.includes('normaliz')) {
    return 7000;
  }
  if (tokens.includes('groq') || tokens.includes('llm') || tokens.includes('ai_generation') || tokens.includes('ai_fallback') || tokens.includes('fallback')) {
    return 4000;
  }
  if (tokens.includes('filter')) {
    return 5000;
  }
  if (tokens.includes('validat')) {
    return 5000;
  }
  if (tokens.includes('deduplicat')) {
    return 5000;
  }
  if (tokens.includes('source_attach') || (tokens.includes('attach') && tokens.includes('source'))) {
    return 5000;
  }
  if (tokens.includes('stor') || tokens.includes('dataset_stor')) {
    return 5000;
  }

  return 10000;
};

const WorkflowPage: React.FC = () => {
  const navigate = useNavigate();
  const params = useParams<{ taskId?: string }>();
  const [searchParams] = useSearchParams();
  const taskId = params.taskId || searchParams.get('taskId');

  const [task, setTask] = useState<Task | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [records, setRecords] = useState<DatasetRecord[]>([]);
  
  const [isLoading, setIsLoading] = useState(true);
  const [isManualRefreshing, setIsManualRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState<'csv' | 'json' | null>(null);

  // Polling management refs
  const timerRef = useRef<any>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const activeTaskIdRef = useRef<string | null>(null);
  const consecutiveErrorsRef = useRef<number>(0);

  /**
   * Fetches the latest workflow state from backend API.
   * Returns fresh Task and Workflow objects, or error info.
   */
  const fetchWorkflowState = async (
    targetTaskId: string,
    isSilentPoll: boolean = false
  ): Promise<{ task: Task; workflow: Workflow } | { error: any; isTerminalError: boolean } | null> => {
    // Abort previous in-flight request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const [wfRes, taskRes] = await Promise.all([
        getWorkflow(targetTaskId, { signal: controller.signal }),
        getTask(targetTaskId, { signal: controller.signal }),
      ]);

      // If task changed while in flight, discard response
      if (activeTaskIdRef.current !== targetTaskId) {
        return null;
      }

      consecutiveErrorsRef.current = 0;
      setWorkflow(wfRes);
      setTask(taskRes);

      // If dataset exists or task completed, fetch dataset details, sources and preview records
      const shouldFetchDataset = taskRes.status === 'completed' || wfRes.status === 'completed' || taskRes.dataset_id;
      if (shouldFetchDataset) {
        try {
          const dsRes = await getDatasets({ task_id: targetTaskId }, { signal: controller.signal });
          if (dsRes.items && dsRes.items.length > 0) {
            const ds = dsRes.items[0];
            setDataset(ds);

            // If task is completed, retrieve collected records
            if (taskRes.status === 'completed' || wfRes.status === 'completed') {
              try {
                const recRes = await getDatasetRecords(ds.id, { limit: 50 }, { signal: controller.signal });
                setRecords(recRes.items || []);
              } catch {
                // Ignore non-fatal record preview fetch error
              }
            }

            // Fetch provenance sources
            try {
              const srcRes = await getSources(ds.id, { signal: controller.signal });
              setSources(srcRes.items || []);
            } catch {
              setSources([]);
            }
          }
        } catch {
          // Ignore non-fatal dataset query error
        }
      }

      setError(null);
      return { task: taskRes, workflow: wfRes };
    } catch (err: any) {
      if (err.name === 'AbortError' || controller.signal.aborted) {
        return null;
      }

      const errMsg = err.message || '';
      const is404 = errMsg.toLowerCase().includes('404') || errMsg.toLowerCase().includes('not found');
      const is401 = errMsg.toLowerCase().includes('401') || errMsg.toLowerCase().includes('unauthorized');

      if (!isSilentPoll) {
        setError(errMsg || 'Failed to load workflow data.');
      }

      return { error: err, isTerminalError: is404 || is401 };
    }
  };

  /**
   * Schedules the next polling execution with an adaptive delay.
   */
  const scheduleNextPoll = (targetTaskId: string, delayMs: number) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    timerRef.current = setTimeout(() => {
      runAdaptivePollCycle(targetTaskId);
    }, delayMs);
  };

  /**
   * Runs a single polling cycle, updates state, and schedules the next cycle adaptively.
   */
  const runAdaptivePollCycle = async (targetTaskId: string) => {
    if (activeTaskIdRef.current !== targetTaskId) return;

    const result = await fetchWorkflowState(targetTaskId, true);
    if (!result) return; // Discarded or aborted

    if ('error' in result) {
      if (result.isTerminalError) {
        // Stop polling on 404/401
        setError(result.error.message || 'Workflow could not be retrieved.');
        return;
      }

      // Exponential backoff for network or transient 500 errors
      consecutiveErrorsRef.current += 1;
      if (consecutiveErrorsRef.current >= 5) {
        setError('Lost connection to backend server after repeated retries.');
        return;
      }

      const backoffDelay = Math.min(30000, 5000 * Math.pow(1.5, consecutiveErrorsRef.current - 1));
      if (activeTaskIdRef.current === targetTaskId) {
        scheduleNextPoll(targetTaskId, backoffDelay);
      }
      return;
    }

    const { task: currentTask, workflow: currentWf } = result;

    const isTerminal = 
      currentTask.status === 'completed' || 
      currentTask.status === 'failed' || 
      currentTask.status === 'cancelled' ||
      currentWf.status === 'completed' || 
      currentWf.status === 'failed';

    if (isTerminal) {
      // Terminal state reached: poller stops completely
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      return;
    }

    // Determine running step for adaptive interval calculation
    const runningStep = currentWf.steps?.find(s => s.status === 'running') || null;
    const adaptiveInterval = getAdaptivePollingInterval(
      currentTask.current_step || currentWf.current_step,
      runningStep
    );

    if (activeTaskIdRef.current === targetTaskId) {
      scheduleNextPoll(targetTaskId, adaptiveInterval);
    }
  };

  /**
   * Triggers an immediate manual refresh without waiting for the polling timer.
   */
  const handleManualRefresh = async () => {
    const activeId = activeTaskIdRef.current || task?.id || taskId;
    if (!activeId) return;

    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }

    setIsManualRefreshing(true);
    const result = await fetchWorkflowState(activeId, true);
    setIsManualRefreshing(false);

    if (result && !('error' in result)) {
      const { task: freshTask, workflow: freshWf } = result;
      const isTerminal = 
        freshTask.status === 'completed' || 
        freshTask.status === 'failed' || 
        freshTask.status === 'cancelled' ||
        freshWf.status === 'completed' || 
        freshWf.status === 'failed';

      if (!isTerminal && activeTaskIdRef.current === activeId) {
        const runningStep = freshWf.steps?.find(s => s.status === 'running') || null;
        const interval = getAdaptivePollingInterval(
          freshTask.current_step || freshWf.current_step,
          runningStep
        );
        scheduleNextPoll(activeId, interval);
      }
    }
  };

  // Main lifecycle: Initialize poller on mount / taskId change, clean up on unmount
  useEffect(() => {
    const activeId = taskId;

    if (!activeId) {
      setIsLoading(true);
      getTasks({ limit: 1 })
        .then(res => {
          if (res.items && res.items.length > 0) {
            navigate(`/workflow/${res.items[0].id}`, { replace: true });
          } else {
            setIsLoading(false);
            setError("No workflows available. Please create a new task first.");
          }
        })
        .catch((err: any) => {
          setIsLoading(false);
          setError(err.message || "Failed to fetch workflows.");
        });
      return;
    }

    activeTaskIdRef.current = activeId;
    consecutiveErrorsRef.current = 0;
    setIsLoading(true);

    fetchWorkflowState(activeId, false).then(result => {
      setIsLoading(false);
      if (result && !('error' in result)) {
        const { task: initialTask, workflow: initialWf } = result;
        const isTerminal = 
          initialTask.status === 'completed' || 
          initialTask.status === 'failed' || 
          initialTask.status === 'cancelled' ||
          initialWf.status === 'completed' || 
          initialWf.status === 'failed';

        if (!isTerminal && activeTaskIdRef.current === activeId) {
          const runningStep = initialWf.steps?.find(s => s.status === 'running') || null;
          const initialInterval = getAdaptivePollingInterval(
            initialTask.current_step || initialWf.current_step,
            runningStep
          );
          scheduleNextPoll(activeId, initialInterval);
        }
      }
    });

    return () => {
      activeTaskIdRef.current = null;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }
    };
  }, [taskId]);

  const handleExport = async (format: 'csv' | 'json') => {
    if (!dataset?.id) return;
    try {
      setIsExporting(format);
      await downloadDatasetExport(dataset.id, format, `${dataset.name || 'dataset'}.${format}`);
    } catch (err: any) {
      alert("Failed to export dataset: " + err.message);
    } finally {
      setIsExporting(null);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto py-20 text-center space-y-4">
        <Loader2 className="w-10 h-10 animate-spin text-dp-accent mx-auto" />
        <h3 className="text-lg font-semibold text-dp-text">Connecting to Live Workflow Engine...</h3>
        <p className="text-sm text-dp-text-secondary">Retrieving real-time task status and pipeline execution state...</p>
      </div>
    );
  }

  if (error || !workflow || !task) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center space-y-6">
        <Card variant="bordered" padding="lg" className="border-dp-error/30 bg-dp-error/5 max-w-lg mx-auto">
          <AlertCircle className="w-12 h-12 text-dp-error mx-auto mb-4" />
          <h3 className="text-xl font-bold text-dp-text mb-2">Workflow Not Found</h3>
          <p className="text-sm text-dp-text-secondary mb-6">{error || "The requested workflow could not be found."}</p>
          <div className="flex items-center justify-center gap-3">
            <Button variant="outline" size="sm" onClick={() => navigate('/history')}>
              View All Workflows
            </Button>
            <Button size="sm" onClick={() => navigate('/new-task')}>
              Create New Task
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  const aiReq: AIRequirements | undefined = task.ai_requirements;
  const rawSteps = workflow.steps || [];

  // Build full step list combining completed AI planning milestones + backend execution steps
  const displaySteps = [
    {
      id: 'plan_1',
      name: 'Understand Request & Intent',
      description: `Analyzed prompt requirements and identified research intent: ${formatIntentLabel(aiReq?.intent || workflow.intent)}.`,
      status: 'completed',
      message: undefined,
    },
    {
      id: 'plan_2',
      name: 'Dynamic Schema Generation',
      description: `Generated schema with ${dataset?.schema?.length || aiReq?.fields?.length || 0} custom fields.`,
      status: 'completed',
      message: undefined,
    },
    ...rawSteps.map((step, idx) => ({
      id: step.id || `exec_${idx}`,
      name: formatFieldName(step.name),
      description: step.description || `Tool: ${step.tool || 'process'}`,
      status: step.status || 'pending',
      message: step.message,
    }))
  ];

  const completedCount = displaySteps.filter(s => s.status === 'completed' || s.status === 'skipped' || s.status === 'fallback').length;
  const totalCount = displaySteps.length;
  const isComplete = task.status === 'completed' && workflow.status === 'completed';
  const progressPercent = isComplete ? 100 : (task.progress || workflow.progress || Math.round((completedCount / totalCount) * 100));
  const fallbackUsed = task.fallback_used || workflow.fallback_used || dataset?.fallback_used;

  return (
    <div className="max-w-6xl w-full mx-auto space-y-8 animate-fade-in pb-12 min-w-0">
      
      {/* ── Fallback Notice Banner ── */}
      {fallbackUsed && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 flex items-start gap-3 shadow-sm animate-fade-in">
          <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="text-sm font-semibold text-amber-200">AI Knowledge Fallback Activated</h4>
            <p className="text-xs text-amber-300/90 leading-relaxed">
              {task.fallback_notice || workflow.fallback_notice || "External web search provider returned HTTP 403 Forbidden or was unavailable. The dataset was generated using Groq AI Knowledge Fallback to complete your request without failing."}
            </p>
          </div>
        </div>
      )}

      {/* ── Header: User Request & Live Status ── */}
      <div className="space-y-4 bg-dp-bg-raised p-6 rounded-[var(--radius-card)] border border-dp-border">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-3 flex-wrap">
              <StatusBadge status={task.status === 'planned' ? 'Planned' : task.status === 'running' ? 'Running' : task.status === 'completed' ? 'Completed' : task.status.charAt(0).toUpperCase() + task.status.slice(1)} />
              <span className="text-sm text-dp-text-secondary font-mono">TASK-{task.id.slice(-6).toUpperCase()}</span>
              {aiReq?.confidence && (
                <span className="text-xs px-2 py-0.5 rounded bg-dp-accent/10 text-dp-accent font-medium">
                  AI Confidence: {Math.round(aiReq.confidence * 100)}%
                </span>
              )}
              {fallbackUsed && (
                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 font-medium border border-amber-500/30">
                  Fallback Mode
                </span>
              )}
            </div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-dp-text-muted uppercase tracking-wider">User Request</span>
                {sources.length > 0 && <span className="text-2xs font-mono text-dp-text-muted">({sources.length} sources tracked)</span>}
              </div>
              <h2 className="text-xl sm:text-2xl font-bold text-dp-text tracking-tight">
                "{task.prompt}"
              </h2>
            </div>
          </div>
          
          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            <Button 
              variant="outline"
              size="sm"
              icon={<RefreshCw className={`w-4 h-4 ${isManualRefreshing || task.status === 'running' ? 'animate-spin' : ''}`} />}
              onClick={handleManualRefresh}
              loading={isManualRefreshing}
            >
              Refresh
            </Button>
            {dataset && (
              <Button 
                onClick={() => navigate(`/datasets/${dataset.id}`)}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                View Full Dataset
              </Button>
            )}
          </div>
        </div>

        {/* Global Progress Bar */}
        <div className="space-y-2 pt-4 border-t border-dp-border">
          <div className="flex justify-between text-sm items-center">
            <div className="flex items-center gap-2">
              <span className="text-dp-text-secondary font-medium font-sans">Execution Progress</span>
              {task.current_message && (
                <span className="text-xs text-dp-text-muted font-mono truncate max-w-xs sm:max-w-md">
                  — {task.current_message}
                </span>
              )}
            </div>
            <span className="text-dp-accent font-bold font-mono">{progressPercent}%</span>
          </div>
          <div className="w-full bg-dp-bg-surface h-2.5 rounded-full overflow-hidden border border-white/5">
            <div 
              className="bg-gradient-to-r from-dp-accent to-orange-400 h-full rounded-full transition-all duration-500 ease-out relative overflow-hidden"
              style={{ width: `${progressPercent}%` }}
            >
              {task.status === 'running' && (
                <div className="absolute inset-0 bg-white/25 animate-pulse" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Completion Banner when 100% finished ── */}
      {isComplete && (
        <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-emerald-500/5 border border-emerald-500/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 animate-fade-in">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shrink-0">
              <Check className="w-6 h-6 text-emerald-400" />
            </div>
            <div>
              <h3 className="text-base font-bold text-dp-text">Dataset Ready ({task.record_count || records.length} Clean Records)</h3>
              <p className="text-xs text-dp-text-secondary">
                Workflow completed successfully. Data has been cleaned, validated, and persisted.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2.5 shrink-0">
            <Button
              variant="outline"
              size="sm"
              icon={<FileDown className="w-4 h-4" />}
              onClick={() => handleExport('csv')}
              loading={isExporting === 'csv'}
            >
              Export CSV
            </Button>
            <Button
              variant="outline"
              size="sm"
              icon={<FileDown className="w-4 h-4" />}
              onClick={() => handleExport('json')}
              loading={isExporting === 'json'}
            >
              Export JSON
            </Button>
            {dataset && (
              <Button
                size="sm"
                icon={<Database className="w-4 h-4" />}
                onClick={() => navigate(`/datasets/${dataset.id}`)}
                className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold"
              >
                Inspect Dataset
              </Button>
            )}
          </div>
        </div>
      )}

      {/* ── Main Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 min-w-0">
        
        {/* ── Left Column: Workflow Steps & Records Preview ── */}
        <div className="lg:col-span-2 space-y-8 min-w-0">
          
          {/* Workflow Steps Timeline */}
          <Card variant="bordered" padding="lg">
            <div className="flex items-center justify-between mb-6 pb-4 border-b border-dp-border">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-dp-accent" />
                <h3 className="text-lg font-semibold text-dp-text">Execution Steps</h3>
              </div>
              <span className="text-xs text-dp-text-muted bg-dp-bg-surface px-2.5 py-1 rounded-full border border-dp-border font-mono">
                {task.status === 'running' ? 'Active Execution' : task.status === 'completed' ? '100% Completed' : 'Workflow Prepared'}
              </span>
            </div>
            
            <div className="space-y-4">
              {displaySteps.map((step, idx) => {
                const isStepCompleted = step.status === 'completed';
                const isStepRunning = step.status === 'running';
                const isStepSkipped = step.status === 'skipped' || step.status === 'fallback';
                const isStepFailed = step.status === 'failed';
                const isStepPending = step.status === 'pending';
                
                return (
                  <div 
                    key={step.id} 
                    className={cn(
                      "p-4 rounded-xl border transition-all duration-300 flex items-start gap-4",
                      isStepRunning 
                        ? "bg-dp-accent/10 border-dp-accent/40 shadow-glow" 
                        : isStepCompleted 
                        ? "bg-dp-bg-surface/70 border-white/10" 
                        : isStepSkipped
                        ? "bg-amber-500/10 border-amber-500/30"
                        : isStepFailed
                        ? "bg-dp-error/10 border-dp-error/30"
                        : "bg-dp-bg-surface/30 border-white/5 opacity-60"
                    )}
                  >
                    {/* Status Icon */}
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-white font-bold text-xs mt-0.5",
                      isStepCompleted ? "bg-emerald-500 text-white" :
                      isStepRunning ? "bg-dp-accent text-white animate-pulse" :
                      isStepSkipped ? "bg-amber-500 text-white" :
                      isStepFailed ? "bg-rose-500 text-white" :
                      "bg-dp-bg-raised text-dp-text-muted border border-white/10"
                    )}>
                      {isStepCompleted && <CheckCircle2 className="w-4 h-4" />}
                      {isStepRunning && <Loader2 className="w-4 h-4 animate-spin" />}
                      {isStepSkipped && <AlertTriangle className="w-4 h-4" />}
                      {isStepFailed && <XCircle className="w-4 h-4" />}
                      {isStepPending && <span>{idx + 1}</span>}
                    </div>

                    {/* Step Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <h4 className={cn(
                          "text-sm font-bold",
                          isStepRunning ? "text-dp-accent font-semibold" :
                          isStepSkipped ? "text-amber-300" :
                          isStepCompleted ? "text-dp-text" :
                          "text-dp-text-secondary"
                        )}>
                          {step.name}
                        </h4>
                        <span className={cn(
                          "text-[10px] px-2 py-0.5 rounded font-mono uppercase tracking-wider font-semibold",
                          isStepCompleted ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20" :
                          isStepRunning ? "bg-dp-accent/20 text-dp-accent border border-dp-accent/30 animate-pulse" :
                          isStepSkipped ? "bg-amber-500/15 text-amber-400 border border-amber-500/30" :
                          isStepFailed ? "bg-rose-500/15 text-rose-400 border border-rose-500/30" :
                          "bg-white/5 text-dp-text-muted border border-white/5"
                        )}>
                          {isStepSkipped ? 'Skipped (Fallback)' : step.status}
                        </span>
                      </div>
                      
                      <p className="text-xs text-dp-text-secondary mt-1 leading-relaxed">
                        {step.description}
                      </p>

                      {step.message && (
                        <p className="text-[11px] font-mono text-amber-300/90 mt-1.5 bg-black/30 px-2.5 py-1 rounded border border-amber-500/20">
                          ℹ {step.message}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Records Preview Table (when available) */}
          {records.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-5 h-5 text-dp-accent" />
                  <h3 className="text-lg font-bold text-dp-text">Collected Records Preview</h3>
                </div>
                <span className="text-xs font-mono text-dp-text-muted">
                  Showing {records.length} records
                </span>
              </div>
              <DatasetTable
                datasetId={dataset?.id}
                datasetName={dataset?.name}
                schema={dataset?.schema}
                records={records}
              />
            </div>
          )}

          {/* Dynamic Dataset Schema Card */}
          <Card variant="bordered" padding="lg">
            <div className="flex items-center justify-between mb-4 border-b border-dp-border pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-dp-accent" />
                <h3 className="text-lg font-semibold text-dp-text">Dataset Schema</h3>
              </div>
              <span className="text-xs font-mono text-dp-text-secondary">
                {dataset?.schema?.length || aiReq?.fields?.length || 0} Dynamic Fields
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {(dataset?.schema || aiReq?.fields || []).map((field) => (
                <div key={field.name} className="p-3 bg-dp-bg-surface rounded-lg border border-dp-border flex flex-col justify-between space-y-1">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-mono font-bold text-dp-text">{field.name}</span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-dp-accent/10 text-dp-accent font-medium">
                      {field.type}
                    </span>
                  </div>
                  {field.description && (
                    <p className="text-[11px] text-dp-text-secondary leading-snug">{field.description}</p>
                  )}
                </div>
              ))}
            </div>
          </Card>
          
        </div>

        {/* ── Right Column: AI PLAN PANEL ── */}
        <div className="space-y-6">
          <Card variant="accent" padding="md" className="sticky top-24 space-y-6 border-dp-accent/30 shadow-lg">
            
            {/* Header */}
            <div className="flex items-center gap-2 border-b border-dp-border pb-4">
              <Sparkles className="w-5 h-5 text-dp-accent animate-pulse" />
              <h3 className="text-lg font-bold text-dp-text tracking-tight">AI Generated Plan</h3>
            </div>
            
            <div className="space-y-5">
              
              {/* Intent */}
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-dp-text-secondary uppercase tracking-wider">
                  <Target className="w-3.5 h-3.5 text-dp-accent" />
                  <span>Intent</span>
                </div>
                <div className="p-2.5 bg-dp-bg-surface rounded-md border border-dp-border text-sm font-semibold text-dp-text">
                  {formatIntentLabel(aiReq?.intent || workflow.intent)}
                </div>
              </div>

              {/* Goal */}
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-dp-text-secondary uppercase tracking-wider">
                  <FileText className="w-3.5 h-3.5 text-dp-accent" />
                  <span>Goal</span>
                </div>
                <p className="p-2.5 bg-dp-bg-surface rounded-md border border-dp-border text-xs text-dp-text leading-relaxed">
                  {aiReq?.goal || workflow.goal || task.prompt}
                </p>
              </div>

              {/* Filters */}
              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-xs font-semibold text-dp-text-secondary uppercase tracking-wider">
                  <Filter className="w-3.5 h-3.5 text-dp-accent" />
                  <span>Filters</span>
                </div>
                <div className="p-2.5 bg-dp-bg-surface rounded-md border border-dp-border space-y-1">
                  {aiReq?.filters && Object.keys(aiReq.filters).length > 0 ? (
                    Object.entries(aiReq.filters).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-xs">
                        <span className="text-dp-text-secondary capitalize">{k.replace(/_/g, ' ')}:</span>
                        <span className="font-semibold text-dp-text">{String(v)}</span>
                      </div>
                    ))
                  ) : (
                    <span className="text-xs text-dp-text-muted italic">No strict filters applied</span>
                  )}
                </div>
              </div>

              {/* Records Limit */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-dp-text-secondary uppercase tracking-wider">Records requested</span>
                  <span className="font-mono font-bold text-dp-accent bg-dp-accent/10 px-2 py-0.5 rounded text-xs">
                    {aiReq?.record_limit || task.record_limit || 50}
                  </span>
                </div>
              </div>

              {/* Required Fields */}
              <div className="space-y-2 pt-2 border-t border-dp-border">
                <span className="text-xs font-semibold text-dp-text-secondary uppercase tracking-wider">Required Fields</span>
                <div className="flex flex-wrap gap-1.5">
                  {(dataset?.schema || aiReq?.fields || []).map((field) => (
                    <span 
                      key={field.name} 
                      className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium bg-dp-bg-surface border border-dp-border rounded-md text-dp-text"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-dp-accent" />
                      {formatFieldName(field.name)}
                    </span>
                  ))}
                </div>
              </div>

              {/* Engine Status Note */}
              <div className="p-3 bg-dp-bg-surface/50 border border-dp-border rounded-lg flex items-start gap-2 text-[11px] text-dp-text-muted">
                <Sparkles className="w-4 h-4 text-dp-accent shrink-0 mt-0.5" />
                <span>
                  {fallbackUsed 
                    ? "Operating in Groq AI fallback mode. Dataset generated using LLM knowledge."
                    : "Autonomous multi-source extraction active with real-time provenance tracking."}
                </span>
              </div>

            </div>
          </Card>
        </div>

      </div>
    </div>
  );
};

export default WorkflowPage;
