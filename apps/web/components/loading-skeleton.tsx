import { cn } from '@/lib/utils';

export function LoadingSkeleton({ className }: { className?: string }) {
  return <div className={cn('skeleton', className)} />;
}

export function DashboardLoadingSkeleton() {
  return (
    <div className="grid gap-6">
      <LoadingSkeleton className="h-32" />
      <div className="grid gap-4 md:grid-cols-3">
        <LoadingSkeleton className="h-32" />
        <LoadingSkeleton className="h-32" />
        <LoadingSkeleton className="h-32" />
      </div>
      <LoadingSkeleton className="h-96" />
    </div>
  );
}
