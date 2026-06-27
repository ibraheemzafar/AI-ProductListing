'use client';

import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

export function WelcomeCreditsToast() {
  const params = useSearchParams();
  const credits = params.get('welcome_credits');
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!credits) {
      return;
    }
    setVisible(true);
    const url = new URL(window.location.href);
    url.searchParams.delete('welcome_credits');
    window.history.replaceState(null, '', url.pathname + url.search);
    const timer = window.setTimeout(() => setVisible(false), 6000);
    return () => window.clearTimeout(timer);
  }, [credits]);

  if (!visible || !credits) {
    return null;
  }

  return (
    <div
      className="glass-panel fixed bottom-5 right-5 z-50 max-w-sm px-4 py-3 text-sm text-white"
      role="status"
    >
      Welcome bonus applied: {Number(credits).toLocaleString()} free credits are ready to use.
    </div>
  );
}
