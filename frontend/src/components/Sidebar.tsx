import React, { useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  PlusCircle,
  Database,
  BarChart3,
  History,
  Settings,
  ChevronLeft,
  ChevronRight,
  Compass,
  X,
} from 'lucide-react';
import { cn } from '@/utils/cn';

interface NavItem {
  label: string;
  path: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
  { label: 'New Task', path: '/new-task', icon: PlusCircle },
  { label: 'Datasets', path: '/datasets', icon: Database },
  { label: 'Analytics', path: '/analytics', icon: BarChart3 },
  { label: 'Workflow History', path: '/history', icon: History },
  { label: 'Settings', path: '/settings', icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onToggle,
  mobileOpen,
  onMobileClose,
}) => {
  const location = useLocation();

  /* Close mobile sidebar on route change */
  useEffect(() => {
    onMobileClose();
  }, [location.pathname]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      {/* ── Mobile Overlay & Drawer (small screens only) ── */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="fixed inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onMobileClose}
          />
          <aside
            className="fixed top-0 left-0 z-50 h-screen w-60 flex flex-col bg-dp-bg-raised border-r border-dp-border shadow-2xl"
          >
            {/* Brand + Close button */}
            <div className="flex items-center justify-between h-16 px-4 border-b border-dp-border shrink-0">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-dp-accent to-dp-accent-hover flex items-center justify-center shrink-0 shadow-glow">
                  <Compass className="w-[18px] h-[18px] text-white" />
                </div>
                <span className="text-[15px] font-bold text-dp-text tracking-tight whitespace-nowrap">
                  DataPilot <span className="text-dp-accent">AI</span>
                </span>
              </div>
              <button
                onClick={onMobileClose}
                className="p-1.5 rounded-md text-dp-text-muted hover:text-dp-text hover:bg-dp-bg-hover transition-colors cursor-pointer"
                aria-label="Close sidebar"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Mobile Nav Links */}
            <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      cn(
                        'group flex items-center gap-3 px-3 py-2.5 rounded-[var(--radius-button)] transition-all duration-200',
                        isActive
                          ? 'bg-dp-accent/10 text-dp-accent border border-dp-accent/15'
                          : 'text-dp-text-secondary hover:text-dp-text hover:bg-dp-bg-hover border border-transparent'
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <Icon
                          className={cn(
                            'w-[18px] h-[18px] shrink-0',
                            isActive ? 'text-dp-accent' : 'text-dp-text-muted group-hover:text-dp-text-secondary'
                          )}
                        />
                        <span className="text-sm font-medium truncate">{item.label}</span>
                      </>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </aside>
        </div>
      )}

      {/* ── Desktop In-Flow Sticky Sidebar (lg+ screens) ── */}
      <aside
        className={cn(
          'hidden lg:flex flex-col shrink-0 sticky top-0 h-screen',
          'bg-dp-bg-raised border-r border-dp-border z-40',
          'transition-all duration-300 ease-out',
          collapsed ? 'w-[68px]' : 'w-60'
        )}
      >
        {/* ── Brand ── */}
        <div
          className={cn(
            'flex items-center h-16 px-4 border-b border-dp-border shrink-0',
            collapsed ? 'justify-center' : 'justify-between'
          )}
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-dp-accent to-dp-accent-hover flex items-center justify-center shrink-0 shadow-glow">
              <Compass className="w-[18px] h-[18px] text-white" />
            </div>
            {!collapsed && (
              <span className="text-[15px] font-bold text-dp-text tracking-tight whitespace-nowrap">
                DataPilot <span className="text-dp-accent">AI</span>
              </span>
            )}
          </div>
        </div>

        {/* ── Navigation ── */}
        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    'group flex items-center gap-3 rounded-[var(--radius-button)] transition-all duration-200',
                    collapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2.5',
                    isActive
                      ? 'bg-dp-accent/10 text-dp-accent border border-dp-accent/15'
                      : 'text-dp-text-secondary hover:text-dp-text hover:bg-dp-bg-hover border border-transparent'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={cn(
                        'w-[18px] h-[18px] shrink-0 transition-colors duration-200',
                        isActive
                          ? 'text-dp-accent'
                          : 'text-dp-text-muted group-hover:text-dp-text-secondary'
                      )}
                    />
                    {!collapsed && (
                      <span className="text-sm font-medium truncate">
                        {item.label}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* ── Collapse Toggle (desktop only) ── */}
        <div className="flex items-center justify-center p-3 border-t border-dp-border shrink-0">
          <button
            onClick={onToggle}
            className={cn(
              'flex items-center justify-center',
              'w-8 h-8 rounded-[var(--radius-button)]',
              'text-dp-text-muted hover:text-dp-text',
              'bg-dp-bg-surface hover:bg-dp-bg-hover',
              'border border-dp-border hover:border-dp-border-hover',
              'transition-all duration-200 cursor-pointer'
            )}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
