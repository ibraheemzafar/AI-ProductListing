'use client';

import { Coins } from 'lucide-react';
import Link from 'next/link';
import { useCallback, useEffect, useState } from 'react';

import { WALLET_REFRESH_EVENT, getWallet } from '@/lib/api/billing';

export function WalletBalance() {
  const [credits, setCredits] = useState<number | null>(null);

  const load = useCallback(async () => {
    const wallet = await getWallet();
    if (wallet) {
      setCredits(wallet.availableCredits);
    }
  }, []);

  useEffect(() => {
    void load();
    const handleRefresh = () => void load();
    window.addEventListener('focus', handleRefresh);
    window.addEventListener(WALLET_REFRESH_EVENT, handleRefresh);
    return () => {
      window.removeEventListener('focus', handleRefresh);
      window.removeEventListener(WALLET_REFRESH_EVENT, handleRefresh);
    };
  }, [load]);

  return (
    <Link
      href="/dashboard/billing"
      className="inline-flex h-10 items-center gap-2 rounded-md border border-primary/25 bg-primary/10 px-3 text-sm font-semibold text-foreground transition hover:bg-primary/15"
      title="Available credits — manage billing"
    >
      <Coins className="size-4 text-primary" aria-hidden="true" />
      <span className="tabular-nums">{credits === null ? '—' : credits.toLocaleString()}</span>
      <span className="hidden text-muted-foreground sm:inline">credits</span>
    </Link>
  );
}
