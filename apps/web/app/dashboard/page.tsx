import { BarChart3, Clock3, ImagePlus, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { Button } from '@/components/ui/button';
import { DashboardShell, MetricCard } from '@/components/dashboard-shell';
import { MotionView } from '@/components/motion-view';
import { getCurrentSession } from '@/lib/api/auth';
import { getListingHistory } from '@/lib/api/listing-history';

export default async function DashboardPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  const history = await getListingHistory();
  const completedCount = history.listings.filter(
    (listing) => listing.status === 'completed',
  ).length;

  return (
    <DashboardShell
      actions={
        <Button asChild>
          <Link href="/dashboard/upload">
            <ImagePlus className="size-4" aria-hidden="true" />
            Upload images
          </Link>
        </Button>
      }
      description="Monitor generated product listings, review recent output, and continue the image-to-marketplace workflow."
      email={session.user.email}
      eyebrow="Dashboard"
      title="Listing history"
    >
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          detail="Generated listing records in this workspace."
          icon={Sparkles}
          label="Total listings"
          value={String(history.listings.length)}
        />
        <MetricCard
          detail="Listings ready for review, copy, SEO, and export."
          icon={BarChart3}
          label="Completed"
          value={String(completedCount)}
        />
        <MetricCard
          detail="Latest generated listing activity."
          icon={Clock3}
          label="Latest"
          value={history.listings[0] ? 'Today' : 'None'}
        />
      </div>

      <section className="mt-8">
        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent listings</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Image-focused cards for quick review.
            </p>
          </div>
          <div className="flex min-w-0 gap-2">
            <input
              aria-label="Search listings"
              className="field-surface h-10 w-full min-w-0 sm:w-72"
              placeholder="Search listings"
              type="search"
            />
          </div>
        </div>

        {history.listings.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {history.listings.map((listing, index) => (
              <MotionView key={listing.id} delay={index * 0.04}>
                <Link
                  className="premium-card premium-card-hover group block h-full overflow-hidden"
                  href={`/dashboard/listings/${listing.id}`}
                >
                  <div className="relative">
                    <img
                      alt={listing.image.originalFilename}
                      className="aspect-[4/3] w-full object-cover transition duration-500 group-hover:scale-105"
                      src={listing.image.imageUrl}
                    />
                    <span className="absolute right-3 top-3 rounded-full border border-white/10 bg-background/70 px-3 py-1 text-xs font-semibold capitalize text-white backdrop-blur">
                      {listing.status}
                    </span>
                  </div>
                  <div className="p-4">
                    <h3 className="line-clamp-1 text-base font-semibold text-white">
                      {listing.title}
                    </h3>
                    <p className="mt-2 line-clamp-2 min-h-10 text-sm leading-5 text-muted-foreground">
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
              </MotionView>
            ))}
          </div>
        ) : (
          <div className="glass-panel px-6 py-14 text-center">
            <div className="mx-auto flex size-14 items-center justify-center rounded-lg bg-primary/15 text-primary">
              <ImagePlus className="size-7" aria-hidden="true" />
            </div>
            <h2 className="mt-5 text-xl font-semibold text-white">No generated listings yet</h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted-foreground">
              Upload a product image, analyze it, then generate a listing to see it here.
            </p>
            <Button asChild className="mt-6">
              <Link href="/dashboard/upload">Upload images</Link>
            </Button>
          </div>
        )}
      </section>
    </DashboardShell>
  );
}
