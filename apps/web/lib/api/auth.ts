import { cookies } from 'next/headers';

import type { AuthSession } from '@ai-product-listing/types';
import { getServerEnv } from '@/lib/env';

interface ApiUserResponse {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
}

interface ApiSessionResponse {
  user: ApiUserResponse;
}

export async function getCurrentSession(): Promise<AuthSession | null> {
  const cookieStore = await cookies();
  const response = await fetch(`${getServerEnv().apiBaseUrl}/auth/me`, {
    cache: 'no-store',
    headers: {
      Cookie: cookieStore.toString(),
    },
  });

  if (!response.ok) {
    return null;
  }

  const session = (await response.json()) as ApiSessionResponse;
  return {
    user: {
      id: session.user.id,
      email: session.user.email,
      name: session.user.name,
      avatarUrl: session.user.avatar_url,
    },
  };
}

