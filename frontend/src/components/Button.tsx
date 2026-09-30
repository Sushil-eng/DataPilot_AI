import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { ButtonVariant, ButtonSize } from '@/types';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    'bg-dp-accent text-white',
    'hover:bg-dp-accent-hover',
    'active:brightness-90',
    'shadow-sm hover:shadow-glow',
  ].join(' '),
  secondary: [
    'bg-dp-bg-surface text-dp-text',
    'border border-dp-border',
    'hover:bg-dp-bg-hover hover:border-dp-border-hover',
  ].join(' '),
  ghost: [
    'bg-transparent text-dp-text-secondary',
    'hover:bg-dp-bg-hover hover:text-dp-text',
  ].join(' '),
  danger: [
    'bg-dp-error/10 text-dp-error',
    'border border-dp-error/20',
    'hover:bg-dp-error/20 hover:border-dp-error/30',
  ].join(' '),
  outline: [
    'bg-transparent text-dp-accent',
    'border border-dp-accent/40',
    'hover:bg-dp-accent/10 hover:border-dp-accent/60',
  ].join(' '),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs gap-1.5 rounded-[var(--radius-button)]',
  md: 'h-10 px-4 text-sm gap-2 rounded-[var(--radius-button)]',
  lg: 'h-12 px-6 text-base gap-2.5 rounded-[var(--radius-button)]',
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      icon,
      iconPosition = 'left',
      fullWidth = false,
      disabled,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={cn(
          // Base
          'inline-flex items-center justify-center',
          'font-medium whitespace-nowrap',
          'transition-all duration-200 ease-out',
          'select-none cursor-pointer',
          'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-dp-accent',
          // Variant & Size
          variantStyles[variant],
          sizeStyles[size],
          // States
          fullWidth && 'w-full',
          isDisabled && 'opacity-50 cursor-not-allowed pointer-events-none',
          className
        )}
        {...props}
      >
        {loading && (
          <Loader2 className="h-4 w-4 animate-spin shrink-0" />
        )}
        {!loading && icon && iconPosition === 'left' && (
          <span className="shrink-0">{icon}</span>
        )}
        {children}
        {!loading && icon && iconPosition === 'right' && (
          <span className="shrink-0">{icon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
