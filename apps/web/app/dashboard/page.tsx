import { BarChart3, Clock3, ImagePlus, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { redirect } from 'next/navigation';

import { ListingHistoryView, type DashboardListingItem } from './listing-history-view';
import { Button } from '@/components/ui/button';
import { DashboardShell, MetricCard } from '@/components/dashboard-shell';
import { getCurrentSession } from '@/lib/api/auth';
import { getListingDetail, getListingHistory } from '@/lib/api/listing-history';

export default async function DashboardPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  const history = await getListingHistory();
  const listings = await enrichListingsWithCategory(history.listings);
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
      description="Scan generated listings, filter by status, and open a focused AI workspace for each product."
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
          value={history.listings[0] ? formatRelativeDate(history.listings[0].createdAt) : 'None'}
        />
      </div>

      <div className="mt-8">
        <ListingHistoryView listings={listings} />
      </div>
    </DashboardShell>
  );
}

async function enrichListingsWithCategory(
  listings: Awaited<ReturnType<typeof getListingHistory>>['listings'],
): Promise<DashboardListingItem[]> {
  return Promise.all(
    listings.map(async (listing) => {
      try {
        const detail = await getListingDetail(listing.id);
        return {
          ...listing,
          category: detail.analysis.category || 'Uncategorized',
        };
      } catch {
        return {
          ...listing,
          category: 'Uncategorized',
        };
      }
    }),
  );
}

function formatRelativeDate(value: string) {
  const date = new Date(value);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return 'Today';
  }
  return new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric' }).format(date);
}
