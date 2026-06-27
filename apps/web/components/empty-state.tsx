import type { ComponentType, ReactNode } from 'react';

interface EmptyStateProps {
  icon: ComponentType<{ className?: string }>;
  title: string;
  description: string;
  action?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <section className="glass-panel px-6 py-12 text-center">
      <span className="mx-auto flex size-14 items-center justify-center rounded-lg bg-primary/15 text-primary">
        <Icon className="size-7" aria-hidden="true" />
      </span>
      <h2 className="mx-auto mt-5 max-w-xl text-xl font-semibold text-white">{title}</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted-foreground">
        {description}
      </p>
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </section>
  );
}
