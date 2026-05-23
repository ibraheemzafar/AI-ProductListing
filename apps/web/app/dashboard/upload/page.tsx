import { redirect } from 'next/navigation';

import { UploadWorkspace } from './upload-workspace';
import { getCurrentSession } from '@/lib/api/auth';
import { getUploadedImages } from '@/lib/api/uploads';

export default async function DashboardUploadPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  const imageList = await getUploadedImages();

  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto flex max-w-6xl flex-col gap-8">
        <div className="border-b border-border pb-6">
          <p className="text-sm font-medium text-primary">Dashboard</p>
          <h1 className="text-3xl font-semibold tracking-normal">Product image upload</h1>
          <p className="mt-2 text-sm text-muted-foreground">{session.user.email}</p>
        </div>

        <UploadWorkspace initialImages={imageList.images} />
      </section>
    </main>
  );
}

