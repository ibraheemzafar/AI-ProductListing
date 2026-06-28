'use client';

import { AlertTriangle } from 'lucide-react';

import { EmptyState } from '@/components/empty-state';
import { Button } from '@/components/ui/button';

export default function DashboardError({ reset }: { reset: () => void }) {
  return (
    <main className="app-shell min-h-screen px-4 py-10 sm:px-6 lg:px-8">
      <section className="mx-auto max-w-3xl">
        <EmptyState
          icon={AlertTriangle}
          title="Workspace History could not load"
          description="Check that the API server is running, then try again."
          action={
            <Button type="button" onClick={reset}>
              Try again
            </Button>
          }
        />
      </section>
    </main>
  );
}
