'use client';

import { ArrowRight, Filter, ImagePlus, Search } from 'lucide-react';
import Link from 'next/link';
import { useMemo, useState } from 'react';

import type { ListingHistoryItem } from '@ai-product-listing/types';
import { EmptyState } from '@/components/empty-state';
import { MotionView } from '@/components/motion-view';
import { StatusBadge, type ListingDisplayStatus, mapListingStatus } from '@/components/status-badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

export interface DashboardListingItem extends ListingHistoryItem {
  category: string;
}

const statusFilters: Array<{ value: 'all' | ListingDisplayStatus; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'draft', label: 'Draft' },
  { value: 'generated', label: 'Generated' },
  { value: 'optimized', label: 'Optimized' },
  { value: 'exported', label: 'Exported' },
];

export function ListingHistoryView({ listings }: { listings: DashboardListingItem[] }) {
  const [query, setQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | ListingDisplayStatus>('all');

  const filteredListings = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return listings.filter((listing) => {
      const displayStatus = mapListingStatus(listing.status);
      const matchesStatus = statusFilter === 'all' || displayStatus === statusFilter;
      const matchesQuery =
        normalizedQuery.length === 0 ||
        listing.title.toLowerCase().includes(normalizedQuery) ||
        listing.shortDescription.toLowerCase().includes(normalizedQuery) ||
        listing.category.toLowerCase().includes(normalizedQuery);

      return matchesStatus && matchesQuery;
    });
  }, [listings, query, statusFilter]);

  if (listings.length === 0) {
    return (
      <EmptyState
        icon={ImagePlus}
        title="No product workflows yet"
        description="Upload a product image and generate AI commerce assets to see Workspace History here."
        action={
          <Button asChild>
          <Link href="/dashboard/upload">Start Product Intake</Link>
          </Button>
        }
      />
    );
  }

  return (
    <section className="grid gap-4">
      <div className="glass-panel p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Recent workflows</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Search, filter, and open product launch workspaces.
            </p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <label className="relative block min-w-0 sm:w-80">
              <Search
                className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />
              <input
                aria-label="Search workflows"
                className="field-surface h-10 w-full pl-9"
                placeholder="Search product, category, description"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
              />
            </label>
            <div className="flex gap-2 overflow-x-auto rounded-md border border-white/10 bg-background/45 p-1">
              {statusFilters.map((filter) => (
                <button
                  key={filter.value}
                  className={cn(
                    'inline-flex h-8 shrink-0 items-center gap-1.5 rounded px-3 text-xs font-semibold transition',
                    statusFilter === filter.value
                      ? 'bg-primary text-white'
                      : 'text-muted-foreground hover:bg-white/[0.06] hover:text-white',
                  )}
                  type="button"
                  onClick={() => setStatusFilter(filter.value)}
                >
                  <Filter className="size-3" aria-hidden="true" />
                  {filter.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {filteredListings.length > 0 ? (
        <div className="grid gap-3">
          {filteredListings.map((listing, index) => (
            <MotionView key={listing.id} delay={index * 0.035}>
              <article className="premium-card group overflow-hidden p-3 transition hover:-translate-y-0.5 hover:border-primary/35 hover:bg-secondary/90">
                <div className="grid gap-4 sm:grid-cols-[112px_minmax(0,1fr)_auto] sm:items-center">
                  <img
                    alt={listing.image.originalFilename}
                    className="aspect-[4/3] w-full rounded-md border border-white/10 object-cover sm:size-28"
                    src={listing.image.imageUrl}
                  />
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge status={listing.status} />
                      <span className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-xs text-muted-foreground">
                        {listing.category}
                      </span>
                    </div>
                    <h3 className="mt-3 line-clamp-1 text-base font-semibold text-white">
                      {listing.title}
                    </h3>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">
                      {listing.shortDescription}
                    </p>
                    <p className="mt-3 text-xs text-muted-foreground">
                      {formatDate(listing.createdAt)}
                    </p>
                  </div>
                  <Button asChild variant="secondary" className="w-full sm:w-auto">
                    <Link href={`/dashboard/listings/${listing.id}`}>
                      Open workspace
                      <ArrowRight className="size-4" aria-hidden="true" />
                    </Link>
                  </Button>
                </div>
              </article>
            </MotionView>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Search}
          title="No workflows match your filters"
          description="Try another search term or switch the status filter back to All."
        />
      )}
    </section>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}
