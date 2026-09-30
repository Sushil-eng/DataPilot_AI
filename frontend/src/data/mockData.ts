import {
  Activity,
  Database,
  Globe2,
  CheckCircle2,
} from 'lucide-react';

export const dashboardKPIs = [
  {
    id: 'active-tasks',
    label: 'Active Tasks',
    value: '3',
    icon: Activity,
    trend: '+1 since yesterday',
    trendDirection: 'up',
  },
  {
    id: 'records-collected',
    label: 'Records Collected',
    value: '12,480',
    icon: Database,
    trend: '+14% this week',
    trendDirection: 'up',
  },
  {
    id: 'sources-processed',
    label: 'Sources Processed',
    value: '284',
    icon: Globe2,
    trend: '+42 this week',
    trendDirection: 'up',
  },
  {
    id: 'datasets',
    label: 'Datasets',
    value: '18',
    icon: CheckCircle2,
    trend: '+2 this week',
    trendDirection: 'up',
  },
];

export const recentTasks = [
  {
    id: 'task-1',
    title: 'Find AI startups in Mumbai hiring Python developers',
    status: 'Completed',
    records: 124,
    sources: 18,
    progress: 100,
  },
  {
    id: 'task-2',
    title: 'Find construction companies in Mumbai',
    status: 'Running',
    records: null,
    sources: null,
    progress: 67,
  },
  {
    id: 'task-3',
    title: 'Find SaaS companies founded after 2020',
    status: 'Completed',
    records: 86,
    sources: 12,
    progress: 100,
  },
];

export const activityChartData = [
  { time: '00:00', records: 120 },
  { time: '04:00', records: 300 },
  { time: '08:00', records: 450 },
  { time: '12:00', records: 800 },
  { time: '16:00', records: 1240 },
  { time: '20:00', records: 890 },
  { time: '23:59', records: 500 },
];

export const recentDatasets = [
  {
    id: 'ds-1',
    name: 'Mumbai AI Startups (Hiring)',
    records: 124,
    sources: 18,
    status: 'Ready',
    created: '2 hours ago',
  },
  {
    id: 'ds-2',
    name: 'SaaS Companies post-2020',
    records: 86,
    sources: 12,
    status: 'Ready',
    created: '5 hours ago',
  },
  {
    id: 'ds-3',
    name: 'Healthcare Providers in Delhi',
    records: 450,
    sources: 34,
    status: 'Archived',
    created: '2 days ago',
  },
];

export interface DatasetRow {
  id: string;
  company: string;
  jobTitle: string;
  location: string;
  salary: string;
  industry: string;
  website: string;
  source: string;
  confidence: number;
  collectedAt: string;
}

export const datasetRows: DatasetRow[] = [
  { id: '1', company: 'TechNova AI', jobTitle: 'Python Developer', location: 'Mumbai', salary: '₹8–12 LPA', industry: 'AI & ML', website: 'technova.ai', source: 'LinkedIn', confidence: 98, collectedAt: '2 hrs ago' },
  { id: '2', company: 'DataSphere', jobTitle: 'Data Engineer', location: 'Mumbai', salary: '₹10–15 LPA', industry: 'Data Analytics', website: 'datasphere.in', source: 'Naukri', confidence: 95, collectedAt: '3 hrs ago' },
  { id: '3', company: 'NeuralCraft', jobTitle: 'Senior Python Dev', location: 'Pune', salary: '₹15–22 LPA', industry: 'AI Services', website: 'neuralcraft.io', source: 'Company Site', confidence: 99, collectedAt: '3 hrs ago' },
  { id: '4', company: 'Cognitive Minds', jobTitle: 'Backend Engineer (Python)', location: 'Mumbai', salary: '₹6–10 LPA', industry: 'AI Education', website: 'cognitiveminds.in', source: 'AngelList', confidence: 88, collectedAt: '4 hrs ago' },
  { id: '5', company: 'Visionary Tech', jobTitle: 'Computer Vision Engineer', location: 'Mumbai', salary: '₹12–18 LPA', industry: 'Computer Vision', website: 'visionary.tech', source: 'LinkedIn', confidence: 92, collectedAt: '4 hrs ago' },
  { id: '6', company: 'AlphaData', jobTitle: 'Python/Django Developer', location: 'Bengaluru', salary: '₹8–14 LPA', industry: 'FinTech AI', website: 'alphadata.co.in', source: 'Naukri', confidence: 96, collectedAt: '5 hrs ago' },
  { id: '7', company: 'Sentient Labs', jobTitle: 'Machine Learning Engineer', location: 'Mumbai', salary: '₹14–20 LPA', industry: 'AI Research', website: 'sentientlabs.ai', source: 'Company Site', confidence: 97, collectedAt: '5 hrs ago' },
  { id: '8', company: 'BotForge', jobTitle: 'RPA Developer (Python)', location: 'Mumbai', salary: '₹5–9 LPA', industry: 'Automation', website: 'botforge.in', source: 'Indeed', confidence: 85, collectedAt: '6 hrs ago' },
  { id: '9', company: 'InsightIQ', jobTitle: 'Data Scientist', location: 'Mumbai', salary: '₹18–25 LPA', industry: 'Retail AI', website: 'insightiq.com', source: 'LinkedIn', confidence: 94, collectedAt: '6 hrs ago' },
  { id: '10', company: 'NexGen AI', jobTitle: 'Python Full Stack Dev', location: 'Pune', salary: '₹9–13 LPA', industry: 'AI SaaS', website: 'nexgenai.io', source: 'AngelList', confidence: 91, collectedAt: '7 hrs ago' },
  { id: '11', company: 'Predictive Solutions', jobTitle: 'Python Scripting Engineer', location: 'Mumbai', salary: '₹4–7 LPA', industry: 'Consulting', website: 'predictivesol.in', source: 'Naukri', confidence: 82, collectedAt: '7 hrs ago' },
  { id: '12', company: 'DeepSense', jobTitle: 'NLP Engineer', location: 'Bengaluru', salary: '₹16–24 LPA', industry: 'NLP', website: 'deepsense.ai', source: 'Company Site', confidence: 99, collectedAt: '8 hrs ago' },
  { id: '13', company: 'Quantum Data', jobTitle: 'Python Developer', location: 'Mumbai', salary: '₹7–11 LPA', industry: 'Big Data', website: 'quantumdata.co', source: 'LinkedIn', confidence: 93, collectedAt: '8 hrs ago' },
  { id: '14', company: 'AI Dynamics', jobTitle: 'Backend Dev (FastAPI)', location: 'Mumbai', salary: '₹10–16 LPA', industry: 'Robotics', website: 'aidynamics.in', source: 'Indeed', confidence: 89, collectedAt: '9 hrs ago' },
  { id: '15', company: 'SmartServe', jobTitle: 'Python Automation Tester', location: 'Pune', salary: '₹6–8 LPA', industry: 'AI Services', website: 'smartserve.ai', source: 'Naukri', confidence: 87, collectedAt: '9 hrs ago' },
];

/* ── Analytics Chart Data ── */

export const analyticsLocationData = [
  { name: 'Mumbai', value: 45 },
  { name: 'Bengaluru', value: 38 },
  { name: 'Pune', value: 24 },
  { name: 'Delhi NCR', value: 17 },
];

export const analyticsIndustryData = [
  { name: 'AI & ML', value: 35 },
  { name: 'Data Analytics', value: 25 },
  { name: 'Computer Vision', value: 15 },
  { name: 'NLP', value: 12 },
  { name: 'Robotics', value: 13 },
];

export const analyticsSalaryData = [
  { range: '₹0–5 LPA', count: 12 },
  { range: '₹5–10 LPA', count: 34 },
  { range: '₹10–15 LPA', count: 45 },
  { range: '₹15–20 LPA', count: 22 },
  { range: '₹20+ LPA', count: 11 },
];

export const analyticsCollectionData = [
  { date: 'Mon', records: 180 },
  { date: 'Tue', records: 340 },
  { date: 'Wed', records: 520 },
  { date: 'Thu', records: 410 },
  { date: 'Fri', records: 680 },
  { date: 'Sat', records: 290 },
  { date: 'Sun', records: 150 },
];

export const analyticsSourceData = [
  { name: 'LinkedIn', value: 52 },
  { name: 'Naukri', value: 38 },
  { name: 'Company Site', value: 24 },
  { name: 'AngelList', value: 10 },
];

/* ── Workflow History ── */

export interface WorkflowHistoryRow {
  id: string;
  task: string;
  created: string;
  status: 'Completed' | 'Running' | 'Failed';
  records: number;
  duration: string;
}

export const workflowHistory: WorkflowHistoryRow[] = [
  { id: 'wf-1', task: 'AI startups in Mumbai', created: 'Today', status: 'Completed', records: 124, duration: '2m 14s' },
  { id: 'wf-2', task: 'Construction companies in Mumbai', created: 'Yesterday', status: 'Completed', records: 86, duration: '1m 42s' },
  { id: 'wf-3', task: 'SaaS companies in India', created: '2 days ago', status: 'Completed', records: 215, duration: '3m 08s' },
  { id: 'wf-4', task: 'Healthcare providers in Delhi', created: '3 days ago', status: 'Failed', records: 0, duration: '0m 45s' },
  { id: 'wf-5', task: 'Fintech startups globally', created: '1 week ago', status: 'Completed', records: 540, duration: '12m 30s' },
];
