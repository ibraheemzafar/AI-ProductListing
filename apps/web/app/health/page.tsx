import Link from 'next/link';

import { StatusBadge } from '@/components/status-badge';
import { getPublicEnv } from '@/lib/env';

interface ApiHealthResponse {
  status: string;
  service: string;
}

export default async function HealthPage() {
  const webStatus = { status: 'ok', service: 'web' };
  const apiStatus = await getApiHealth();

  return (
    <main className="app-shell min-h-screen px-4 py-10 sm:px-6 lg:px-8">
      <section className="mx-auto max-w-3xl">
        <div className="glass-panel p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="eyebrow">Health Check</p>
              <h1 className="mt-3 text-3xl font-semibold text-white">System status</h1>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                Lightweight readiness check for the web app and API connection.
              </p>
            </div>
            <Link
              className="inline-flex h-10 items-center justify-center rounded-md border border-white/10 bg-white/[0.05] px-4 text-sm font-semibold text-white transition hover:bg-white/10"
              href="/login"
            >
              Login
            </Link>
          </div>

          <div className="mt-8 grid gap-3">
            <HealthRow label="Web app" detail={webStatus.service} healthy={webStatus.status === 'ok'} />
            <HealthRow
              label="API"
              detail={apiStatus.service}
              healthy={apiStatus.status === 'ok'}
              message={apiStatus.message}
            />
          </div>
        </div>
      </section>
    </main>
  );
}

function HealthRow({
  label,
  detail,
  healthy,
  message,
}: {
  label: string;
  detail: string;
  healthy: boolean;
  message?: string;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-white/10 bg-white/[0.04] p-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm font-semibold text-white">{label}</p>
        <p className="mt-1 text-xs text-muted-foreground">{message ?? detail}</p>
      </div>
      <StatusBadge status={healthy ? 'generated' : 'draft'} />
    </div>
  );
}

async function getApiHealth(): Promise<ApiHealthResponse & { message?: string }> {
  try {
    const response = await fetch(`${getPublicEnv().apiBaseUrl}/health`, {
      cache: 'no-store',
    });

    if (!response.ok) {
      return {
        status: 'error',
        service: 'api',
        message: `API returned ${response.status}`,
      };
    }

    return (await response.json()) as ApiHealthResponse;
  } catch {
    return {
      status: 'error',
      service: 'api',
      message: 'API is not reachable from the web app.',
    };
  }
}
