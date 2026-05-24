'use client';

import { Button } from '@/components/ui/button';

export default function AppError({ reset }: { error: Error; reset: () => void }) {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto max-w-3xl rounded-md border border-border p-8 text-center">
        <h1 className="text-2xl font-semibold">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The page could not load. Check that the API server is running, then try again.
        </p>
        <Button className="mt-5" type="button" onClick={reset}>
          Try again
        </Button>
      </section>
    </main>
  );
}
