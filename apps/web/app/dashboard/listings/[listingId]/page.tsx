import { notFound, redirect } from 'next/navigation';

import { ListingDetailView } from './listing-detail-view';
import { DashboardShell } from '@/components/dashboard-shell';
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
        description="Review Product Intelligence, Listing Studio copy, Creative Studio images, marketplace assets, marketing, and versions in one organized workspace."
        email={session.user.email}
        eyebrow="AI Workspace"
        title="Product workspace"
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
