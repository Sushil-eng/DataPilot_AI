import React from 'react';
import { Badge } from '@/components/Badge';

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const normalizedStatus = status.toLowerCase();
  
  let variant: 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent' = 'default';
  
  if (['completed', 'ready', 'success'].includes(normalizedStatus)) {
    variant = 'success';
  } else if (['running', 'in progress', 'processing'].includes(normalizedStatus)) {
    variant = 'info';
  } else if (['failed', 'error'].includes(normalizedStatus)) {
    variant = 'error';
  } else if (['paused', 'archived'].includes(normalizedStatus)) {
    variant = 'warning';
  }

  return (
    <Badge variant={variant} dot className={className}>
      {status}
    </Badge>
  );
};
