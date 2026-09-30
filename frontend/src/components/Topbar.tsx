import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, Menu, User, LogOut, ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAuth } from '@/context/AuthContext';

interface TopbarProps {
  sidebarCollapsed?: boolean;
  onMenuClick: () => void;
  pageTitle?: string;
}

const Topbar: React.FC<TopbarProps> = ({
  onMenuClick,
  pageTitle,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setProfileOpen(false);
      }
    };
    if (profileOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [profileOpen]);

  const handleLogout = () => {
    setProfileOpen(false);
    logout();
    navigate('/login');
  };

  const displayName = user?.full_name || user?.email?.split('@')[0] || 'User';
  const displayEmail = user?.email || '';

  return (
    <header
      className="sticky top-0 z-30 h-16 w-full bg-dp-bg/80 backdrop-blur-md border-b border-dp-border shrink-0"
    >
      <div className="flex items-center justify-between h-full px-4 lg:px-6 w-full max-w-full">
        {/* ── Left: Mobile menu + Page title ── */}
        <div className="flex items-center gap-3 min-w-0">
          {/* Mobile hamburger */}
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-[var(--radius-button)] text-dp-text-muted hover:text-dp-text hover:bg-dp-bg-hover transition-colors cursor-pointer"
            aria-label="Open sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>

          {/* Page title */}
          {pageTitle && (
            <h1 className="text-lg font-semibold text-dp-text truncate hidden sm:block">
              {pageTitle}
            </h1>
          )}
        </div>

        {/* ── Right: Search, Notifications, Profile ── */}
        <div className="flex items-center gap-1.5">
          {/* Search */}
          <button
            className={cn(
              'flex items-center gap-2',
              'h-9 rounded-[var(--radius-button)]',
              'text-dp-text-muted hover:text-dp-text',
              'transition-colors duration-200 cursor-pointer',
              // Desktop: looks like a search bar
              'lg:bg-dp-bg-surface lg:border lg:border-dp-border lg:hover:border-dp-border-hover lg:px-3 lg:w-64',
              // Mobile: just an icon button
              'p-2 lg:p-0'
            )}
            aria-label="Search"
          >
            <Search className="w-4 h-4 shrink-0" />
            <span className="hidden lg:block text-sm text-dp-text-muted">
              Search...
            </span>
            <kbd className="hidden lg:inline-flex items-center ml-auto text-[10px] font-mono text-dp-text-disabled bg-dp-bg-hover border border-dp-border rounded px-1.5 py-0.5">
              ⌘K
            </kbd>
          </button>

          {/* Notifications */}
          <button
            className={cn(
              'relative p-2 rounded-[var(--radius-button)]',
              'text-dp-text-muted hover:text-dp-text hover:bg-dp-bg-hover',
              'transition-colors duration-200 cursor-pointer'
            )}
            aria-label="Notifications"
          >
            <Bell className="w-[18px] h-[18px]" />
            {/* Notification dot */}
            <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-dp-accent ring-2 ring-dp-bg" />
          </button>

          {/* Divider */}
          <div className="hidden sm:block w-px h-6 bg-dp-border mx-1.5" />

          {/* Profile with Dropdown */}
          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setProfileOpen(prev => !prev)}
              className={cn(
                'flex items-center gap-2.5 p-1.5 pr-3 rounded-[var(--radius-button)]',
                'hover:bg-dp-bg-hover transition-colors duration-200 cursor-pointer',
                profileOpen && 'bg-dp-bg-hover'
              )}
              aria-label="User profile"
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-dp-accent/80 to-dp-accent-hover flex items-center justify-center">
                <User className="w-3.5 h-3.5 text-white" />
              </div>
              <div className="hidden sm:flex flex-col items-start">
                <span className="text-xs font-medium text-dp-text leading-tight">
                  {displayName}
                </span>
                <span className="text-[10px] text-dp-text-muted leading-tight">
                  Admin
                </span>
              </div>
              <ChevronDown className={cn(
                "w-3.5 h-3.5 text-dp-text-muted hidden sm:block transition-transform duration-200",
                profileOpen && "rotate-180"
              )} />
            </button>

            {/* Dropdown Menu */}
            {profileOpen && (
              <div className="absolute right-0 top-full mt-2 w-56 bg-dp-bg-raised border border-dp-border rounded-[var(--radius-card)] shadow-card-hover overflow-hidden animate-scale-in z-50">
                {/* User Info */}
                <div className="px-4 py-3 border-b border-dp-border">
                  <p className="text-sm font-medium text-dp-text truncate">{displayName}</p>
                  {displayEmail && (
                    <p className="text-xs text-dp-text-muted truncate mt-0.5">{displayEmail}</p>
                  )}
                </div>

                {/* Logout Button */}
                <div className="p-1.5">
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-2.5 w-full px-3 py-2 text-sm text-dp-text-secondary hover:text-dp-error hover:bg-dp-error/10 rounded-[var(--radius-button)] transition-colors cursor-pointer"
                  >
                    <LogOut className="w-4 h-4" />
                    <span className="font-medium">Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;

