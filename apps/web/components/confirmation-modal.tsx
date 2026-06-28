'use client';

import type { ReactNode } from 'react';

import { Button } from '@/components/ui/button';

interface ConfirmationModalProps {
  title: string;
  description: string;
  confirmLabel: string;
  isConfirming?: boolean;
  errorMessage?: string | null;
  onCancel: () => void;
  onConfirm: () => void;
  children?: ReactNode;
}

export function ConfirmationModal({
  title,
  description,
  confirmLabel,
  isConfirming = false,
  errorMessage,
  onCancel,
  onConfirm,
  children,
}: ConfirmationModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirmation-modal-title"
    >
      <section className="w-full max-w-md rounded-lg border border-white/10 bg-background p-5 shadow-2xl">
        <h2 id="confirmation-modal-title" className="text-lg font-semibold text-white">
          {title}
        </h2>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{description}</p>
        <p className="mt-3 rounded-md border border-red-400/25 bg-red-500/10 px-3 py-2 text-sm font-medium text-red-100">
          This action cannot be undone.
        </p>
        {children ? <div className="mt-4">{children}</div> : null}
        {errorMessage ? (
          <p className="mt-4 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
            {errorMessage}
          </p>
        ) : null}
        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onCancel} disabled={isConfirming}>
            Cancel
          </Button>
          <Button type="button" onClick={onConfirm} disabled={isConfirming}>
            {isConfirming ? 'Deleting' : confirmLabel}
          </Button>
        </div>
      </section>
    </div>
  );
}
