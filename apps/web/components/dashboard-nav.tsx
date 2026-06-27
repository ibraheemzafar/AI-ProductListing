'use client';

import { ImagePlus, LayoutDashboard, Sparkles, type LucideIcon } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { cn } from '@/lib/utils';

const navigationItems: Array<{ href: string; label: string; icon: LucideIcon }> = [
  { href: '/dashboard', label: 'Listings', icon: LayoutDashboard },
  { href: '/dashboard/upload', label: 'Upload', icon: ImagePlus },
];

export function DashboardBrand() {
  return (
    <Link className="flex items-center gap-3 rounded-md px-3 py-2" href="/">
      <span className="flex size-10 items-center justify-center rounded-md bg-primary text-white">
        <Sparkles className="size-5" aria-hidden="true" />
      </span>
      <span>
        <span className="block text-sm font-semibold">CatalogAI</span>
        <span className="block text-xs text-muted-foreground">Listing studio</span>
      </span>
    </Link>
  );
}

export function DashboardNav({ mobile = false }: { mobile?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className={mobile ? 'flex gap-2 overflow-x-auto px-4 py-2' : 'mt-8 grid gap-2'}>
      {navigationItems.map((item) => {
        const Icon = item.icon;
        const isActive =
          pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
        return (
          <Link
            key={item.href}
            className={cn(
              'inline-flex items-center gap-3 rounded-md text-sm font-medium transition',
              mobile ? 'h-9 shrink-0 px-3' : 'px-3 py-2.5',
              isActive
                ? 'bg-primary/15 text-white ring-1 ring-primary/25'
                : 'text-muted-foreground hover:bg-white/[0.06] hover:text-foreground',
            )}
            href={item.href}
          >
            <Icon className="size-4" aria-hidden="true" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
