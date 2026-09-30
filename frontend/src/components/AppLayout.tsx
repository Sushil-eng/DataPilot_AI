import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '@/components/Sidebar';
import Topbar from '@/components/Topbar';

/* Map route paths to page titles for the topbar */
const pageTitles: Record<string, string> = {
  '/dashboard': 'Overview',
  '/new-task': 'New Task',
  '/datasets': 'Datasets',
  '/analytics': 'Analytics',
  '/history': 'Workflow History',
  '/settings': 'Settings',
  '/workflow': 'Workflow',
  '/design': 'Design System',
};

const AppLayout: React.FC = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  const pageTitle = pageTitles[location.pathname] || '';

  return (
    <div className="flex min-h-screen bg-dp-bg w-full overflow-x-hidden">
      {/* ── Sidebar (In-flow flex sibling on desktop, drawer on mobile) ── */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((prev) => !prev)}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
      />

      {/* ── Right Content Column (Topbar + Page View) ── */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen w-full">
        {/* Topbar */}
        <Topbar
          sidebarCollapsed={sidebarCollapsed}
          onMenuClick={() => setMobileOpen(true)}
          pageTitle={pageTitle}
        />

        {/* Main Content Area */}
        <main className="flex-1 p-4 lg:p-6 w-full max-w-full min-w-0 overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppLayout;
