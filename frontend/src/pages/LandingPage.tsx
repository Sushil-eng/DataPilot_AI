import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Compass,
  ArrowRight,
  Play,
  MessageSquareText,
  Workflow,
  Bot,
  BarChart3,
  ShieldCheck,
  Fingerprint,
  LineChart,
  Search,
  FileDown,
  Sparkles,
  CheckCircle2,
  Database,
  TrendingUp,
  Globe,
  Menu,
  X
} from 'lucide-react';
import { Button } from '@/components';

const STEPS = [
  {
    step: '01',
    icon: MessageSquareText,
    title: 'Describe Requirements',
    subtitle: 'Natural Language Prompting',
    description: 'Ask for market research, company leads, job postings, or product data in plain English.',
    badge: 'Step 1'
  },
  {
    step: '02',
    icon: Workflow,
    title: 'AI Schema & Workflow',
    subtitle: 'Dynamic Intent Planning',
    description: 'DataPilot AI builds tailored JSON schemas, identifies sources, and plans collection steps.',
    badge: 'Step 2'
  },
  {
    step: '03',
    icon: Bot,
    title: 'Autonomous Collection',
    subtitle: 'Multi-Source Discovery',
    description: 'Scrapes, extracts, cleanses, standardizes, and deduplicates records automatically.',
    badge: 'Step 3'
  },
  {
    step: '04',
    icon: BarChart3,
    title: 'Explore & Export',
    subtitle: 'Interactive Intelligence',
    description: 'Analyze distribution charts, review field statistics, and export cleanly in CSV or JSON.',
    badge: 'Step 4'
  },
];

const FEATURES = [
  {
    icon: MessageSquareText,
    title: 'Natural Language Prompts',
    description: 'Describe complex data requirements in conversational language without writing scrapers.',
    color: 'from-orange-500/20 to-amber-500/10 text-orange-400',
  },
  {
    icon: Workflow,
    title: 'AI Pipeline Generation',
    description: 'Dynamic schema generation and automated 9-stage extraction workflow planning.',
    color: 'from-violet-500/20 to-purple-500/10 text-violet-400',
  },
  {
    icon: ShieldCheck,
    title: 'Source Provenance',
    description: 'Every record is mapped back to its source URL with title, snippet, and collection timestamps.',
    color: 'from-cyan-500/20 to-blue-500/10 text-cyan-400',
  },
  {
    icon: Fingerprint,
    title: 'Smart Deduplication',
    description: 'Exact fingerprinting and fuzzy string similarity matching to prune duplicate data.',
    color: 'from-emerald-500/20 to-teal-500/10 text-emerald-400',
  },
  {
    icon: LineChart,
    title: 'Real-time Analytics',
    description: 'Automated field value statistics, data quality audit scores, and domain breakdown charts.',
    color: 'from-amber-500/20 to-orange-500/10 text-amber-400',
  },
  {
    icon: Database,
    title: 'MongoDB Integration',
    description: 'Persisted datasets, task history, workflow execution logs, and full search capabilities.',
    color: 'from-blue-500/20 to-indigo-500/10 text-blue-400',
  },
  {
    icon: Search,
    title: 'Instant Data Exploration',
    description: 'Filter, sort, inspect detail view, and search across thousands of structured records.',
    color: 'from-rose-500/20 to-pink-500/10 text-rose-400',
  },
  {
    icon: FileDown,
    title: '1-Click CSV & JSON Export',
    description: 'Download structured datasets formatted and clean for your data science pipeline.',
    color: 'from-emerald-500/20 to-green-500/10 text-emerald-400',
  },
];

const METRICS = [
  { label: 'Records Extracted', value: '1.2M+', trend: '+28% this week' },
  { label: 'Data Accuracy Rate', value: '99.4%', trend: 'AI audited' },
  { label: 'Avg Workflow Time', value: '45s', trend: 'Real-time extraction' },
  { label: 'Supported Domains', value: 'Unlimited', trend: 'Generic scrapers' },
];

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-dp-bg text-dp-text relative overflow-x-hidden selection:bg-dp-accent/30 selection:text-white flex flex-col items-center">
      {/* ── Background Ambient Glow System ── */}
      {/* Fixed ambient grid — covers whole viewport */}
      <div className="bg-ambient-grid fixed inset-0 pointer-events-none z-0" />
      {/* Decorative glow — wrapped in overflow-hidden so it can never shift page layout */}
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="hero-gradient-glow" />
      </div>

      {/* ── Task 4: Responsive Floating Navbar ── */}
      <header className="fixed top-0 left-0 right-0 z-50 glass-nav border-b border-white/10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 sm:h-20 flex items-center justify-between">
          {/* Logo - Left Aligned */}
          <div 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 cursor-pointer group shrink-0"
          >
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-dp-accent via-orange-500 to-amber-500 flex items-center justify-center shadow-glow group-hover:scale-105 transition-transform duration-300">
              <Compass className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <span className="text-base sm:text-lg font-extrabold text-dp-text tracking-tight font-display flex items-center gap-1.5">
                DataPilot <span className="text-gradient-orange">AI</span>
              </span>
              <span className="text-[9px] sm:text-[10px] text-dp-text-muted tracking-wider uppercase font-medium">Data Intelligence</span>
            </div>
          </div>

          {/* Navigation Links - Centered on Desktop */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-dp-text-secondary">
            <a href="#features" className="hover:text-dp-text transition-colors">Features</a>
            <a href="#how-it-works" className="hover:text-dp-text transition-colors">How It Works</a>
            <a href="#metrics" className="hover:text-dp-text transition-colors">Analytics</a>
          </nav>

          {/* Action Buttons - Right Aligned */}
          <div className="hidden sm:flex items-center gap-3 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/login')}
              className="text-dp-text-secondary hover:text-dp-text"
            >
              Sign In
            </Button>
            <Button
              size="sm"
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
              onClick={() => navigate('/dashboard')}
              className="bg-gradient-to-r from-dp-accent to-orange-500 hover:from-dp-accent-hover hover:to-orange-400 text-white font-semibold shadow-glow btn-glow-accent rounded-lg"
            >
              Launch Platform
            </Button>
          </div>

          {/* Mobile Hamburger Toggle Button */}
          <button
            onClick={() => setMobileMenuOpen(prev => !prev)}
            className="sm:hidden p-2 rounded-lg text-dp-text-secondary hover:text-dp-text hover:bg-black/5 transition-colors"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>

        {/* Mobile Dropdown Navigation Menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden bg-white/95 border-b border-black/8 px-4 pt-3 pb-5 flex flex-col gap-3 backdrop-blur-xl animate-fade-in">
            <a 
              href="#features" 
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm font-medium text-dp-text-secondary hover:text-dp-text py-1.5 border-b border-black/6"
            >
              Features
            </a>
            <a 
              href="#how-it-works" 
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm font-medium text-dp-text-secondary hover:text-dp-text py-1.5 border-b border-black/6"
            >
              How It Works
            </a>
            <a 
              href="#metrics" 
              onClick={() => setMobileMenuOpen(false)}
              className="text-sm font-medium text-dp-text-secondary hover:text-dp-text py-1.5 border-b border-black/6"
            >
              Metrics
            </a>
            <div className="flex flex-col gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => { setMobileMenuOpen(false); navigate('/login'); }}
                className="w-full justify-center"
              >
                Sign In
              </Button>
              <Button
                size="sm"
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
                onClick={() => { setMobileMenuOpen(false); navigate('/dashboard'); }}
                className="w-full justify-center bg-gradient-to-r from-dp-accent to-orange-500 text-white font-semibold"
              >
                Launch Platform
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* ── Hero Section — padding computed from --header-height CSS variable ── */}
      <section className="hero-section w-full pb-20 px-4 sm:px-6 lg:px-8 z-10 flex flex-col items-center">
        <div className="w-full max-w-4xl mx-auto flex flex-col items-center text-center">
          {/* Release Badge */}
          <div className="inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full glass-panel border-dp-accent/30 text-dp-accent text-xs font-semibold mb-10 animate-fade-in shadow-glow">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-dp-accent opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-dp-accent"></span>
            </span>
            <span className="text-dp-text-secondary">Next-Gen Autonomous Data Intelligence</span>
            <span className="text-dp-border hidden sm:inline">|</span>
            <span className="text-gradient-orange font-bold flex items-center gap-1 hidden sm:inline-flex">
              v2.0 Released <Sparkles className="w-3 h-3 text-amber-400" />
            </span>
          </div>

          {/* Centered Main Heading */}
          <h1 className="w-full text-3xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-dp-text leading-[1.18] mb-8 font-display text-center">
            Turn Business Questions <br className="hidden sm:inline" />
            <span className="text-gradient-orange">Into Actionable Datasets</span>
          </h1>

          {/* Centered Description */}
          <p className="w-full text-base sm:text-lg lg:text-xl text-dp-text-secondary max-w-2xl mx-auto text-center mb-10 leading-loose font-sans">
            Describe what data you need in plain English. DataPilot AI autonomously plans schemas, discovers sources, extracts fields, validates quality, and organizes information into source-backed datasets.
          </p>

          {/* Centered CTA Buttons */}
          <div className="flex items-center justify-center gap-5 flex-wrap mb-8 w-full">
            <Button
              size="lg"
              icon={<ArrowRight className="w-5 h-5" />}
              iconPosition="right"
              onClick={() => navigate('/new-task')}
              className="bg-gradient-to-r from-dp-accent via-orange-500 to-amber-500 hover:from-dp-accent-hover text-white font-bold px-8 py-3.5 text-base shadow-glow-strong btn-glow-accent rounded-xl"
            >
              Start Free Task
            </Button>
            <Button
              variant="outline"
              size="lg"
              icon={<Play className="w-4 h-4 text-dp-accent fill-dp-accent" />}
              onClick={() => navigate('/dashboard')}
              className="bg-white text-dp-text-secondary border border-black/12 hover:border-dp-accent/50 hover:text-dp-accent rounded-xl px-7 py-3.5 font-semibold hover:bg-orange-50 shadow-sm"
            >
              Explore Live Dashboard
            </Button>
          </div>

          {/* Centered Feature Micro-Badges */}
          <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-12 text-sm font-medium text-dp-text-muted mb-20 w-full">
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span className="text-dp-text-secondary">No Code Scraper Setup</span>
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span className="text-dp-text-secondary">100% Source-Backed Records</span>
            </div>
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span className="text-dp-text-secondary">Automated Deduplication</span>
            </div>
          </div>
        </div>

        {/* ── Task 3: Centered Responsive Dashboard Preview ── */}
        <div className="w-full max-w-5xl mx-auto relative">
          <div className="absolute -inset-1.5 bg-gradient-to-r from-dp-accent/15 via-violet-500/8 to-amber-500/15 rounded-3xl blur-2xl opacity-50" />
          
          <div className="relative w-full rounded-2xl glass-panel border border-black/8 overflow-hidden shadow-card-hover">
            {/* Mock Window Header */}
            <div className="flex items-center justify-between px-5 sm:px-6 py-3.5 border-b border-black/8 bg-slate-50/90">
              <div className="flex items-center gap-2 min-w-0">
                <div className="w-3 h-3 rounded-full bg-rose-500/80 shrink-0" />
                <div className="w-3 h-3 rounded-full bg-amber-500/80 shrink-0" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/80 shrink-0" />
                <span className="text-xs font-mono text-dp-text-muted ml-2 sm:ml-3 flex items-center gap-1.5 truncate">
                  <Globe className="w-3.5 h-3.5 text-dp-accent shrink-0" /> datapilot.ai/platform/dashboard
                </span>
              </div>
              <div className="hidden sm:flex items-center gap-2 text-[11px] font-medium text-dp-text-muted shrink-0">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                FastAPI + MongoDB Connected
              </div>
            </div>

            {/* Mock Dashboard Content Grid */}
            <div className="p-5 sm:p-7 lg:p-9 bg-slate-50/80">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-5 mb-7">
                {[
                  { label: 'Active Tasks', value: '12', sub: '3 running pipelines', color: 'text-orange-400' },
                  { label: 'Total Records', value: '48,290', sub: '+1,420 today', color: 'text-cyan-400' },
                  { label: 'Verified Sources', value: '1,842', sub: '99.2% reachability', color: 'text-violet-400' },
                  { label: 'Clean Datasets', value: '34', sub: 'Ready for export', color: 'text-emerald-400' },
                ].map((stat) => (
                  <div key={stat.label} className="p-4 sm:p-5 rounded-xl bg-white border border-black/6 shadow-sm">
                    <p className="text-[10px] sm:text-[11px] font-semibold text-dp-text-muted uppercase tracking-wider mb-1 truncate">{stat.label}</p>
                    <p className={`text-xl sm:text-2xl font-bold font-display ${stat.color}`}>{stat.value}</p>
                    <p className="text-[10px] text-dp-text-muted mt-1 truncate">{stat.sub}</p>
                  </div>
                ))}
              </div>

              {/* Extraction Speed Bar Chart */}
              <div className="p-5 sm:p-6 rounded-xl bg-white border border-black/6 shadow-sm w-full overflow-hidden">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-dp-accent" />
                    <span className="text-xs sm:text-sm font-semibold text-dp-text">Extraction Throughput & Speed</span>
                  </div>
                  <span className="text-[10px] font-mono text-dp-text-muted bg-black/5 px-2 py-0.5 rounded">Live Stream</span>
                </div>
                <div className="h-40 sm:h-48 flex items-end justify-between gap-1.5 sm:gap-2.5 pt-4 px-2 border-b border-black/8 w-full">
                  {[35, 55, 42, 78, 65, 92, 70, 88, 60, 95, 82, 100].map((height, i) => (
                    <div key={i} className="flex-1 flex flex-col justify-end items-center h-full group">
                      <div 
                        className="w-full bg-gradient-to-t from-dp-accent/20 via-dp-accent/60 to-dp-accent rounded-t transition-all duration-300 group-hover:brightness-125"
                        style={{ height: `${height}%` }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Task 5: Statistics Bar Section ── */}
      <section id="metrics" className="w-full py-16 sm:py-20 border-y border-black/8 bg-slate-50 flex justify-center">
        <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 sm:gap-12 text-center">
            {METRICS.map((metric) => (
              <div key={metric.label} className="space-y-1">
                <p className="text-2xl sm:text-4xl font-extrabold text-dp-text font-display text-gradient-orange">{metric.value}</p>
                <p className="text-xs sm:text-sm font-medium text-dp-text">{metric.label}</p>
                <p className="text-[11px] text-dp-text-muted">{metric.trend}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Task 5: How It Works Section ── */}
      <section id="how-it-works" className="w-full py-24 sm:py-32 px-4 sm:px-6 lg:px-8 z-10 flex flex-col items-center">
        <div className="w-full max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16 sm:mb-20">
            <span className="text-xs font-bold uppercase tracking-wider text-dp-accent bg-dp-accent/10 px-3 py-1 rounded-full border border-dp-accent/20">Workflow Architecture</span>
            <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-dp-text tracking-tight mt-4 mb-5 font-display">
              Four Steps from Prompt to Dataset
            </h2>
            <p className="text-dp-text-secondary text-sm sm:text-base leading-relaxed">
              DataPilot AI handles source discovery, scraping, field normalization, standardizing, and deduplication.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-7 w-full">
            {STEPS.map((step) => {
              const Icon = step.icon;
              return (
                <div 
                  key={step.title}
                  className="group relative p-7 sm:p-8 rounded-2xl glass-panel glass-panel-hover flex flex-col justify-between min-h-[220px]"
                >
                  <div className="flex items-center justify-between mb-8">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-dp-accent/20 to-orange-500/10 border border-dp-accent/30 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Icon className="w-6 h-6 text-dp-accent" />
                    </div>
                    <span className="text-xs font-mono font-bold text-dp-text-muted bg-black/4 px-2.5 py-1 rounded-md border border-black/8">{step.step}</span>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold text-dp-accent uppercase tracking-wider">{step.subtitle}</span>
                    <h3 className="text-base sm:text-lg font-bold text-dp-text mt-2 mb-3 font-display">{step.title}</h3>
                    <p className="text-sm text-dp-text-secondary leading-relaxed">{step.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Task 5: Features Section ── */}
      <section id="features" className="w-full py-24 sm:py-32 px-4 sm:px-6 lg:px-8 bg-slate-50 border-t border-black/6 z-10 flex flex-col items-center">
        <div className="w-full max-w-6xl mx-auto">
          <div className="text-center max-w-2xl mx-auto mb-16 sm:mb-20">
            <span className="text-xs font-bold uppercase tracking-wider text-violet-400 bg-violet-500/10 px-3 py-1 rounded-full border border-violet-500/20">Capabilities</span>
            <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-dp-text tracking-tight mt-4 mb-5 font-display">
              Enterprise-Grade Platform Features
            </h2>
            <p className="text-dp-text-secondary text-sm sm:text-base leading-relaxed">
              Built with FastAPI async backend, Motor MongoDB driver, and React TypeScript frontend.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-7 w-full">
            {FEATURES.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="p-7 sm:p-8 rounded-2xl glass-panel glass-panel-hover flex flex-col justify-between group min-h-[200px]"
                >
                  <div>
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.color} border border-black/8 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <h3 className="text-base font-bold text-dp-text mb-3 font-display">{feature.title}</h3>
                    <p className="text-sm text-dp-text-secondary leading-relaxed">{feature.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Task 5: CTA Banner Section ── */}
      <section className="w-full py-24 sm:py-32 px-4 sm:px-6 lg:px-8 z-10 flex flex-col items-center">
        <div className="w-full max-w-5xl mx-auto relative rounded-3xl overflow-hidden bg-gradient-to-br from-orange-50 via-white to-violet-50 border border-orange-100 shadow-lg p-10 sm:p-16 lg:p-20 text-center flex flex-col items-center">
          <div className="absolute inset-0 bg-gradient-to-r from-orange-500/5 via-violet-500/5 to-amber-500/5 pointer-events-none" />
          
          <div className="relative z-10 max-w-2xl mx-auto flex flex-col items-center text-center">
            <h2 className="text-2xl sm:text-4xl lg:text-5xl font-extrabold text-dp-text tracking-tight mb-6 font-display">
              Ready to Collect Data in Minutes?
            </h2>
            <p className="text-dp-text-secondary text-sm sm:text-base mb-10 leading-relaxed">
              Experience prompt-driven autonomous data extraction. No web scrapers to configure, no manual formatting required.
            </p>
            <div className="flex items-center justify-center gap-4 flex-wrap w-full">
              <Button
                size="lg"
                icon={<ArrowRight className="w-5 h-5" />}
                iconPosition="right"
                onClick={() => navigate('/new-task')}
                className="bg-gradient-to-r from-dp-accent to-orange-500 text-white font-bold px-8 py-3.5 text-base shadow-glow-strong btn-glow-accent rounded-xl"
              >
                Create Your First Task
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Task 5: Footer ── */}
      <footer className="w-full border-t border-black/8 py-12 sm:py-16 px-4 sm:px-6 lg:px-8 bg-white z-10 flex justify-center">
        <div className="w-full max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-dp-text-muted">
          <div className="flex items-center gap-4">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-dp-accent to-orange-500 flex items-center justify-center">
              <Compass className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-dp-text font-display">DataPilot AI</span>
            <span className="text-xs text-dp-text-muted">© 2026. All rights reserved.</span>
          </div>

          <div className="flex items-center gap-8 text-sm text-dp-text-secondary flex-wrap justify-center">
            <button onClick={() => navigate('/dashboard')} className="hover:text-dp-text transition-colors">Dashboard</button>
            <button onClick={() => navigate('/new-task')} className="hover:text-dp-text transition-colors">New Task</button>
            <button onClick={() => navigate('/datasets')} className="hover:text-dp-text transition-colors">Datasets</button>
            <button onClick={() => navigate('/analytics')} className="hover:text-dp-text transition-colors">Analytics</button>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
