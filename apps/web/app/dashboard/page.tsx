import { redirect } from 'next/navigation';

import { LogoutButton } from './logout-button';
import { getCurrentSession } from '@/lib/api/auth';

export default async function DashboardPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto flex max-w-5xl flex-col gap-8">
        <div className="flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Dashboard</p>
            <h1 className="text-3xl font-semibold tracking-normal">Welcome back</h1>
            <p className="mt-2 text-sm text-muted-foreground">{session.user.email}</p>
          </div>
          <LogoutButton />
        </div>

        <div className="rounded-md border border-border p-6">
          <h2 className="text-lg font-medium">Authentication is ready</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Uploads and AI listing generation are intentionally not implemented in this auth slice.
          </p>
        </div>
      </section>
    </main>
  );
}

