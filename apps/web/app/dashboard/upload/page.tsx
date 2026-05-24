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
      description="Drop product photography, preview selections, then send clean image assets into the AI analysis workflow."
      email={session.user.email}
      eyebrow="AI Intake"
      title="Product image upload"
    >
      <UploadWorkspace initialImages={imageList.images} />
    </DashboardShell>
  );
}
