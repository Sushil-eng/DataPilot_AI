import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, Lightbulb, SlidersHorizontal, AlertCircle, CheckCircle2, Loader2, Cpu, Database, Network } from 'lucide-react';
import { Card, Button, Textarea, Select } from '@/components';
import { createTask, generateTaskPlan, executeTask } from '@/services/api';

const EXAMPLE_PROMPTS = [
  "Find 50 Python developer jobs in Mumbai.",
  "Find 30 AI startups in India founded after 2022.",
  "Find laptops under ₹50,000 with at least 16GB RAM.",
  "Find construction companies in Mumbai with their website, location and services."
];

const EXAMPLE_LABELS = [
  "Python Developer Jobs",
  "AI Startups India",
  "Laptop Search",
  "Construction Companies"
];

const PLANNING_STEPS = [
  { label: "Understanding your request...", icon: Sparkles },
  { label: "Identifying required data...", icon: Cpu },
  { label: "Designing dataset...", icon: Database },
  { label: "Creating collection workflow...", icon: Network },
  { label: "Plan ready", icon: CheckCircle2 }
];

const NewTaskPage: React.FC = () => {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // AI Planning state
  const [isPlanning, setIsPlanning] = useState(false);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  const [records, setRecords] = useState('1');
  const [freshness, setFreshness] = useState('Latest');

  const handleExampleClick = (index: number) => {
    setPrompt(EXAMPLE_PROMPTS[index]);
    setError('');
  };

  const handleSubmit = async () => {
    if (!prompt.trim()) {
      setError("Please describe what data you need.");
      return;
    }
    
    setError('');
    setIsSubmitting(true);
    
    try {
      const recordLimit = parseInt(records, 10) || 1;
      
      // Step 1: Create Task (POST /api/tasks)
      const task = await createTask(prompt.trim(), recordLimit);
      
      // Step 2: Show Planning State
      setIsPlanning(true);
      setCurrentStepIndex(1);

      // Step 3: Generate AI Plan (POST /api/tasks/{task_id}/plan)
      await generateTaskPlan(task.id);
      setCurrentStepIndex(3);

      // Step 4: Start background workflow execution
      try {
        await executeTask(task.id);
      } catch (execErr) {
        console.warn("Background execution notification:", execErr);
      }
      
      setCurrentStepIndex(4);

      // Immediately navigate to the Workflow page to watch real-time execution
      navigate(`/workflow/${task.id}`);
    } catch (err: any) {
      setIsPlanning(false);
      setIsSubmitting(false);
      setCurrentStepIndex(0);
      
      const msg = err.message || "Failed to generate AI data workflow.";
      if (msg.includes('unavailable') || msg.includes('fetch')) {
        setError("Backend server is unavailable. Please ensure FastAPI server is running.");
      } else if (msg.includes('LLM') || msg.includes('Groq') || msg.includes('502')) {
        setError("AI Service error: " + msg);
      } else {
        setError(msg);
      }
    }
  };

  return (
    <div className="max-w-4xl w-full space-y-8 animate-fade-in pb-12 min-w-0">
      {/* ── Header ── */}
      <div>
        <h2 className="text-3xl font-bold text-dp-text tracking-tight">
          What data do you need?
        </h2>
        <p className="text-base text-dp-text-secondary mt-2 max-w-2xl">
          Describe your data requirement and DataPilot AI will automatically understand your request, build a dynamic dataset schema, and construct an execution plan.
        </p>
      </div>

      {isPlanning ? (
        /* ── AI Planning Loading UI ── */
        <Card variant="accent" padding="lg" className="border border-dp-accent/40 bg-dp-bg-raised shadow-xl animate-fade-in">
          <div className="space-y-8 py-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-dp-accent/20 flex items-center justify-center animate-pulse">
                <Sparkles className="w-5 h-5 text-dp-accent" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-dp-text">AI Planning in Progress</h3>
                <p className="text-sm text-dp-text-secondary">Analyzing natural language requirements and engineering dataset workflow...</p>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-mono text-dp-text-secondary">
                <span>STAGE {Math.min(currentStepIndex + 1, 5)} OF 5</span>
                <span className="text-dp-accent font-bold">{Math.round(((currentStepIndex + 1) / 5) * 100)}%</span>
              </div>
              <div className="w-full bg-dp-bg-surface h-2.5 rounded-full overflow-hidden border border-dp-border">
                <div 
                  className="bg-gradient-to-r from-dp-accent to-dp-accent-hover h-full rounded-full transition-all duration-500 ease-out"
                  style={{ width: `${((currentStepIndex + 1) / 5) * 100}%` }}
                />
              </div>
            </div>

            {/* Stepper Timeline */}
            <div className="space-y-3 pt-2">
              {PLANNING_STEPS.map((stepItem, idx) => {
                const StepIcon = stepItem.icon;
                const isDone = idx < currentStepIndex;
                const isCurrent = idx === currentStepIndex;

                return (
                  <div 
                    key={stepItem.label} 
                    className={`flex items-center gap-3 p-3 rounded-lg border transition-all duration-300 ${
                      isCurrent 
                        ? 'bg-dp-accent/10 border-dp-accent text-dp-text shadow-sm' 
                        : isDone 
                        ? 'bg-dp-bg-surface/60 border-dp-success/30 text-dp-text' 
                        : 'bg-dp-bg-surface/20 border-dp-border/40 text-dp-text-muted opacity-50'
                    }`}
                  >
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                      isDone ? 'bg-dp-success text-white' :
                      isCurrent ? 'bg-dp-accent text-white animate-spin' :
                      'bg-dp-bg-surface text-dp-text-muted border border-dp-border'
                    }`}>
                      {isDone ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : isCurrent ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <StepIcon className="w-3.5 h-3.5" />
                      )}
                    </div>

                    <span className={`text-sm font-medium ${isCurrent ? 'text-dp-accent font-semibold' : ''}`}>
                      {stepItem.label}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="text-center text-xs text-dp-text-muted italic pt-2">
              Powered by LLM Requirement Analyzer & Dynamic Schema Generator
            </div>
          </div>
        </Card>
      ) : (
        /* ── Standard New Task Form ── */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 min-w-0">
          {/* ── Left Column: Prompt & Examples ── */}
          <div className="lg:col-span-2 space-y-8 min-w-0">
            
            {/* Prompt Input */}
            <div className="space-y-4">
              <div className="relative">
                <Textarea
                  value={prompt}
                  onChange={(e) => {
                    setPrompt(e.target.value);
                    if (error) setError('');
                  }}
                  error={error}
                  placeholder="Example: Find 50 AI startups in India founded after 2022 with founders, location and funding."
                  className="min-h-[180px] text-base p-4 pl-12 bg-dp-bg-raised border-dp-border focus:border-dp-accent/50 shadow-sm"
                />
                <Sparkles className="absolute left-4 top-4 w-5 h-5 text-dp-accent" />
              </div>

              {error && (
                <div className="p-3 bg-dp-error/10 border border-dp-error/30 rounded-[var(--radius-button)] text-sm text-dp-error flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{error}</span>
                </div>
              )}
              
              {/* Examples */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-medium text-dp-text-secondary">
                  <Lightbulb className="w-4 h-4 text-dp-warning" />
                  <span>Example requests</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_LABELS.map((label, idx) => (
                    <button
                      key={label}
                      type="button"
                      onClick={() => handleExampleClick(idx)}
                      className="px-3 py-1.5 text-xs font-medium rounded-full bg-dp-bg-surface border border-dp-border text-dp-text hover:border-dp-accent hover:text-dp-accent transition-colors cursor-pointer"
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
            
          </div>

          {/* ── Right Column: Configuration ── */}
          <div className="space-y-6 min-w-0">
            <Card variant="bordered" padding="md" className="sticky top-24">
              <div className="flex items-center gap-2 mb-6 border-b border-dp-border pb-4">
                <SlidersHorizontal className="w-4 h-4 text-dp-text-secondary" />
                <h3 className="font-semibold text-dp-text">Configuration</h3>
              </div>
              
              <div className="space-y-6">
                {/* Selects */}
                <div className="space-y-4">
                  <Select 
                    label="Number of records" 
                    value={records}
                    onChange={(e) => setRecords(e.target.value)}
                  >
                    <option value="1">1 record</option>
                    <option value="2">2 records</option>
                    <option value="3">3 records</option>
                    <option value="4">4 records</option>
                    <option value="5">5 records</option>
                  </Select>
                  
                  <Select 
                    label="Data freshness"
                    value={freshness}
                    onChange={(e) => setFreshness(e.target.value)}
                  >
                    <option value="Latest">Latest (Live extraction)</option>
                    <option value="Cached (24h)">Cached (Last 24h)</option>
                    <option value="Any">Any available</option>
                  </Select>
                </div>

                {/* Submit */}
                <div className="pt-4 border-t border-dp-border">
                  <Button 
                    fullWidth 
                    size="lg" 
                    icon={<ArrowRight className="w-4 h-4" />} 
                    iconPosition="right"
                    onClick={handleSubmit}
                    loading={isSubmitting}
                  >
                    Create Data Workflow
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewTaskPage;

