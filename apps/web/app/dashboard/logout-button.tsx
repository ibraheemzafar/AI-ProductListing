'use client';

import { LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { getPublicEnv } from '@/lib/env';

export function LogoutButton() {
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  async function handleLogout() {
    setIsLoggingOut(true);
    await fetch(`${getPublicEnv().apiBaseUrl}/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    router.replace('/login');
    router.refresh();
  }

  return (
    <Button type="button" variant="secondary" onClick={handleLogout} disabled={isLoggingOut}>
      <LogOut className="mr-2 size-4" aria-hidden="true" />
      {isLoggingOut ? 'Signing out' : 'Sign out'}
    </Button>
  );
}

