import { LoadingSkeleton } from '@/components/loading-skeleton';

export default function UploadLoading() {
  return (
    <main className="app-shell min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <section className="mx-auto grid max-w-7xl gap-6">
        <LoadingSkeleton className="h-24" />
        <LoadingSkeleton className="h-80" />
        <LoadingSkeleton className="h-96" />
      </section>
    </main>
  );
}
