import React from 'react';
import { Card } from '@/components/Card';
import { StatusBadge } from '@/components/StatusBadge';
import { Database, Globe2 } from 'lucide-react';
import { cn } from '@/utils/cn';

interface TaskCardProps {
  title: string;
  status: string;
  records?: number | null;
  sources?: number | null;
  progress?: number;
  className?: string;
}

export const TaskCard: React.FC<TaskCardProps> = ({
  title,
  status,
  records,
  sources,
  progress,
  className,
}) => {
  return (
    <Card variant="bordered" padding="md" className={cn("flex flex-col h-full hover:border-dp-border-hover transition-colors", className)}>
      <div className="flex justify-between items-start gap-4 mb-4">
        <h4 className="text-sm font-medium text-dp-text leading-snug line-clamp-2">
          {title}
        </h4>
        <StatusBadge status={status} className="shrink-0" />
      </div>
      
      <div className="mt-auto space-y-4">
        {/* Progress Bar (if running) */}
        {progress !== undefined && status.toLowerCase() === 'running' && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-dp-text-secondary">Progress</span>
              <span className="text-dp-accent font-medium">{progress}%</span>
            </div>
            <div className="w-full bg-dp-bg-surface h-1.5 rounded-full overflow-hidden">
              <div 
                className="bg-dp-accent h-full rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Stats Row */}
        <div className="flex items-center gap-4 text-xs text-dp-text-muted">
          {records !== undefined && records !== null && (
            <div className="flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5" />
              <span>{records.toLocaleString()} records</span>
            </div>
          )}
          {sources !== undefined && sources !== null && (
            <div className="flex items-center gap-1.5">
              <Globe2 className="w-3.5 h-3.5" />
              <span>{sources.toLocaleString()} sources</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
