import React from 'react';
import { cn } from '@/utils/cn';
import type { BadgeVariant } from '@/types';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: 'bg-dp-bg-surface text-dp-text-secondary border-dp-border',
  success: 'bg-dp-success/10 text-dp-success border-dp-success/20',
  warning: 'bg-dp-warning/10 text-dp-warning border-dp-warning/20',
  error: 'bg-dp-error/10 text-dp-error border-dp-error/20',
  info: 'bg-dp-info/10 text-dp-info border-dp-info/20',
  accent: 'bg-dp-accent/10 text-dp-accent border-dp-accent/20',
};

const dotColors: Record<BadgeVariant, string> = {
  default: 'bg-dp-text-muted',
  success: 'bg-dp-success',
  warning: 'bg-dp-warning',
  error: 'bg-dp-error',
  info: 'bg-dp-info',
  accent: 'bg-dp-accent',
};

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  dot = false,
  className,
  children,
  ...props
}) => (
  <span
    className={cn(
      'inline-flex items-center gap-1.5',
      'px-2.5 py-0.5',
      'text-xs font-medium',
      'border rounded-[var(--radius-badge)]',
      variantStyles[variant],
      className
    )}
    {...props}
  >
    {dot && (
      <span className={cn('w-1.5 h-1.5 rounded-full shrink-0', dotColors[variant])} />
    )}
    {children}
  </span>
);

Badge.displayName = 'Badge';

export default Badge;
