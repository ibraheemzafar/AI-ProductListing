import { redirect } from 'next/navigation';

import { DashboardShell } from '@/components/dashboard-shell';
import { getCurrentSession } from '@/lib/api/auth';
import { BillingView } from './billing-view';

export default async function BillingPage() {
  const session = await getCurrentSession();

  if (!session) {
    redirect('/login');
  }

  return (
    <DashboardShell
      description="Buy credits, manage your subscription, and review your credit usage."
      email={session.user.email}
      eyebrow="Billing"
      title="Plans & credits"
    >
      <BillingView />
    </DashboardShell>
  );
}
