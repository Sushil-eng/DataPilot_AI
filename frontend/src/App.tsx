import { BrowserRouter, Routes, Route } from 'react-router-dom';
import AppLayout from '@/components/AppLayout';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import {
  DashboardPage,
  NewTaskPage,
  DatasetsPage,
  AnalyticsPage,
  HistoryPage,
  SettingsPage,
  DesignSystemPreview,
  WorkflowPage,
  LandingPage,
  LoginPage,
  RegisterPage,
} from '@/pages';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Landing & Auth pages */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Protected App shell with sidebar + topbar */}
        <Route
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="new-task" element={<NewTaskPage />} />
          <Route path="datasets" element={<DatasetsPage />} />
          <Route path="datasets/:datasetId" element={<DatasetsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="settings" element={<SettingsPage />} />
          <Route path="workflow" element={<WorkflowPage />} />
          <Route path="workflow/:taskId" element={<WorkflowPage />} />

          <Route path="design" element={<DesignSystemPreview />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
