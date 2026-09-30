import React from 'react';
import { cn } from '@/utils/cn';
import type { CardVariant } from '@/types';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: CardVariant;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  as?: React.ElementType;
}

const variantStyles: Record<CardVariant, string> = {
  default: [
    'bg-dp-bg-raised',
    'border border-dp-border',
  ].join(' '),
  elevated: [
    'bg-dp-bg-surface',
    'border border-dp-border',
    'shadow-card',
  ].join(' '),
  bordered: [
    'bg-dp-bg-raised',
    'border border-dp-border-hover',
  ].join(' '),
  accent: [
    'bg-dp-bg-raised',
    'border border-dp-border-accent',
  ].join(' '),
  interactive: [
    'bg-dp-bg-raised',
    'border border-dp-border',
    'hover:border-dp-border-hover hover:bg-dp-bg-surface',
    'hover:shadow-card-hover',
    'transition-all duration-200 ease-out',
    'cursor-pointer',
  ].join(' '),
};

const paddingStyles: Record<string, string> = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
};

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = 'default',
      padding = 'md',
      as: Component = 'div',
      className,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <Component
        ref={ref}
        className={cn(
          'rounded-[var(--radius-card)] min-w-0',
          variantStyles[variant],
          paddingStyles[padding],
          className
        )}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Card.displayName = 'Card';

/* ── Card Sub-components ── */

interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  title,
  description,
  action,
  className,
  ...props
}) => (
  <div className={cn('flex items-start justify-between gap-4 mb-4', className)} {...props}>
    <div className="min-w-0">
      <h3 className="text-base font-semibold text-dp-text truncate">{title}</h3>
      {description && (
        <p className="text-sm text-dp-text-secondary mt-1">{description}</p>
      )}
    </div>
    {action && <div className="shrink-0">{action}</div>}
  </div>
);

CardHeader.displayName = 'CardHeader';

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn('', className)} {...props}>
    {children}
  </div>
);

CardContent.displayName = 'CardContent';

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn(
      'flex items-center gap-3 mt-4 pt-4 border-t border-dp-border',
      className
    )}
    {...props}
  >
    {children}
  </div>
);

CardFooter.displayName = 'CardFooter';

export default Card;
