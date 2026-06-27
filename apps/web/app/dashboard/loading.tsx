import { DashboardLoadingSkeleton } from '@/components/loading-skeleton';

export default function DashboardLoading() {
  return (
    <main className="app-shell min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <section className="mx-auto max-w-7xl">
        <DashboardLoadingSkeleton />
      </section>
    </main>
  );
}
