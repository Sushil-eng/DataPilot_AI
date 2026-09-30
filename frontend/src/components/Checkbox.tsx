import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '@/utils/cn';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, className, id, checked, ...props }, ref) => {
    const checkboxId = id || label?.toLowerCase().replace(/\s+/g, '-');

    return (
      <label
        htmlFor={checkboxId}
        className={cn(
          'flex items-center gap-2.5 cursor-pointer group w-fit',
          props.disabled && 'opacity-50 cursor-not-allowed',
          className
        )}
      >
        <div className="relative flex items-center justify-center w-5 h-5">
          <input
            type="checkbox"
            id={checkboxId}
            ref={ref}
            checked={checked}
            className="sr-only"
            {...props}
          />
          <div className={cn(
            'w-full h-full rounded border transition-all duration-200 flex items-center justify-center',
            checked
              ? 'bg-dp-accent border-dp-accent'
              : 'border-dp-border bg-dp-bg-surface group-hover:border-dp-border-hover'
          )}>
            <Check
              className={cn(
                'w-3.5 h-3.5 text-white transition-opacity duration-150',
                checked ? 'opacity-100' : 'opacity-0'
              )}
              strokeWidth={3}
            />
          </div>
        </div>
        {label && (
          <span className="text-sm text-dp-text select-none">
            {label}
          </span>
        )}
      </label>
    );
  }
);

Checkbox.displayName = 'Checkbox';

export default Checkbox;
