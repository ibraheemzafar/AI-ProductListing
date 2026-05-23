import { redirect } from 'next/navigation';
import Link from 'next/link';

import { LogoutButton } from './logout-button';
import { getCurrentSession } from '@/lib/api/auth';
import { getUploadedImages } from '@/lib/api/uploads';

export default async function DashboardPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  const imageList = await getUploadedImages();

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
          <h2 className="text-lg font-medium">Product uploads</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
            Upload product images now. AI listing generation is intentionally not implemented yet.
          </p>
          <Link
            className="mt-4 inline-flex h-10 items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
            href="/dashboard/upload"
          >
            Upload images
          </Link>
        </div>

        <div className="rounded-md border border-border p-6">
          <h2 className="text-lg font-medium">Recent images</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {imageList.images.length > 0 ? (
              imageList.images.slice(0, 8).map((image) => (
                <div key={image.id} className="overflow-hidden rounded-md border border-border">
                  <img
                    alt={image.originalFilename}
                    className="aspect-square w-full object-cover"
                    src={image.imageUrl}
                  />
                  <p className="truncate px-3 py-2 text-xs text-muted-foreground">
                    {image.originalFilename}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No uploads yet.</p>
            )}
          </div>
        </div>
      </section>
    </main>
  );
}
