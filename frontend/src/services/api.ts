const rawApiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
export const API_BASE_URL = rawApiUrl.replace(/\/+$/, '');

export interface DataFieldInfo {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
}

export interface AIRequirements {
  intent: string;
  goal: string;
  record_limit: number;
  filters: Record<string, any>;
  fields: DataFieldInfo[];
  workflow_steps: string[];
  confidence?: number;
  notes?: string;
}

export interface DynamicSchemaInfo {
  schema_name: string;
  description: string;
  fields: DataFieldInfo[];
  total_fields: number;
  required_count: number;
}

export interface Task {
  id: string;
  _id?: string;
  prompt: string;
  record_limit: number;
  user_id: string;
  status: 'pending' | 'planning' | 'planned' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  record_count: number;
  current_step?: string;
  current_message?: string;
  fallback_used?: boolean;
  fallback_notice?: string;
  dataset_id?: string;
  ai_requirements?: AIRequirements;
  created_at: string;
  updated_at: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  description?: string;
  tool?: string;
  status: 'pending' | 'planning' | 'planned' | 'running' | 'completed' | 'failed' | 'skipped' | 'fallback' | 'cancelled';
  depends_on?: string | null;
  message?: string;
  result?: Record<string, any> | null;
}

export interface Workflow {
  id: string;
  _id?: string;
  task_id: string;
  status: 'pending' | 'planning' | 'planned' | 'running' | 'completed' | 'failed' | 'cancelled';
  workflow_type?: string;
  goal?: string;
  intent?: string;
  record_limit?: number;
  progress: number;
  current_step?: string;
  current_message?: string;
  fallback_used?: boolean;
  fallback_notice?: string;
  steps: WorkflowStep[];
  total_steps?: number;
  created_at: string;
  updated_at: string;
}

export interface DatasetSchemaField {
  name: string;
  type: string;
  description?: string;
  required?: boolean;
}

export interface Dataset {
  id: string;
  _id?: string;
  task_id?: string;
  name: string;
  description: string;
  schema: DatasetSchemaField[];
  dynamic_schema?: DynamicSchemaInfo;
  record_count: number;
  fallback_used?: boolean;
  fallback_notice?: string;
  created_at: string;
  updated_at: string;
}

export interface DatasetRecord {
  id: string;
  _id?: string;
  dataset_id: string;
  data: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface Source {
  id: string;
  _id?: string;
  dataset_id: string;
  url: string;
  title: string;
  source_type: string;
  collected_at: string;
}

export interface AIPlanResult {
  task_id: string;
  requirements: AIRequirements;
  schema: DynamicSchemaInfo;
  workflow: Workflow;
}

export interface OverviewStats {
  active_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_tasks: number;
  total_records: number;
  total_sources: number;
  total_datasets: number;
}

export interface ActivityPoint {
  date: string;
  records: number;
  tasks: number;
}

export interface ActivityData {
  data: ActivityPoint[];
}

export interface FieldStatistic {
  field_name: string;
  field_type: string;
  total_values: number;
  non_null_count: number;
  null_count: number;
  minimum?: number;
  maximum?: number;
  average?: number;
  unique_count?: number;
  top_values?: Array<{ value: string; count: number }>;
  earliest?: string;
  latest?: string;
  source_count?: number;
  chart_type?: string;
}

export interface SourceStatistic {
  domain: string;
  count: number;
}

export interface DatasetAnalytics {
  dataset_id: string;
  dataset_name: string;
  description: string;
  record_count: number;
  field_count: number;
  source_count: number;
  valid_records: number;
  invalid_records: number;
  duplicates_removed: number;
  field_statistics: FieldStatistic[];
  source_statistics: SourceStatistic[];
}

export interface AuthUser {
  id: string;
  email: string;
  full_name?: string;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: {
    message: string;
  };
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const token = localStorage.getItem('datapilot_auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...((options.headers as Record<string, string>) || {}),
  };

  let response: Response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (err: any) {
    throw new Error(`Backend server is unavailable. Please ensure the FastAPI backend is running at ${API_BASE_URL}`);
  }

  let result: any = null;
  try {
    result = await response.json();
  } catch (parseErr) {
    if (!response.ok) {
      if (response.status === 404) {
        throw new Error(`API endpoint not found (404): ${endpoint}. Please check API configuration.`);
      }
      if (response.status >= 500) {
        throw new Error(`Server error (${response.status}): ${response.statusText}`);
      }
      throw new Error(`HTTP Error ${response.status}: ${response.statusText}`);
    }
  }

  if (!response.ok || (result && result.success === false)) {
    let errorMsg = '';

    if (typeof result?.detail === 'string') {
      errorMsg = result.detail;
    } else if (result?.detail?.error?.message) {
      errorMsg = result.detail.error.message;
    } else if (result?.error?.message) {
      errorMsg = result.error.message;
    } else if (result?.message) {
      errorMsg = result.message;
    } else {
      if (response.status === 401) {
        errorMsg = 'Invalid email or password';
      } else if (response.status === 400) {
        errorMsg = 'Bad request - invalid input data';
      } else if (response.status === 404) {
        errorMsg = `API endpoint not found (404): ${endpoint}`;
      } else if (response.status >= 500) {
        errorMsg = `Server error (${response.status}). Please try again later.`;
      } else {
        errorMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      }
    }

    throw new Error(errorMsg);
  }

  let data = (result && result.data !== undefined) ? result.data : result;
  if (data && typeof data === 'object') {
    if (data._id && !data.id) data.id = data._id;
    if (Array.isArray(data.items)) {
      data.items = data.items.map((item: any) => {
        if (item && item._id && !item.id) item.id = item._id;
        return item;
      });
    }
  }

  return data as T;
}

export async function getHealthCheck(): Promise<{ status: string; service?: string }> {
  return request<{ status: string; service?: string }>('/health');
}


// ==================================================
// TASK SERVICES
// ==================================================

export async function createTask(prompt: string, recordLimit: number = 50): Promise<Task> {
  return request<Task>('/tasks', {
    method: 'POST',
    body: JSON.stringify({ prompt, record_limit: recordLimit }),
  });
}

export async function generateTaskPlan(taskId: string): Promise<AIPlanResult> {
  return request<AIPlanResult>(`/tasks/${taskId}/plan`, {
    method: 'POST',
  });
}

export async function executeTask(taskId: string): Promise<{ task_id: string; status: string; message: string }> {
  return request<{ task_id: string; status: string; message: string }>(`/tasks/${taskId}/execute`, {
    method: 'POST',
  });
}

export async function getTasks(params: { status?: string; search?: string; page?: number; limit?: number } = {}): Promise<{ items: Task[]; page: number; limit: number }> {
  const query = new URLSearchParams();
  if (params.status && params.status !== 'All') query.append('status', params.status);
  if (params.search) query.append('search', params.search);
  if (params.page) query.append('page', params.page.toString());
  if (params.limit) query.append('limit', params.limit.toString());

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return request<{ items: Task[]; page: number; limit: number }>(`/tasks${queryString}`);
}

export async function getTask(taskId: string, options?: RequestInit): Promise<Task> {
  return request<Task>(`/tasks/${taskId}`, options);
}

export async function updateTask(taskId: string, updateData: Partial<Task>): Promise<{ message: string }> {
  return request<{ message: string }>(`/tasks/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
}

export async function deleteTask(taskId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/tasks/${taskId}`, {
    method: 'DELETE',
  });
}

// ==================================================
// WORKFLOW SERVICES
// ==================================================

export async function getWorkflow(taskId: string, options?: RequestInit): Promise<Workflow> {
  return request<Workflow>(`/workflows/${taskId}`, options);
}

export async function updateWorkflow(taskId: string, updateData: { status?: string; progress?: number }): Promise<Workflow> {
  return request<Workflow>(`/workflows/${taskId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
}

export async function getWorkflowSteps(taskId: string, options?: RequestInit): Promise<{ steps: WorkflowStep[] }> {
  return request<{ steps: WorkflowStep[] }>(`/workflows/${taskId}/steps`, options);
}

export async function updateWorkflowStep(
  taskId: string,
  stepId: string,
  stepUpdate: { status?: string; result?: Record<string, any> }
): Promise<WorkflowStep> {
  return request<WorkflowStep>(`/workflows/${taskId}/steps/${stepId}`, {
    method: 'PATCH',
    body: JSON.stringify(stepUpdate),
  });
}

// ==================================================
// DATASET SERVICES
// ==================================================

export async function getDatasets(
  params: { task_id?: string; search?: string; page?: number; limit?: number } = {},
  options?: RequestInit
): Promise<{ items: Dataset[]; page: number; limit: number }> {
  const query = new URLSearchParams();
  if (params.task_id) query.append('task_id', params.task_id);
  if (params.search) query.append('search', params.search);
  if (params.page) query.append('page', params.page.toString());
  if (params.limit) query.append('limit', params.limit.toString());

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return request<{ items: Dataset[]; page: number; limit: number }>(`/datasets${queryString}`, options);
}

export async function createDataset(datasetData: {
  task_id?: string;
  name: string;
  description?: string;
  schema?: DatasetSchemaField[];
}): Promise<Dataset> {
  return request<Dataset>('/datasets', {
    method: 'POST',
    body: JSON.stringify(datasetData),
  });
}

export async function getDataset(datasetId: string, options?: RequestInit): Promise<Dataset> {
  return request<Dataset>(`/datasets/${datasetId}`, options);
}

export async function updateDataset(datasetId: string, updateData: Partial<Dataset>): Promise<Dataset> {
  return request<Dataset>(`/datasets/${datasetId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
}

export async function deleteDataset(datasetId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/datasets/${datasetId}`, {
    method: 'DELETE',
  });
}

// ==================================================
// DATASET RECORD SERVICES
// ==================================================

export async function getDatasetRecords(
  datasetId: string,
  params: { page?: number; limit?: number; search?: string; sort_by?: string; order?: 'asc' | 'desc' } = {},
  options?: RequestInit
): Promise<{ items: DatasetRecord[]; page: number; limit: number; total: number }> {
  const query = new URLSearchParams();
  if (params.page) query.append('page', params.page.toString());
  if (params.limit) query.append('limit', params.limit.toString());
  if (params.search) query.append('search', params.search);
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.order) query.append('order', params.order);

  const queryString = query.toString() ? `?${query.toString()}` : '';
  return request<{ items: DatasetRecord[]; page: number; limit: number; total: number }>(`/datasets/${datasetId}/records${queryString}`, options);
}

export async function downloadDatasetExport(datasetId: string, format: 'csv' | 'json' = 'csv', filename?: string): Promise<void> {
  const url = `${API_BASE_URL}/datasets/${datasetId}/export?format=${format}`;
  const token = localStorage.getItem('datapilot_auth_token');
  const headers: Record<string, string> = token ? { 'Authorization': `Bearer ${token}` } : {};
  const response = await fetch(url, { headers });
  if (!response.ok) {
    let errorMsg = 'Failed to export dataset';
    try {
      const json = await response.json();
      errorMsg = json.detail?.error?.message || json.detail || errorMsg;
    } catch {}
    throw new Error(errorMsg);
  }
  const rawBlob = await response.blob();
  const mimeType = format === 'json' ? 'application/json' : 'text/csv;charset=utf-8;';
  const blob = new Blob([rawBlob], { type: mimeType });
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.setAttribute('download', filename || `dataset_export.${format}`);
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

// ==================================================
// AUTHENTICATION SERVICES — Phase 5 Prompt 3
// ==================================================

export async function loginUser(email: string, password: string): Promise<AuthResponse> {
  const res = await request<AuthResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (res.access_token) {
    localStorage.setItem('datapilot_auth_token', res.access_token);
  }
  return res;
}

export async function registerUser(email: string, password: string, full_name?: string): Promise<AuthResponse> {
  const res = await request<AuthResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password, full_name }),
  });
  if (res.access_token) {
    localStorage.setItem('datapilot_auth_token', res.access_token);
  }
  return res;
}

export async function getCurrentUser(): Promise<AuthUser> {
  return request<AuthUser>('/auth/me');
}

export function logoutUser(): void {
  localStorage.removeItem('datapilot_auth_token');
}


export async function createDatasetRecord(datasetId: string, recordData: Record<string, any>): Promise<DatasetRecord> {
  return request<DatasetRecord>(`/datasets/${datasetId}/records`, {
    method: 'POST',
    body: JSON.stringify(recordData),
  });
}

export async function updateDatasetRecord(
  datasetId: string,
  recordId: string,
  updateData: Record<string, any>
): Promise<DatasetRecord> {
  return request<DatasetRecord>(`/datasets/${datasetId}/records/${recordId}`, {
    method: 'PATCH',
    body: JSON.stringify(updateData),
  });
}

export async function deleteDatasetRecord(datasetId: string, recordId: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/datasets/${datasetId}/records/${recordId}`, {
    method: 'DELETE',
  });
}

// ==================================================
// SOURCE SERVICES
// ==================================================

export async function getSources(datasetId: string, options?: RequestInit): Promise<{ items: Source[]; count: number }> {
  return request<{ items: Source[]; count: number }>(`/sources/${datasetId}`, options);
}

export async function createSource(sourceData: {
  dataset_id: string;
  url: string;
  title: string;
  source_type: string;
}): Promise<Source> {
  return request<Source>('/sources', {
    method: 'POST',
    body: JSON.stringify(sourceData),
  });
}

// ==================================================
// ANALYTICS SERVICES — Phase 5
// ==================================================

export async function getOverviewStats(): Promise<OverviewStats> {
  return request<OverviewStats>('/analytics/overview');
}

export async function getActivityTimeline(days: number = 7): Promise<ActivityData> {
  return request<ActivityData>(`/analytics/activity?days=${days}`);
}

export async function getDatasetAnalytics(datasetId: string): Promise<DatasetAnalytics> {
  return request<DatasetAnalytics>(`/analytics/datasets/${datasetId}`);
}


