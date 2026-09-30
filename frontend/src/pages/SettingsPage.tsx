import React, { useState, useRef } from 'react';
import { Save, UserCircle, Palette, Database, Bell, Shield, Check } from 'lucide-react';
import { Card, CardHeader, CardContent, Button, Input, Select } from '@/components';
import { useAuth } from '@/context/AuthContext';
import { cn } from '@/utils/cn';

interface SettingsSection {
  id: string;
  label: string;
  icon: React.ElementType;
}

const sections: SettingsSection[] = [
  { id: 'profile', label: 'Profile', icon: UserCircle },
  { id: 'appearance', label: 'Appearance', icon: Palette },
  { id: 'data', label: 'Data Preferences', icon: Database },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'security', label: 'Security', icon: Shield },
];

const SettingsPage: React.FC = () => {
  const { user } = useAuth();

  // Profile
  const [name, setName] = useState(user?.full_name || 'Sushil');
  const [email, setEmail] = useState(user?.email || 'sushil@datapilot.ai');

  // Appearance
  const [theme, setTheme] = useState('dark');

  // Data
  const [defaultRecords, setDefaultRecords] = useState('1');
  const [defaultFreshness, setDefaultFreshness] = useState('Latest');
  const [exportFormat, setExportFormat] = useState('csv');

  // Notifications
  const [emailNotif, setEmailNotif] = useState(true);
  const [taskComplete, setTaskComplete] = useState(true);
  const [weeklyReport, setWeeklyReport] = useState(false);

  // Security
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [saved, setSaved] = useState(false);
  const [activeSection, setActiveSection] = useState('profile');

  // Section refs for scrolling
  const sectionRefs: Record<string, React.RefObject<HTMLDivElement | null>> = {
    profile: useRef<HTMLDivElement>(null),
    appearance: useRef<HTMLDivElement>(null),
    data: useRef<HTMLDivElement>(null),
    notifications: useRef<HTMLDivElement>(null),
    security: useRef<HTMLDivElement>(null),
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const scrollToSection = (id: string) => {
    setActiveSection(id);
    sectionRefs[id]?.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const Toggle: React.FC<{ checked: boolean; onChange: (v: boolean) => void; label: string; description?: string }> = ({ checked, onChange, label, description }) => (
    <div className="flex items-center justify-between py-4">
      <div className="min-w-0 pr-4">
        <p className="text-sm font-medium text-dp-text">{label}</p>
        {description && <p className="text-xs text-dp-text-muted mt-0.5">{description}</p>}
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={cn(
          'relative w-11 h-6 rounded-full transition-colors duration-200 cursor-pointer shrink-0',
          checked ? 'bg-dp-accent' : 'bg-dp-bg-surface border border-dp-border'
        )}
      >
        <span className={cn(
          'absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200',
          checked ? 'translate-x-5' : 'translate-x-0'
        )} />
      </button>
    </div>
  );

  return (
    <div className="flex flex-col lg:flex-row gap-6 animate-fade-in pb-12 w-full min-h-[calc(100vh-8rem)]">

      {/* ── Settings Navigation Sidebar ── */}
      <div className="lg:w-60 shrink-0">
        <div className="lg:sticky lg:top-24 space-y-1">
          {/* Page Header (mobile/tablet) */}
          <div className="mb-6">
            <h2 className="text-2xl sm:text-3xl font-bold text-dp-text tracking-tight">Settings</h2>
            <p className="text-sm text-dp-text-secondary mt-1">Manage your account and workspace.</p>
          </div>

          {/* Nav Items */}
          <nav className="flex lg:flex-col gap-1 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
            {sections.map(section => {
              const Icon = section.icon;
              return (
                <button
                  key={section.id}
                  onClick={() => scrollToSection(section.id)}
                  className={cn(
                    'flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-button)] text-sm font-medium transition-all duration-200 cursor-pointer whitespace-nowrap',
                    activeSection === section.id
                      ? 'bg-dp-accent/10 text-dp-accent border border-dp-accent/15'
                      : 'text-dp-text-secondary hover:text-dp-text hover:bg-dp-bg-hover border border-transparent'
                  )}
                >
                  <Icon className={cn(
                    'w-4 h-4 shrink-0',
                    activeSection === section.id ? 'text-dp-accent' : 'text-dp-text-muted'
                  )} />
                  {section.label}
                </button>
              );
            })}
          </nav>

          {/* Save Button (desktop – sticky with nav) */}
          <div className="hidden lg:block pt-4 mt-4 border-t border-dp-border">
            <Button
              icon={saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
              onClick={handleSave}
              className={cn('w-full', saved && 'bg-dp-success border-dp-success hover:bg-dp-success/90')}
            >
              {saved ? 'Saved!' : 'Save Changes'}
            </Button>
          </div>
        </div>
      </div>

      {/* ── Settings Content ── */}
      <div className="flex-1 min-w-0 space-y-6">

        {/* Mobile Save Button */}
        <div className="lg:hidden flex justify-end">
          <Button
            icon={saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
            onClick={handleSave}
            className={cn(saved && 'bg-dp-success border-dp-success hover:bg-dp-success/90')}
          >
            {saved ? 'Saved!' : 'Save Changes'}
          </Button>
        </div>

        {/* ── Profile ── */}
        <div ref={sectionRefs.profile}>
          <Card variant="bordered" padding="md">
            <CardHeader title="Profile" description="Your personal information." className="mb-6" />
            <CardContent>
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 rounded-full bg-dp-accent/10 flex items-center justify-center text-dp-accent font-bold text-xl border-2 border-dp-accent/30 shrink-0">
                  {name.charAt(0).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="text-dp-text font-semibold truncate">{name}</p>
                  <p className="text-dp-text-muted text-sm truncate">{email}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Input label="Full Name" value={name} onChange={(e) => setName(e.target.value)} />
                <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Appearance ── */}
        <div ref={sectionRefs.appearance}>
          <Card variant="bordered" padding="md">
            <CardHeader title="Appearance" description="Customize how DataPilot AI looks." className="mb-6" />
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <Select label="Theme" value={theme} onChange={(e) => setTheme(e.target.value)}>
                  <option value="dark">Dark (Default)</option>
                  <option value="light">Light (Coming soon)</option>
                  <option value="system">System</option>
                </Select>
                <div className="flex flex-col gap-1.5">
                  <label className="text-xs font-semibold text-dp-text-secondary uppercase tracking-wider">Preview</label>
                  <div className="flex items-center gap-3 h-[42px]">
                    <div className="w-8 h-8 rounded-lg bg-dp-accent" title="Accent" />
                    <div className="w-8 h-8 rounded-lg bg-dp-bg-raised border border-dp-border" title="Surface" />
                    <div className="w-8 h-8 rounded-lg bg-dp-bg-surface border border-dp-border" title="Background" />
                    <div className="w-8 h-8 rounded-lg bg-dp-text" title="Text" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Data Preferences ── */}
        <div ref={sectionRefs.data}>
          <Card variant="bordered" padding="md">
            <CardHeader title="Data Preferences" description="Default settings for new data collection workflows." className="mb-6" />
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Select label="Default Records" value={defaultRecords} onChange={(e) => setDefaultRecords(e.target.value)}>
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                  <option value="4">4</option>
                  <option value="5">5</option>
                </Select>
                <Select label="Data Freshness" value={defaultFreshness} onChange={(e) => setDefaultFreshness(e.target.value)}>
                  <option value="Latest">Latest</option>
                  <option value="Cached">Cached (24h)</option>
                  <option value="Any">Any</option>
                </Select>
                <Select label="Export Format" value={exportFormat} onChange={(e) => setExportFormat(e.target.value)}>
                  <option value="csv">CSV</option>
                  <option value="xlsx">Excel (.xlsx)</option>
                  <option value="json">JSON</option>
                </Select>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Notifications ── */}
        <div ref={sectionRefs.notifications}>
          <Card variant="bordered" padding="md">
            <CardHeader title="Notifications" description="Control when and how you receive updates." className="mb-6" />
            <CardContent>
              <div className="divide-y divide-dp-border">
                <Toggle checked={emailNotif} onChange={setEmailNotif} label="Email Notifications" description="Receive email updates about your workflows." />
                <Toggle checked={taskComplete} onChange={setTaskComplete} label="Task Completion Alerts" description="Get notified when a data collection workflow finishes." />
                <Toggle checked={weeklyReport} onChange={setWeeklyReport} label="Weekly Summary Report" description="Receive a weekly digest of your analytics and usage." />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* ── Security ── */}
        <div ref={sectionRefs.security}>
          <Card variant="bordered" padding="md">
            <CardHeader title="Security" description="Update your password and manage account security." className="mb-6" />
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Input label="Current Password" type="password" placeholder="••••••••" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
                <Input label="New Password" type="password" placeholder="••••••••" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
                <Input label="Confirm Password" type="password" placeholder="••••••••" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
              </div>
              <div className="mt-4 pt-4 border-t border-dp-border flex items-center justify-between">
                <p className="text-xs text-dp-text-muted">Password must be at least 8 characters.</p>
                <Button variant="outline" size="sm">Update Password</Button>
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
};

export default SettingsPage;
