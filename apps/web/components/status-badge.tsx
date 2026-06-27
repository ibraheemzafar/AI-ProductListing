import { cn } from '@/lib/utils';

export type ListingDisplayStatus = 'draft' | 'generated' | 'optimized' | 'exported';

const statusStyles: Record<ListingDisplayStatus, string> = {
  draft: 'border-white/10 bg-white/[0.06] text-muted-foreground',
  generated: 'border-primary/35 bg-primary/15 text-white',
  optimized: 'border-accent/35 bg-accent/15 text-accent',
  exported: 'border-emerald-300/30 bg-emerald-300/10 text-emerald-100',
};

const statusLabels: Record<ListingDisplayStatus, string> = {
  draft: 'Draft',
  generated: 'Generated',
  optimized: 'Optimized',
  exported: 'Exported',
};

export function mapListingStatus(status: string): ListingDisplayStatus {
  const normalized = status.toLowerCase();
  if (normalized.includes('export')) {
    return 'exported';
  }
  if (normalized.includes('optim')) {
    return 'optimized';
  }
  if (normalized.includes('complete') || normalized.includes('generated') || normalized.includes('success')) {
    return 'generated';
  }
  return 'draft';
}

export function StatusBadge({ status }: { status: string | ListingDisplayStatus }) {
  const displayStatus = isDisplayStatus(status) ? status : mapListingStatus(status);

  return (
    <span
      className={cn(
        'inline-flex h-7 items-center rounded-full border px-2.5 text-xs font-semibold',
        statusStyles[displayStatus],
      )}
    >
      {statusLabels[displayStatus]}
    </span>
  );
}

function isDisplayStatus(status: string): status is ListingDisplayStatus {
  return ['draft', 'generated', 'optimized', 'exported'].includes(status);
}
