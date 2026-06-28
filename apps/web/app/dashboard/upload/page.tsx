import { redirect } from 'next/navigation';

import { UploadWorkspace } from './upload-workspace';
import { DashboardShell } from '@/components/dashboard-shell';
import { getCurrentSession } from '@/lib/api/auth';
import { getUploadedImages } from '@/lib/api/uploads';

export default async function DashboardUploadPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  const imageList = await getUploadedImages();

  return (
    <DashboardShell
      description="Drop product photography, preview selections, then send clean image assets into Product Intelligence and the connected studios."
      email={session.user.email}
      eyebrow="Product Intake"
      title="Upload product images"
    >
      <UploadWorkspace initialImages={imageList.images} />
    </DashboardShell>
  );
}
