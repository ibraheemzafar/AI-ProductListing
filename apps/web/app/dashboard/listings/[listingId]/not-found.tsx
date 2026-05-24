import Link from 'next/link';

export default function ListingDetailNotFound() {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto max-w-3xl rounded-md border border-border p-8 text-center">
        <h1 className="text-2xl font-semibold">Listing not found</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This listing does not exist or is not available for your account.
        </p>
        <Link
          className="mt-5 inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
          href="/dashboard"
        >
          Back to dashboard
        </Link>
      </section>
    </main>
  );
}
