import { type ClassValue, clsx } from 'clsx';

/**
 * Utility for conditionally joining classNames together.
 * Lightweight alternative to the full clsx+twMerge pattern.
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}
