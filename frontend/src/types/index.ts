/* ── Button Variants ── */

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
export type ButtonSize = 'sm' | 'md' | 'lg';

/* ── Card Variants ── */

export type CardVariant = 'default' | 'elevated' | 'bordered' | 'accent' | 'interactive';

/* ── Badge Variants ── */

export type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'accent';

/* ── Status ── */

export type Status = 'idle' | 'loading' | 'success' | 'error';

/* ── Common Props ── */

export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  id?: string;
}
