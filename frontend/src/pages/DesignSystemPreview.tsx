import React from 'react';
import {
  Database,
  ArrowRight,
  Sparkles,
  Search,
  Settings,
  Zap,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Info,
  Plus,
  Download,
  Trash2,
  Mail,
} from 'lucide-react';
import { Button, Card, CardHeader, CardContent, CardFooter, Badge, Input } from '@/components';

/**
 * Design System Preview — showcases all components and tokens.
 * This page is for development only and will be replaced by actual pages.
 */
const DesignSystemPreview: React.FC = () => {
  return (
    <div className="min-h-screen bg-dp-bg">
      {/* ── Header ── */}
      <header className="border-b border-dp-border bg-dp-bg-raised/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-dp-accent/20 flex items-center justify-center">
              <Database className="w-4 h-4 text-dp-accent" />
            </div>
            <span className="text-lg font-bold text-dp-text tracking-tight">
              DataPilot <span className="text-dp-accent">AI</span>
            </span>
          </div>
          <p className="text-sm text-dp-text-muted hidden sm:block">
            Design System Preview
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-12 space-y-16">
        {/* ── Hero ── */}
        <section className="text-center space-y-4">
          <h1 className="text-4xl sm:text-5xl font-bold text-dp-text tracking-tight">
            DataPilot <span className="text-gradient-accent">AI</span>
          </h1>
          <p className="text-lg text-dp-text-secondary max-w-xl mx-auto">
            Turn business questions into actionable datasets.
          </p>
        </section>

        {/* ── Color Palette ── */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-dp-text">Color Palette</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            {[
              { name: 'Background', color: 'bg-dp-bg', text: '#0a0a0f' },
              { name: 'Raised', color: 'bg-dp-bg-raised', text: '#111118' },
              { name: 'Surface', color: 'bg-dp-bg-surface', text: '#16161f' },
              { name: 'Overlay', color: 'bg-dp-bg-overlay', text: '#1c1c27' },
              { name: 'Accent', color: 'bg-dp-accent', text: '#f97316' },
              { name: 'Accent Hover', color: 'bg-dp-accent-hover', text: '#fb923c' },
            ].map((swatch) => (
              <div key={swatch.name} className="space-y-2">
                <div
                  className={`h-16 rounded-lg border border-dp-border ${swatch.color}`}
                />
                <div>
                  <p className="text-xs font-medium text-dp-text">{swatch.name}</p>
                  <p className="text-2xs text-dp-text-muted font-mono">{swatch.text}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Typography ── */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-dp-text">Typography</h2>
          <Card variant="bordered" padding="lg">
            <div className="space-y-4">
              <p className="text-4xl font-bold text-dp-text tracking-tight">Heading 1 — 2.25rem Bold</p>
              <p className="text-2xl font-semibold text-dp-text">Heading 2 — 1.5rem Semibold</p>
              <p className="text-xl font-semibold text-dp-text">Heading 3 — 1.25rem Semibold</p>
              <p className="text-base text-dp-text">Body — 1rem Regular</p>
              <p className="text-sm text-dp-text-secondary">Secondary — 0.875rem</p>
              <p className="text-xs text-dp-text-muted">Muted — 0.75rem</p>
              <p className="text-sm font-mono text-dp-accent">Monospace — JetBrains Mono</p>
            </div>
          </Card>
        </section>

        {/* ── Buttons ── */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-dp-text">Buttons</h2>

          {/* Variants */}
          <div className="space-y-3">
            <p className="text-sm text-dp-text-secondary font-medium">Variants</p>
            <div className="flex flex-wrap gap-3">
              <Button variant="primary" icon={<Sparkles className="w-4 h-4" />}>
                Primary
              </Button>
              <Button variant="secondary" icon={<Settings className="w-4 h-4" />}>
                Secondary
              </Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="outline" icon={<Zap className="w-4 h-4" />}>
                Outline
              </Button>
              <Button variant="danger" icon={<Trash2 className="w-4 h-4" />}>
                Danger
              </Button>
            </div>
          </div>

          {/* Sizes */}
          <div className="space-y-3">
            <p className="text-sm text-dp-text-secondary font-medium">Sizes</p>
            <div className="flex flex-wrap items-center gap-3">
              <Button size="sm">Small</Button>
              <Button size="md">Medium</Button>
              <Button size="lg">Large</Button>
            </div>
          </div>

          {/* States */}
          <div className="space-y-3">
            <p className="text-sm text-dp-text-secondary font-medium">States</p>
            <div className="flex flex-wrap gap-3">
              <Button loading>Loading</Button>
              <Button disabled>Disabled</Button>
              <Button icon={<Plus className="w-4 h-4" />}>With Icon</Button>
              <Button icon={<ArrowRight className="w-4 h-4" />} iconPosition="right">
                Icon Right
              </Button>
              <Button variant="secondary" icon={<Download className="w-4 h-4" />}>
                Download
              </Button>
            </div>
          </div>
        </section>

        {/* ── Cards ── */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-dp-text">Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Card variant="default">
              <CardHeader title="Default Card" description="Standard background with subtle border." />
              <CardContent>
                <p className="text-sm text-dp-text-secondary">
                  Use for general content containers and sections.
                </p>
              </CardContent>
            </Card>

            <Card variant="elevated">
              <CardHeader title="Elevated Card" description="Raised surface with shadow depth." />
              <CardContent>
                <p className="text-sm text-dp-text-secondary">
                  Use for content that needs visual prominence.
                </p>
              </CardContent>
            </Card>

            <Card variant="interactive">
              <CardHeader
                title="Interactive Card"
                description="Hover to see the transition effect."
              />
              <CardContent>
                <p className="text-sm text-dp-text-secondary">
                  Use for clickable cards, list items, and navigable surfaces.
                </p>
              </CardContent>
            </Card>

            <Card variant="accent">
              <CardHeader
                title="Accent Card"
                description="Orange accent border for emphasis."
                action={<Badge variant="accent">New</Badge>}
              />
              <CardContent>
                <p className="text-sm text-dp-text-secondary">
                  Use for featured or highlighted content sections.
                </p>
              </CardContent>
              <CardFooter>
                <Button size="sm" variant="ghost">Learn More</Button>
                <Button size="sm">Get Started</Button>
              </CardFooter>
            </Card>

            <Card variant="bordered">
              <CardHeader title="Bordered Card" description="Stronger border visibility." />
              <CardContent>
                <p className="text-sm text-dp-text-secondary">
                  Use when cards need clear visual separation.
                </p>
              </CardContent>
            </Card>

            <Card variant="default" className="card-glow">
              <CardHeader
                title="Glow Effect"
                description="Hover for a subtle accent glow."
                action={<Badge variant="accent" dot>Live</Badge>}
              />
              <CardContent>
                <p className="text-sm text-dp-text-secondary">
                  Add <code className="text-xs font-mono text-dp-accent bg-dp-accent/10 px-1.5 py-0.5 rounded">card-glow</code> class for the effect.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* ── Badges ── */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-dp-text">Badges</h2>
          <Card variant="bordered">
            <div className="space-y-4">
              <div className="space-y-2">
                <p className="text-sm text-dp-text-secondary font-medium">Variants</p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="default">Default</Badge>
                  <Badge variant="success">Success</Badge>
                  <Badge variant="warning">Warning</Badge>
                  <Badge variant="error">Error</Badge>
                  <Badge variant="info">Info</Badge>
                  <Badge variant="accent">Accent</Badge>
                </div>
              </div>
              <div className="space-y-2">
                <p className="text-sm text-dp-text-secondary font-medium">With Status Dot</p>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="success" dot>Connected</Badge>
                  <Badge variant="warning" dot>Syncing</Badge>
                  <Badge variant="error" dot>Offline</Badge>
                  <Badge variant="info" dot>Processing</Badge>
                  <Badge variant="accent" dot>AI Active</Badge>
                </div>
              </div>
            </div>
          </Card>
        </section>

        {/* ── Inputs ── */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-dp-text">Inputs</h2>
          <Card variant="bordered" padding="lg">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Input
                label="Search datasets"
                placeholder="Type to search..."
                icon={<Search className="w-4 h-4" />}
              />
              <Input
                label="Email address"
                placeholder="you@company.com"
                type="email"
                icon={<Mail className="w-4 h-4" />}
              />
              <Input
                label="With error"
                placeholder="Enter value"
                error="This field is required"
                defaultValue=""
              />
              <Input
                label="With hint"
                placeholder="api_key_xxxxx"
                hint="Your API key can be found in Settings."
                icon={<Settings className="w-4 h-4" />}
              />
            </div>
          </Card>
        </section>

        {/* ── Semantic Colors ── */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-dp-text">Semantic Colors</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {[
              { icon: CheckCircle, label: 'Success', color: 'text-dp-success', bg: 'bg-dp-success/10' },
              { icon: AlertTriangle, label: 'Warning', color: 'text-dp-warning', bg: 'bg-dp-warning/10' },
              { icon: XCircle, label: 'Error', color: 'text-dp-error', bg: 'bg-dp-error/10' },
              { icon: Info, label: 'Info', color: 'text-dp-info', bg: 'bg-dp-info/10' },
            ].map(({ icon: Icon, label, color, bg }) => (
              <Card key={label} variant="default" padding="sm">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center`}>
                    <Icon className={`w-5 h-5 ${color}`} />
                  </div>
                  <div>
                    <p className={`text-sm font-medium ${color}`}>{label}</p>
                    <p className="text-xs text-dp-text-muted">Semantic color</p>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </section>

        {/* ── Footer ── */}
        <footer className="border-t border-dp-border pt-8 pb-12 text-center">
          <p className="text-sm text-dp-text-muted">
            DataPilot AI — Design System v1.0
          </p>
        </footer>
      </main>
    </div>
  );
};

export default DesignSystemPreview;
