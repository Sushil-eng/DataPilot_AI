import React from 'react';
import { cn } from '@/utils/cn';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      icon,
      iconPosition = 'left',
      fullWidth = true,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-semibold text-dp-text-secondary"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center w-full">
          {icon && iconPosition === 'left' && (
            <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-dp-text-muted pointer-events-none z-10 flex items-center justify-center">
              {icon}
            </span>
          )}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              // Base
              'w-full h-10 text-sm',
              'bg-dp-bg-surface text-dp-text',
              'border rounded-[var(--radius-input)]',
              'placeholder:text-dp-text-muted/70',
              'transition-colors duration-200',
              // Focus
              'focus:outline-none focus:border-dp-accent/50 focus:ring-1 focus:ring-dp-accent/20',
              // States
              error
                ? 'border-dp-error/50 focus:border-dp-error focus:ring-dp-error/20'
                : 'border-dp-border hover:border-dp-border-hover',
              // Dynamic Icon padding (avoids Tailwind px-3 overriding pl-10)
              icon && iconPosition === 'left'
                ? 'pl-10 pr-3'
                : icon && iconPosition === 'right'
                ? 'pl-3 pr-10'
                : 'px-3',
              // Disabled
              props.disabled && 'opacity-50 cursor-not-allowed',
              className
            )}
            {...props}
          />
          {icon && iconPosition === 'right' && (
            <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-dp-text-muted pointer-events-none z-10 flex items-center justify-center">
              {icon}
            </span>
          )}
        </div>
        {error && (
          <p className="text-xs text-dp-error mt-0.5">{error}</p>
        )}
        {hint && !error && (
          <p className="text-xs text-dp-text-muted mt-0.5">{hint}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
