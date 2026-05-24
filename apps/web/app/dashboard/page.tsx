import Link from 'next/link';
import { redirect } from 'next/navigation';

import { LogoutButton } from './logout-button';
import { getCurrentSession } from '@/lib/api/auth';
import { getListingHistory } from '@/lib/api/listing-history';

export default async function DashboardPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  const history = await getListingHistory();

  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Dashboard</p>
            <h1 className="text-3xl font-semibold tracking-normal">Listing history</h1>
            <p className="mt-2 text-sm text-muted-foreground">{session.user.email}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link
              className="inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
              href="/dashboard/upload"
            >
              Upload images
            </Link>
            <LogoutButton />
          </div>
        </div>

        {history.listings.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            {history.listings.map((listing) => (
              <Link
                key={listing.id}
                className="grid gap-4 rounded-md border border-border p-3 transition-colors hover:bg-muted sm:grid-cols-[120px_minmax(0,1fr)]"
                href={`/dashboard/listings/${listing.id}`}
              >
                <img
                  alt={listing.image.originalFilename}
                  className="aspect-square w-full rounded object-cover sm:size-[120px]"
                  src={listing.image.imageUrl}
                />
                <div className="min-w-0">
                  <div className="flex items-center justify-between gap-3">
                    <h2 className="truncate text-base font-medium">{listing.title}</h2>
                    <span className="rounded bg-muted px-2 py-1 text-xs capitalize text-muted-foreground">
                      {listing.status}
                    </span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
                    {listing.shortDescription}
                  </p>
                  <p className="mt-4 text-xs text-muted-foreground">
                    {new Intl.DateTimeFormat('en', {
                      dateStyle: 'medium',
                      timeStyle: 'short',
                    }).format(new Date(listing.createdAt))}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-md border border-dashed border-border p-8 text-center">
            <h2 className="text-lg font-medium">No generated listings yet</h2>
            <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
              Upload a product image, analyze it, then generate a listing to see it here.
            </p>
            <Link
              className="mt-5 inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
              href="/dashboard/upload"
            >
              Upload images
            </Link>
          </div>
        )}
      </section>
    </main>
  );
}
