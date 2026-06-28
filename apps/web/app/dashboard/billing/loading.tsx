import { LoadingSkeleton } from '@/components/loading-skeleton';

export default function BillingLoading() {
  return (
    <main className="app-shell min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <section className="mx-auto grid max-w-7xl gap-6">
        <LoadingSkeleton className="h-24" />
        <div className="grid gap-4 md:grid-cols-3">
          <LoadingSkeleton className="h-32" />
          <LoadingSkeleton className="h-32" />
          <LoadingSkeleton className="h-32" />
        </div>
        <LoadingSkeleton className="h-80" />
      </section>
    </main>
  );
}
