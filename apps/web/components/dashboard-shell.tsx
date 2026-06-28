import {
  BarChart3,
  ImagePlus,
  Sparkles,
  WandSparkles,
} from 'lucide-react';
import Link from 'next/link';
import { Suspense, type ReactNode } from 'react';

import { LogoutButton } from '@/app/dashboard/logout-button';
import { DashboardBrand, DashboardNav } from '@/components/dashboard-nav';
import { PageHeader } from '@/components/page-header';
import { WalletBalance } from '@/components/wallet-balance';
import { WelcomeCreditsToast } from '@/components/welcome-credits-toast';

interface DashboardShellProps {
  children: ReactNode;
  eyebrow: string;
  title: string;
  description?: string;
  email?: string;
  actions?: ReactNode;
}

export function DashboardShell({
  children,
  eyebrow,
  title,
  description,
  email,
  actions,
}: DashboardShellProps) {
  return (
    <div className="app-shell min-h-screen lg:grid lg:grid-cols-[280px_minmax(0,1fr)]">
      <Suspense fallback={null}>
        <WelcomeCreditsToast />
      </Suspense>
      <aside className="hidden border-r border-white/10 bg-background/60 px-4 py-5 backdrop-blur-xl lg:block">
        <DashboardBrand />
        <DashboardNav />
        <div className="mt-8 rounded-lg border border-primary/20 bg-primary/10 p-4 shadow-[0_20px_80px_-60px_hsl(var(--primary))]">
          <WandSparkles className="size-5 text-primary" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium">AI Commerce Workspace</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Upload one product image, generate commerce assets, and review every studio output.
          </p>
        </div>
      </aside>

      <main className="min-w-0">
        <header className="sticky top-0 z-30 border-b border-white/10 bg-background/72 backdrop-blur-xl">
          <div className="flex min-h-16 items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
            <div className="flex min-w-0 items-center gap-3 lg:hidden">
              <Link className="flex items-center gap-2 font-semibold" href="/">
                <Sparkles className="size-5 text-primary" aria-hidden="true" />
                CatalogAI
              </Link>
            </div>
            <div className="hidden min-w-0 text-sm text-muted-foreground lg:block">
              {email ? email : 'AI commerce workspace'}
            </div>
            <div className="flex items-center gap-2">
              <WalletBalance />
              <Link
                className="hidden h-10 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.05] px-3 text-sm font-semibold text-foreground transition hover:-translate-y-0.5 hover:bg-white/10 sm:inline-flex"
                href="/dashboard/upload"
              >
                <ImagePlus className="size-4" aria-hidden="true" />
                Product Intake
              </Link>
              <LogoutButton />
            </div>
          </div>
          <div className="border-t border-white/10 lg:hidden">
            <DashboardNav mobile />
          </div>
        </header>

        <div className="page-container">
          <PageHeader actions={actions} description={description} eyebrow={eyebrow} title={title} />
          {children}
        </div>
      </main>
    </div>
  );
}

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
}: {
  label: string;
  value: string;
  detail: string;
  icon: typeof BarChart3;
}) {
  return (
    <div className="premium-card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
        </div>
        <span className="flex size-10 items-center justify-center rounded-md bg-primary/15 text-primary">
          <Icon className="size-5" aria-hidden="true" />
        </span>
      </div>
      <p className="mt-4 text-xs text-muted-foreground">{detail}</p>
    </div>
  );
}
