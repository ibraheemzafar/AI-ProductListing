import { Suspense } from 'react';

import { AuthForm } from './auth-form';

export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center px-6 py-10">
      <section className="mx-auto flex w-full max-w-md flex-col gap-6">
        <div className="flex flex-col gap-3">
          <p className="text-sm font-medium text-primary">AI Product Listing Generator</p>
          <h1 className="text-3xl font-semibold tracking-normal">Sign in to your workspace</h1>
          <p className="text-sm text-muted-foreground">Use your email and password.</p>
        </div>

        <Suspense fallback={<p className="text-sm text-muted-foreground">Loading form...</p>}>
          <AuthForm />
        </Suspense>
      </section>
    </main>
  );
}
