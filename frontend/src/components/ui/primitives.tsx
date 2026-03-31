import { type ComponentPropsWithoutRef, type ReactNode } from 'react'

export function Button({ className = '', ...props }: ComponentPropsWithoutRef<'button'>) {
  return (
    <button
      className={[
        'inline-flex items-center justify-center gap-2 rounded-full border border-transparent px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50',
        'bg-[var(--accent)] text-white shadow-[0_10px_24px_rgba(198,93,46,0.22)] hover:bg-[var(--accent-strong)]',
        className,
      ].join(' ')}
      {...props}
    />
  )
}

export function GhostButton({ className = '', ...props }: ComponentPropsWithoutRef<'button'>) {
  return (
    <button
      className={[
        'inline-flex items-center justify-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition focus:outline-none focus:ring-2 focus:ring-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50',
        'border-[var(--border)] bg-white/60 text-[var(--foreground)] hover:bg-white',
        className,
      ].join(' ')}
      {...props}
    />
  )
}

export function Input({ className = '', ...props }: ComponentPropsWithoutRef<'input'>) {
  return (
    <input
      className={[
        'w-full rounded-2xl border px-4 py-3 text-sm outline-none transition',
        'border-[var(--border)] bg-white/80 text-[var(--foreground)] placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:bg-white',
        className,
      ].join(' ')}
      {...props}
    />
  )
}

export function Textarea({ className = '', ...props }: ComponentPropsWithoutRef<'textarea'>) {
  return (
    <textarea
      className={[
        'w-full rounded-3xl border px-4 py-3 text-sm outline-none transition',
        'border-[var(--border)] bg-white/85 text-[var(--foreground)] placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:bg-white',
        className,
      ].join(' ')}
      {...props}
    />
  )
}

export function Badge({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]',
        'border-[var(--border)] bg-[var(--accent-soft)] text-[var(--accent-strong)]',
        className,
      ].join(' ')}
    >
      {children}
    </span>
  )
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <section
      className={[
        'rounded-[28px] border p-5 backdrop-blur-sm',
        'border-[var(--border)] bg-[var(--panel)] shadow-[var(--shadow)]',
        className,
      ].join(' ')}
    >
      {children}
    </section>
  )
}

export function Separator({ className = '' }: { className?: string }) {
  return <div className={['h-px w-full bg-[var(--border)]', className].join(' ')} />
}
