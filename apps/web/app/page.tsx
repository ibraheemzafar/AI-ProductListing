import {
  ArrowRight,
  CheckCircle2,
  ImageIcon,
  SearchCheck,
  Sparkles,
  WandSparkles,
} from 'lucide-react';
import Link from 'next/link';

import { MotionView } from '@/components/motion-view';

export default function HomePage() {
  return (
    <main className="app-shell min-h-screen">
      <header className="mx-auto flex max-w-7xl items-center justify-between px-4 py-5 sm:px-6 lg:px-8">
        <Link className="flex items-center gap-3 font-semibold" href="/">
          <span className="flex size-10 items-center justify-center rounded-md bg-primary text-white">
            <Sparkles className="size-5" aria-hidden="true" />
          </span>
          CatalogAI
        </Link>
        <Link
          className="inline-flex h-10 items-center justify-center rounded-md border border-white/10 bg-white/[0.06] px-4 text-sm font-semibold text-white transition hover:bg-white/10"
          href="/login"
        >
          Sign in
        </Link>
      </header>

      <section className="mx-auto grid max-w-7xl gap-10 px-4 pb-16 pt-10 sm:px-6 lg:grid-cols-[minmax(0,1fr)_520px] lg:px-8 lg:pt-20">
        <MotionView className="flex flex-col justify-center">
          <p className="eyebrow">AI Product Listing Generator</p>
          <h1 className="mt-5 max-w-4xl text-5xl font-semibold tracking-normal text-white sm:text-6xl lg:text-7xl">
            Turn product photos into polished marketplace listings.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-8 text-muted-foreground sm:text-lg">
            Upload product images, extract visual attributes, generate SEO copy, improve listings,
            and create premium product visuals from one focused AI workspace.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-primary px-5 text-sm font-semibold text-white shadow-[0_18px_55px_-22px_hsl(var(--primary))] transition hover:-translate-y-0.5 hover:bg-primary/90"
              href="/login"
            >
              Open workspace
              <ArrowRight className="size-4" aria-hidden="true" />
            </Link>
            <a
              className="inline-flex h-11 items-center justify-center rounded-md border border-white/10 bg-white/[0.05] px-5 text-sm font-semibold text-white transition hover:bg-white/10"
              href="#features"
            >
              View workflow
            </a>
          </div>
        </MotionView>

        <MotionView className="glass-panel p-4" delay={0.12}>
          <div className="overflow-hidden rounded-lg border border-white/10 bg-background/70">
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
              <div>
                <p className="text-sm font-semibold text-white">AI listing studio</p>
                <p className="text-xs text-muted-foreground">Live product workflow</p>
              </div>
              <span className="rounded-full bg-accent/15 px-3 py-1 text-xs font-semibold text-accent">
                Ready
              </span>
            </div>
            <div className="grid gap-4 p-4">
              <div className="aspect-[4/3] rounded-lg border border-white/10 bg-[linear-gradient(135deg,hsl(263_92%_68%/0.22),hsl(196_89%_62%/0.12)),url('/window.svg')] bg-cover p-4">
                <div className="mt-auto w-48 rounded-lg border border-white/10 bg-background/70 p-3 backdrop-blur">
                  <p className="text-xs text-muted-foreground">Generated title</p>
                  <p className="mt-1 text-sm font-semibold text-white">Minimal Ceramic Desk Lamp</p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                {[
                  ['SEO', '94/100'],
                  ['Keywords', '18'],
                  ['Images', '6'],
                ].map(([label, value]) => (
                  <div
                    key={label}
                    className="rounded-md border border-white/10 bg-white/[0.04] p-3"
                  >
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="mt-1 text-lg font-semibold text-white">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </MotionView>
      </section>

      <section
        id="features"
        className="mx-auto grid max-w-7xl gap-4 px-4 pb-20 sm:px-6 md:grid-cols-3 lg:px-8"
      >
        {[
          {
            icon: ImageIcon,
            title: 'Image-first intake',
            body: 'Drag in product photos and keep the upload workflow clear, visual, and responsive.',
          },
          {
            icon: WandSparkles,
            title: 'AI copy generation',
            body: 'Generate titles, descriptions, tags, keywords, and ad-ready copy for MVP exports.',
          },
          {
            icon: SearchCheck,
            title: 'SEO improvement loop',
            body: 'Review scores, suggestions, listing versions, and marketplace-ready output.',
          },
        ].map((feature, index) => {
          const Icon = feature.icon;
          return (
            <MotionView key={feature.title} delay={index * 0.08}>
              <article className="premium-card premium-card-hover h-full p-5">
                <Icon className="size-5 text-primary" aria-hidden="true" />
                <h2 className="mt-5 text-lg font-semibold text-white">{feature.title}</h2>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{feature.body}</p>
                <p className="mt-5 flex items-center gap-2 text-xs font-semibold text-accent">
                  <CheckCircle2 className="size-4" aria-hidden="true" />
                  MVP aligned
                </p>
              </article>
            </MotionView>
          );
        })}
      </section>

      <footer className="border-t border-white/10 px-4 py-8 text-center text-sm text-muted-foreground">
        CatalogAI builds SEO-ready product listings from images.
      </footer>
    </main>
  );
}
