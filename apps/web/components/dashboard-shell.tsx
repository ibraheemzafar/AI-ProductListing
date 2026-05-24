import { BarChart3, ImagePlus, LayoutDashboard, Sparkles, WandSparkles } from 'lucide-react';
import Link from 'next/link';
import type { ReactNode } from 'react';

import { LogoutButton } from '@/app/dashboard/logout-button';

interface DashboardShellProps {
  children: ReactNode;
  eyebrow: string;
  title: string;
  description?: string;
  email?: string;
  actions?: ReactNode;
}

const navigationItems = [
  { href: '/dashboard', label: 'Listings', icon: LayoutDashboard },
  { href: '/dashboard/upload', label: 'Upload', icon: ImagePlus },
];

export function DashboardShell({
  children,
  eyebrow,
  title,
  description,
  email,
  actions,
}: DashboardShellProps) {
  return (
    <div className="app-shell min-h-screen lg:grid lg:grid-cols-[272px_minmax(0,1fr)]">
      <aside className="hidden border-r border-white/10 bg-background/55 px-4 py-5 backdrop-blur-xl lg:block">
        <Link className="flex items-center gap-3 rounded-md px-3 py-2" href="/">
          <span className="flex size-10 items-center justify-center rounded-md bg-primary text-white">
            <Sparkles className="size-5" aria-hidden="true" />
          </span>
          <span>
            <span className="block text-sm font-semibold">CatalogAI</span>
            <span className="block text-xs text-muted-foreground">Listing studio</span>
          </span>
        </Link>
        <nav className="mt-8 grid gap-2">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                className="flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-muted-foreground transition hover:bg-white/8 hover:text-foreground"
                href={item.href}
              >
                <Icon className="size-4" aria-hidden="true" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="mt-8 rounded-lg border border-primary/20 bg-primary/10 p-4">
          <WandSparkles className="size-5 text-primary" aria-hidden="true" />
          <p className="mt-3 text-sm font-medium">AI workflow</p>
          <p className="mt-1 text-xs leading-5 text-muted-foreground">
            Analyze images, generate SEO copy, enhance visuals, and export marketplace-ready assets.
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
              {email ? email : 'AI product listing workspace'}
            </div>
            <div className="flex items-center gap-2">
              <Link
                className="hidden h-10 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.05] px-3 text-sm font-semibold text-foreground transition hover:bg-white/10 sm:inline-flex"
                href="/dashboard/upload"
              >
                <ImagePlus className="size-4" aria-hidden="true" />
                Upload
              </Link>
              <LogoutButton />
            </div>
          </div>
          <nav className="flex gap-2 overflow-x-auto border-t border-white/10 px-4 py-2 lg:hidden">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  className="inline-flex h-9 shrink-0 items-center gap-2 rounded-md px-3 text-sm font-medium text-muted-foreground hover:bg-white/8 hover:text-foreground"
                  href={item.href}
                >
                  <Icon className="size-4" aria-hidden="true" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </header>

        <div className="page-container">
          <section className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="eyebrow">{eyebrow}</p>
              <h1 className="mt-3 max-w-4xl text-3xl font-semibold tracking-normal text-white sm:text-4xl">
                {title}
              </h1>
              {description ? (
                <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">
                  {description}
                </p>
              ) : null}
            </div>
            {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
          </section>

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
