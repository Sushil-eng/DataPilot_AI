import React from 'react';
import { cn } from '@/utils/cn';

interface ConfidenceBadgeProps {
  score: number;
  className?: string;
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({ score, className }) => {
  let colorClass = 'text-dp-success bg-dp-success/10 border-dp-success/20';
  
  if (score < 85) {
    colorClass = 'text-dp-error bg-dp-error/10 border-dp-error/20';
  } else if (score < 95) {
    colorClass = 'text-dp-warning bg-dp-warning/10 border-dp-warning/20';
  }

  return (
    <span className={cn(
      'inline-flex items-center justify-center px-2 py-0.5 text-xs font-medium border rounded-[var(--radius-badge)]',
      colorClass,
      className
    )}>
      {score}%
    </span>
  );
};
