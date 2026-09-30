import React from 'react';
import { cn } from '@/utils/cn';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  hint?: string;
  fullWidth?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      label,
      error,
      hint,
      fullWidth = true,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={textareaId}
            className="text-sm font-medium text-dp-text-secondary"
          >
            {label}
          </label>
        )}
        <div className="relative">
          <textarea
            ref={ref}
            id={textareaId}
            className={cn(
              // Base
              'w-full p-3 text-sm min-h-[120px] resize-y',
              'bg-dp-bg-surface text-dp-text',
              'border rounded-[var(--radius-input)]',
              'placeholder:text-dp-text-muted',
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
          />
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

Textarea.displayName = 'Textarea';

export default Textarea;
