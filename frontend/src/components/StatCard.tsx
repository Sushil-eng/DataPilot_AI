import React from 'react';
import { Card } from '@/components/Card';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/utils/cn';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ElementType;
  trend?: string;
  trendContent?: React.ReactNode;
  trendDirection?: 'up' | 'down' | 'neutral';
  className?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon: Icon,
  trend,
  trendContent,
  trendDirection = 'neutral',
  className,
}) => {
  return (
    <Card variant="interactive" padding="md" className={cn("flex flex-col min-w-0 overflow-hidden", className)}>
      <div className="flex justify-between items-start gap-2 mb-4 min-w-0">
        <p className="text-sm font-medium text-dp-text-muted uppercase tracking-wider min-w-0 truncate">
          {label}
        </p>
        <div className="p-2 bg-dp-bg-surface rounded-lg shrink-0">
          <Icon className="w-5 h-5 text-dp-accent" />
        </div>
      </div>
      
      <div className="mt-auto min-w-0">
        <h3 className="text-3xl font-bold text-dp-text tracking-tight mb-2 truncate" title={String(value)}>
          {value}
        </h3>
        
        {/* Custom trend content (e.g. badges) */}
        {trendContent && (
          <div className="mt-2 min-w-0 overflow-hidden">
            {trendContent}
          </div>
        )}

        {/* Text-based trend */}
        {!trendContent && trend && (
          <div className="flex items-center gap-1.5 mt-2 min-w-0">
            {trendDirection === 'up' && <TrendingUp className="w-3.5 h-3.5 text-dp-success shrink-0" />}
            {trendDirection === 'down' && <TrendingDown className="w-3.5 h-3.5 text-dp-error shrink-0" />}
            <span className={cn(
              "text-xs font-medium truncate",
              trendDirection === 'up' ? "text-dp-success" : 
              trendDirection === 'down' ? "text-dp-error" : 
              "text-dp-text-muted"
            )} title={trend}>
              {trend}
            </span>
          </div>
        )}
      </div>
    </Card>
  );
};

