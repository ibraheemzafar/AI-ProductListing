'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';

export default function ListingDetailError({ reset }: { reset: () => void }) {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto max-w-3xl rounded-md border border-border p-8 text-center">
        <h1 className="text-2xl font-semibold">Listing detail could not load</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The listing may be unavailable, or the API server may be offline.
        </p>
        <div className="mt-5 flex justify-center gap-3">
          <Button type="button" onClick={reset}>
            Try again
          </Button>
          <Button asChild variant="secondary">
            <Link href="/dashboard">Back</Link>
          </Button>
        </div>
      </section>
    </main>
  );
}
