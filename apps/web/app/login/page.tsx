import { Suspense } from 'react';

import { AuthForm } from './auth-form';
import { MotionView } from '@/components/motion-view';

export default function LoginPage() {
  return (
    <main className="app-shell flex min-h-screen items-center px-4 py-10 sm:px-6">
      <MotionView className="mx-auto grid w-full max-w-5xl overflow-hidden rounded-lg border border-white/10 bg-white/[0.045] shadow-[0_30px_100px_-70px_rgba(0,0,0,1)] backdrop-blur-xl lg:grid-cols-[minmax(0,1fr)_420px]">
        <section className="hidden min-h-[560px] flex-col justify-between bg-[linear-gradient(135deg,hsl(263_92%_68%/0.28),hsl(196_89%_62%/0.12))] p-8 lg:flex">
          <div>
            <p className="eyebrow">CatalogAI</p>
            <h1 className="mt-5 max-w-md text-4xl font-semibold tracking-normal text-white">
              Your AI Commerce Workspace.
            </h1>
            <p className="mt-4 max-w-sm text-sm leading-6 text-white/72">
              Turn one product image into launch-ready listings, marketplace content, visuals, and
              campaign assets from one premium workspace.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-3">
            {['Intelligence', 'Studios', 'Launch'].map((item) => (
              <div key={item} className="rounded-md border border-white/15 bg-white/10 p-3">
                <p className="text-sm font-semibold text-white">{item}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="flex flex-col gap-6 p-6 sm:p-8">
          <div className="flex flex-col gap-3">
            <p className="eyebrow">AI Commerce Workspace</p>
            <h2 className="text-3xl font-semibold tracking-normal text-white">
              Sign in to your workspace
            </h2>
            <p className="text-sm text-muted-foreground">Use your email and password.</p>
          </div>

          <Suspense fallback={<div className="skeleton h-72" />}>
            <AuthForm />
          </Suspense>
        </section>
      </MotionView>
    </main>
  );
}
