import Link from 'next/link';
import { notFound, redirect } from 'next/navigation';

import { ListingDetailView } from './listing-detail-view';
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
      <main className="min-h-screen px-6 py-10">
        <section className="mx-auto flex max-w-6xl flex-col gap-8">
          <div className="border-b border-border pb-6">
            <Link className="text-sm font-medium text-primary" href="/dashboard">
              Dashboard
            </Link>
            <h1 className="mt-2 text-3xl font-semibold tracking-normal">{listing.listing.title}</h1>
            <p className="mt-2 text-sm text-muted-foreground">{session.user.email}</p>
          </div>

          <ListingDetailView listing={listing} />
        </section>
      </main>
    );
  } catch (error) {
    if (error instanceof Error && error.message === 'Generated listing was not found') {
      notFound();
    }
    throw error;
  }
}
