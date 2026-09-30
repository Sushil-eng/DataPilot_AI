import React from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  hint?: string;
  fullWidth?: boolean;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      label,
      error,
      hint,
      fullWidth = true,
      className,
      id,
      children,
      ...props
    },
    ref
  ) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={selectId}
            className="text-sm font-medium text-dp-text-secondary"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={cn(
              // Base
              'w-full h-10 px-3 pr-10 text-sm appearance-none',
              'bg-dp-bg-surface text-dp-text',
              'border rounded-[var(--radius-input)]',
              'transition-colors duration-200',
              // Focus
              'focus:outline-none focus:border-dp-accent/50 focus:ring-1 focus:ring-dp-accent/20',
              // States
              error
                ? 'border-dp-error/50 focus:border-dp-error focus:ring-dp-error/20'
                : 'border-dp-border hover:border-dp-border-hover',
              // Disabled
              props.disabled && 'opacity-50 cursor-not-allowed',
              className
            )}
            {...props}
          >
            {children}
          </select>
          <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-dp-text-muted">
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
        {error && (
          <p className="text-xs text-dp-error">{error}</p>
        )}
        {hint && !error && (
          <p className="text-xs text-dp-text-muted">{hint}</p>
        )}
      </div>
    );
  }
);

Select.displayName = 'Select';

export default Select;
