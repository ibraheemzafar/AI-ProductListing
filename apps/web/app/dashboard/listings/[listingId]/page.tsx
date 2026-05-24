import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';

import { ListingDetailView } from './listing-detail-view';
import { DashboardShell } from '@/components/dashboard-shell';
import { Button } from '@/components/ui/button';
import { getCurrentSession } from '@/lib/api/auth';
import { getListingDetail } from '@/lib/api/listing-history';

interface ListingDetailPageProps {
  params: Promise<{
    listingId: string;
  }>;
}

export default async function ListingDetailPage({ params }: ListingDetailPageProps) {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  const { listingId } = await params;

  try {
    const listing = await getListingDetail(listingId);
    return (
      <DashboardShell
        actions={
          <Button asChild variant="secondary">
            <Link href="/dashboard">Back to listings</Link>
          </Button>
        }
        description="Review generated copy, run SEO analysis, create improved versions, and build product image variants."
        email={session.user.email}
        eyebrow="Listing detail"
        title={listing.listing.title}
      >
        <ListingDetailView listing={listing} />
      </DashboardShell>
    );
  } catch (error) {
    if (error instanceof Error && error.message === 'Generated listing was not found') {
      notFound();
    }
    throw error;
  }
}
