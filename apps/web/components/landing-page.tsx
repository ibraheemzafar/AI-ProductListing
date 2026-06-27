'use client';

import {
  ArrowRight,
  BadgeCheck,
  Bot,
  Boxes,
  Camera,
  Check,
  ChevronDown,
  ClipboardList,
  CloudLightning,
  Download,
  ExternalLink,
  Eye,
  FileText,
  Globe2,
  ImageIcon,
  LineChart,
  Megaphone,
  MousePointerClick,
  PackageCheck,
  Play,
  Send,
  ShoppingBag,
  Sparkles,
  Stars,
  Store,
  UploadCloud,
  Zap,
} from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useState } from 'react';
import type { ComponentType } from 'react';

interface IconProps {
  className?: string;
}

interface FeatureCard {
  icon: ComponentType<IconProps>;
  title: string;
  body: string;
  points: string[];
}

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0 },
};

const stagger = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const workflowSteps = [
  { icon: UploadCloud, label: 'Upload Product', body: 'Drop a product image into the studio.' },
  { icon: Bot, label: 'AI Analysis', body: 'Detect category, style, attributes, and audience.' },
  { icon: FileText, label: 'SEO Listing', body: 'Create conversion-focused titles and descriptions.' },
  { icon: ImageIcon, label: 'Lifestyle Images', body: 'Generate rich campaign-ready product scenes.' },
  { icon: Download, label: 'Marketplace Export', body: 'Prepare content for storefronts and channels.' },
];

const trustItems = [
  { icon: Zap, label: 'Generate in Seconds' },
  { icon: LineChart, label: 'SEO Optimized' },
  { icon: ImageIcon, label: 'AI Product Images' },
  { icon: ShoppingBag, label: 'Marketplace Ready' },
  { icon: Globe2, label: 'Multi-Language' },
];

const features: FeatureCard[] = [
  {
    icon: Eye,
    title: 'AI Product Analysis',
    body: 'Turn a single image into useful product intelligence for listings and campaigns.',
    points: ['Detect category', 'Extract attributes', 'Product intelligence'],
  },
  {
    icon: ClipboardList,
    title: 'AI Listing Generator',
    body: 'Generate marketplace-ready product content with SEO structure baked in.',
    points: ['SEO titles', 'Descriptions', 'Tags'],
  },
  {
    icon: Camera,
    title: 'AI Image Studio',
    body: 'Create polished visuals that make products feel ready for premium storefronts.',
    points: ['Background removal', 'Lifestyle images', 'Hero images'],
  },
  {
    icon: Store,
    title: 'Marketplace Optimization',
    body: 'Adapt listing assets for the channels sellers already use every day.',
    points: ['Shopify', 'Amazon', 'Etsy', 'Daraz', 'WooCommerce', 'eBay'],
  },
  {
    icon: Megaphone,
    title: 'AI Marketing Suite',
    body: 'Extend the listing into ad copy, social captions, and lifecycle campaigns.',
    points: ['Facebook Ads', 'Instagram Captions', 'Google Ads', 'Email Campaigns'],
  },
];

const timeline = [
  'Upload Product',
  'AI Analysis',
  'Listing Generation',
  'SEO Optimization',
  'Image Generation',
  'Export',
];

const marketplaces = [
  { name: 'Shopify', icon: ShoppingBag, color: 'from-emerald-400/30 to-lime-300/10' },
  { name: 'Amazon', icon: PackageCheck, color: 'from-amber-400/30 to-orange-300/10' },
  { name: 'Etsy', icon: Store, color: 'from-rose-400/30 to-orange-300/10' },
  { name: 'Daraz', icon: Boxes, color: 'from-sky-400/30 to-violet-300/10' },
  { name: 'WooCommerce', icon: Store, color: 'from-indigo-400/30 to-sky-300/10' },
  { name: 'eBay', icon: PackageCheck, color: 'from-lime-400/30 to-sky-300/10' },
  { name: 'Generic Store', icon: ShoppingBag, color: 'from-white/20 to-cyan-300/10' },
];

const testimonials = [
  {
    quote:
      'CatalogAI turned a messy batch of product photos into polished listings my team could publish the same afternoon.',
    name: 'Maya Chen',
    role: 'Founder, Linen & Loom',
  },
  {
    quote:
      'The SEO drafts are strong, but the real win is the consistency. Every product now sounds like it belongs to the same brand.',
    name: 'Omar Hassan',
    role: 'Marketplace Lead, StudioSupply',
  },
  {
    quote:
      'We use it as a first-pass creative studio for product launches. Titles, image concepts, and ads are ready before kickoff.',
    name: 'Sofia Reyes',
    role: 'Growth Strategist, Northstar Goods',
  },
];

const pricing = [
  {
    name: 'Starter',
    price: '$19',
    description: 'For new sellers building a cleaner catalog workflow.',
    features: ['50 AI listings / month', 'SEO titles and tags', 'Basic exports'],
  },
  {
    name: 'Professional',
    price: '$49',
    description: 'For growing stores that need content and campaign assets.',
    features: ['300 AI listings / month', 'Image studio access', 'Marketplace optimization'],
    highlighted: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'For agencies and teams managing high-volume catalogs.',
    features: ['Custom usage limits', 'Workflow support', 'Priority onboarding'],
  },
];

const faqs = [
  {
    question: 'Can CatalogAI generate a listing from one image?',
    answer:
      'Yes. The product workflow is designed around image-first intake, then AI analysis, SEO copy, and export-ready listing assets.',
  },
  {
    question: 'Which marketplaces are supported?',
    answer:
      'The product direction includes marketplace-ready exports for common e-commerce channels, with Shopify, Amazon, Etsy, Daraz, WooCommerce, and CSV workflows represented in the experience.',
  },
  {
    question: 'Is this useful for agencies?',
    answer:
      'Yes. Agencies can use the workflow to standardize listing content, generate campaign copy, and speed up product launch preparation.',
  },
  {
    question: 'Does it support AI-generated product visuals?',
    answer:
      'The platform experience includes image enhancement, lifestyle scenes, and hero image generation as part of the AI content workflow.',
  },
];

function SectionHeading({
  eyebrow,
  title,
  body,
}: {
  eyebrow: string;
  title: string;
  body: string;
}) {
  return (
    <motion.div
      className="mx-auto max-w-3xl text-center"
      initial="hidden"
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      variants={fadeUp}
      viewport={{ once: true, margin: '-80px' }}
      whileInView="visible"
    >
      <p className="eyebrow">{eyebrow}</p>
      <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl lg:text-5xl">{title}</h2>
      <p className="mt-5 text-base leading-8 text-muted-foreground sm:text-lg">{body}</p>
    </motion.div>
  );
}

function GradientBackdrop() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <motion.div
        animate={{ x: [0, 28, -18, 0], y: [0, -18, 18, 0], scale: [1, 1.08, 0.98, 1] }}
        className="absolute left-[8%] top-24 h-80 w-80 rounded-full bg-primary/20 blur-3xl"
        transition={{ duration: 12, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.div
        animate={{ x: [0, -24, 22, 0], y: [0, 22, -12, 0], scale: [1, 0.95, 1.08, 1] }}
        className="absolute right-[6%] top-36 h-96 w-96 rounded-full bg-accent/15 blur-3xl"
        transition={{ duration: 14, repeat: Infinity, ease: 'easeInOut' }}
      />
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent" />
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:72px_72px] [mask-image:linear-gradient(to_bottom,black,transparent_78%)]" />
    </div>
  );
}

function Navigation() {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-background/70 backdrop-blur-2xl">
      <nav className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link className="flex items-center gap-3 font-semibold text-white" href="/">
          <span className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent text-white shadow-[0_16px_48px_-20px_hsl(var(--primary))]">
            <Sparkles className="size-4" aria-hidden="true" />
          </span>
          CatalogAI
        </Link>
        <div className="hidden items-center gap-7 text-sm font-medium text-muted-foreground md:flex">
          <a className="transition hover:text-white" href="#features">
            Features
          </a>
          <a className="transition hover:text-white" href="#pricing">
            Pricing
          </a>
          <a className="transition hover:text-white" href="#demo">
            Demo
          </a>
        </div>
        <div className="flex items-center gap-2">
          <Link
            className="hidden h-10 items-center justify-center rounded-md px-4 text-sm font-semibold text-muted-foreground transition hover:text-white sm:inline-flex"
            href="/login"
          >
            Sign In
          </Link>
          <Link
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-white px-4 text-sm font-semibold text-slate-950 shadow-[0_18px_58px_-28px_rgba(255,255,255,0.9)] transition hover:-translate-y-0.5 hover:bg-white/90"
            href="/login"
          >
            Get Started
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
        </div>
      </nav>
    </header>
  );
}

function HeroWorkflowVisual() {
  return (
    <motion.div
      animate={{ y: [0, -10, 0] }}
      className="glass-panel relative mx-auto w-full max-w-xl p-4"
      transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut' }}
    >
      <div className="absolute -right-8 top-10 hidden rounded-lg border border-accent/20 bg-accent/10 p-3 text-accent shadow-2xl backdrop-blur-xl sm:block">
        <CloudLightning className="size-5" aria-hidden="true" />
      </div>
      <div className="absolute -left-6 bottom-24 hidden rounded-lg border border-primary/20 bg-primary/10 p-3 text-primary shadow-2xl backdrop-blur-xl sm:block">
        <Stars className="size-5" aria-hidden="true" />
      </div>
      <div className="overflow-hidden rounded-lg border border-white/10 bg-slate-950/70">
        <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
          <div>
            <p className="text-sm font-semibold text-white">AI workflow engine</p>
            <p className="text-xs text-muted-foreground">Product image to launch assets</p>
          </div>
          <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-semibold text-emerald-200">
            Live
          </span>
        </div>
        <div className="space-y-3 p-4">
          {workflowSteps.map((step, index) => {
            const Icon = step.icon;
            return (
              <motion.div
                animate={{ opacity: [0.72, 1, 0.72], x: [0, index % 2 === 0 ? 4 : -4, 0] }}
                className="relative rounded-lg border border-white/10 bg-white/[0.045] p-4"
                key={step.label}
                transition={{ duration: 3.5, delay: index * 0.2, repeat: Infinity }}
              >
                {index < workflowSteps.length - 1 ? (
                  <span className="absolute -bottom-3 left-8 h-3 w-px bg-gradient-to-b from-primary to-accent" />
                ) : null}
                <div className="flex items-start gap-3">
                  <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-primary/25 to-accent/15 text-white">
                    <Icon className="size-5" />
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-white">{step.label}</p>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">{step.body}</p>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

function HeroSection() {
  return (
    <section className="relative mx-auto grid max-w-7xl gap-12 px-4 pb-20 pt-16 sm:px-6 lg:grid-cols-[minmax(0,1fr)_520px] lg:px-8 lg:pb-28 lg:pt-24">
      <motion.div
        animate="visible"
        className="flex flex-col justify-center"
        initial="hidden"
        transition={{ staggerChildren: 0.08 }}
      >
        <motion.p className="eyebrow" variants={fadeUp}>
          AI Product Listing Generator
        </motion.p>
        <motion.h1
          className="mt-5 max-w-5xl text-5xl font-semibold text-white sm:text-6xl lg:text-7xl"
          variants={fadeUp}
        >
          Transform Product Photos into High-Converting Listings with AI
        </motion.h1>
        <motion.p
          className="mt-6 max-w-2xl text-base leading-8 text-muted-foreground sm:text-lg"
          variants={fadeUp}
        >
          Generate product listings, SEO content, marketplace exports, lifestyle images, ad copy,
          and marketing assets from a single product image.
        </motion.p>
        <motion.div className="mt-9 flex flex-wrap gap-3" variants={fadeUp}>
          <Link
            className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-gradient-to-r from-primary to-accent px-5 text-sm font-semibold text-white shadow-[0_22px_70px_-28px_hsl(var(--primary))] transition hover:-translate-y-0.5"
            href="/login"
          >
            Generate First Listing
            <ArrowRight className="size-4" aria-hidden="true" />
          </Link>
          <a
            className="inline-flex h-12 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.06] px-5 text-sm font-semibold text-white backdrop-blur transition hover:-translate-y-0.5 hover:bg-white/10"
            href="#demo"
          >
            <Play className="size-4" aria-hidden="true" />
            Watch Demo
          </a>
        </motion.div>
      </motion.div>
      <motion.div
        animate={{ opacity: 1, scale: 1 }}
        initial={{ opacity: 0, scale: 0.96 }}
        transition={{ duration: 0.65, delay: 0.18, ease: [0.22, 1, 0.36, 1] }}
      >
        <HeroWorkflowVisual />
      </motion.div>
    </section>
  );
}

function TrustBar() {
  return (
    <section className="border-y border-white/10 bg-white/[0.025]">
      <motion.div
        className="mx-auto grid max-w-7xl gap-3 px-4 py-5 sm:grid-cols-2 sm:px-6 lg:grid-cols-5 lg:px-8"
        initial="hidden"
        variants={stagger}
        viewport={{ once: true }}
        whileInView="visible"
      >
        {trustItems.map((item) => {
          const Icon = item.icon;
          return (
            <motion.div
              className="flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-3 text-sm font-semibold text-white"
              key={item.label}
              variants={fadeUp}
            >
              <Icon className="size-4 text-accent" />
              {item.label}
            </motion.div>
          );
        })}
      </motion.div>
    </section>
  );
}

function FeatureSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8" id="features">
      <SectionHeading
        body="A focused AI workspace for sellers who need better listings, stronger visuals, and faster launches."
        eyebrow="Features"
        title="Everything your product content team needs"
      />
      <motion.div
        className="mt-14 grid gap-4 md:grid-cols-2 lg:grid-cols-3"
        initial="hidden"
        variants={stagger}
        viewport={{ once: true, margin: '-80px' }}
        whileInView="visible"
      >
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <motion.article className="premium-card premium-card-hover h-full p-6" key={feature.title} variants={fadeUp}>
              <span className="flex size-11 items-center justify-center rounded-lg bg-gradient-to-br from-primary/25 to-accent/15 text-white">
                <Icon className="size-5" />
              </span>
              <h3 className="mt-6 text-xl font-semibold text-white">{feature.title}</h3>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">{feature.body}</p>
              <div className="mt-6 space-y-3">
                {feature.points.map((point) => (
                  <p className="flex items-center gap-2 text-sm text-white/85" key={point}>
                    <Check className="size-4 text-accent" aria-hidden="true" />
                    {point}
                  </p>
                ))}
              </div>
            </motion.article>
          );
        })}
      </motion.div>
    </section>
  );
}

function WorkflowSection() {
  return (
    <section className="bg-white/[0.025] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          body="From raw product image to publishable marketplace content, the workflow stays guided and fast."
          eyebrow="Workflow"
          title="A launch pipeline powered by AI"
        />
        <div className="mt-16 grid gap-4 lg:grid-cols-6">
          {timeline.map((step, index) => (
            <motion.div
              className="relative rounded-lg border border-white/10 bg-background/70 p-5 backdrop-blur"
              initial={{ opacity: 0, y: 18 }}
              key={step}
              transition={{ duration: 0.45, delay: index * 0.08 }}
              viewport={{ once: true, margin: '-80px' }}
              whileInView={{ opacity: 1, y: 0 }}
            >
              {index < timeline.length - 1 ? (
                <motion.span
                  className="absolute left-10 top-8 hidden h-px w-[calc(100%+1rem)] bg-gradient-to-r from-primary via-accent to-transparent lg:block"
                  initial={{ scaleX: 0 }}
                  style={{ transformOrigin: 'left' }}
                  transition={{ duration: 0.6, delay: index * 0.12 + 0.2 }}
                  viewport={{ once: true }}
                  whileInView={{ scaleX: 1 }}
                />
              ) : null}
              <span className="relative z-10 flex size-10 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent text-sm font-bold text-white">
                {index + 1}
              </span>
              <h3 className="mt-5 text-base font-semibold text-white">{step}</h3>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

function DemoSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8" id="demo">
      <SectionHeading
        body="A realistic preview of how a product image becomes SEO copy, visual direction, and export-ready content."
        eyebrow="Interactive Demo"
        title="Watch the listing build itself"
      />
      <div className="mt-14 grid gap-5 lg:grid-cols-[420px_minmax(0,1fr)]">
        <motion.div
          className="glass-panel p-5"
          initial="hidden"
          variants={fadeUp}
          viewport={{ once: true, margin: '-80px' }}
          whileInView="visible"
        >
          <div className="flex aspect-[4/3] items-center justify-center rounded-lg border border-dashed border-white/15 bg-gradient-to-br from-white/[0.08] to-white/[0.02]">
            <div className="text-center">
              <span className="mx-auto flex size-14 items-center justify-center rounded-lg bg-primary/15 text-primary">
                <UploadCloud className="size-7" aria-hidden="true" />
              </span>
              <p className="mt-4 text-sm font-semibold text-white">Upload Product</p>
              <p className="mt-1 text-xs text-muted-foreground">Matte ceramic desk lamp.jpg</p>
            </div>
          </div>
          <div className="mt-5 grid grid-cols-3 gap-3">
            {['Analyzing', 'Writing', 'Exporting'].map((item, index) => (
              <div className="skeleton h-16 p-3" key={item}>
                <p className="relative z-10 text-xs font-semibold text-white/80">{item}</p>
                <motion.span
                  animate={{ width: ['35%', '78%', '48%'] }}
                  className="relative z-10 mt-3 block h-1.5 rounded-full bg-gradient-to-r from-primary to-accent"
                  transition={{ duration: 2.5, delay: index * 0.2, repeat: Infinity }}
                />
              </div>
            ))}
          </div>
        </motion.div>
        <motion.div
          className="glass-panel overflow-hidden"
          initial="hidden"
          variants={fadeUp}
          viewport={{ once: true, margin: '-80px' }}
          whileInView="visible"
        >
          <div className="border-b border-white/10 px-5 py-4">
            <p className="text-sm font-semibold text-white">Generated Listing Preview</p>
            <p className="mt-1 text-xs text-muted-foreground">SEO score 94/100 · Marketplace ready</p>
          </div>
          <div className="grid gap-5 p-5 lg:grid-cols-[minmax(0,1fr)_280px]">
            <div className="space-y-5">
              <div>
                <p className="text-xs font-semibold uppercase text-accent">Generated Title</p>
                <h3 className="mt-2 text-2xl font-semibold text-white">
                  Modern Matte Ceramic Desk Lamp for Warm Minimalist Workspaces
                </h3>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-accent">Generated Description</p>
                <p className="mt-2 text-sm leading-7 text-muted-foreground">
                  Bring soft, focused light to your desk, nightstand, or reading corner with a
                  sculptural ceramic lamp designed for calm modern interiors. The matte finish,
                  compact silhouette, and warm glow make it ideal for home offices and boutique
                  decor collections.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                {['minimal lamp', 'ceramic lighting', 'desk decor', 'warm light'].map((tag) => (
                  <span className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-white/85" key={tag}>
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-lg border border-white/10 bg-[radial-gradient(circle_at_35%_25%,rgba(255,255,255,0.55),transparent_18%),linear-gradient(135deg,rgba(168,85,247,0.32),rgba(34,211,238,0.14)),linear-gradient(160deg,#1e1b4b,#020617)] p-4">
              <div className="flex h-full min-h-64 flex-col justify-end rounded-md border border-white/10 bg-black/10 p-4">
                <p className="text-xs font-semibold uppercase text-white/70">Generated Lifestyle Image</p>
                <p className="mt-2 text-lg font-semibold text-white">Warm studio desk scene</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function GallerySection() {
  return (
    <section className="bg-white/[0.025] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          body="Give every catalog item the visual language of a premium campaign without slowing down launch work."
          eyebrow="Before / After"
          title="From product shot to lifestyle scene"
        />
        <div className="mt-14 grid gap-5 md:grid-cols-2">
          {['Original Product', 'AI Generated Lifestyle Image'].map((label, index) => (
            <motion.article
              className="glass-panel overflow-hidden p-4"
              initial={{ opacity: 0, y: 20 }}
              key={label}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              viewport={{ once: true }}
              whileInView={{ opacity: 1, y: 0 }}
            >
              <div
                className={
                  index === 0
                    ? 'flex aspect-[4/3] items-center justify-center rounded-lg border border-white/10 bg-slate-900'
                    : 'flex aspect-[4/3] items-center justify-center rounded-lg border border-white/10 bg-[radial-gradient(circle_at_50%_28%,rgba(255,255,255,0.62),transparent_16%),linear-gradient(135deg,rgba(59,130,246,0.28),rgba(168,85,247,0.24)),linear-gradient(160deg,#111827,#020617)]'
                }
              >
                <div className="h-28 w-24 rounded-[2rem_2rem_0.75rem_0.75rem] border border-white/20 bg-gradient-to-b from-white/70 to-white/20 shadow-2xl" />
              </div>
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm font-semibold text-white">{label}</p>
                {index === 0 ? (
                  <ArrowRight className="size-4 text-muted-foreground" aria-hidden="true" />
                ) : (
                  <BadgeCheck className="size-4 text-accent" aria-hidden="true" />
                )}
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

function MarketplaceSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
      <div className="grid gap-10 lg:grid-cols-[0.82fr_1fr] lg:items-center">
        <div>
          <p className="eyebrow">Marketplace Export</p>
          <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">One Click Export</h2>
          <p className="mt-5 text-base leading-8 text-muted-foreground">
            Prepare polished content for major marketplaces and storefront workflows, then move from
            generation to publishing without rebuilding assets by hand.
          </p>
          <Link
            className="mt-8 inline-flex h-11 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.06] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-white/10"
            href="/login"
          >
            Export a listing
            <ExternalLink className="size-4" aria-hidden="true" />
          </Link>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          {marketplaces.map((marketplace) => {
            const Icon = marketplace.icon;
            return (
              <motion.div
                className={`rounded-lg border border-white/10 bg-gradient-to-br ${marketplace.color} p-5 shadow-[0_22px_80px_-54px_rgba(0,0,0,0.95)]`}
                initial={{ opacity: 0, y: 18 }}
                key={marketplace.name}
                viewport={{ once: true }}
                whileHover={{ y: -6 }}
                whileInView={{ opacity: 1, y: 0 }}
              >
                <Icon className="size-6 text-white" />
                <p className="mt-6 text-xl font-semibold text-white">{marketplace.name}</p>
                <p className="mt-2 text-sm text-white/70">Ready for listing export</p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function TestimonialsSection() {
  return (
    <section className="bg-white/[0.025] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <SectionHeading
          body="Built for sellers, marketers, and agencies that need catalog content to move faster."
          eyebrow="Testimonials"
          title="Teams launch cleaner product pages"
        />
        <div className="mt-14 grid gap-4 md:grid-cols-3">
          {testimonials.map((testimonial, index) => (
            <motion.article
              className="premium-card h-full p-6"
              initial={{ opacity: 0, y: 20 }}
              key={testimonial.name}
              transition={{ duration: 0.45, delay: index * 0.08 }}
              viewport={{ once: true }}
              whileInView={{ opacity: 1, y: 0 }}
            >
              <Sparkles className="size-5 text-primary" aria-hidden="true" />
              <p className="mt-5 text-sm leading-7 text-white/82">"{testimonial.quote}"</p>
              <div className="mt-6 border-t border-white/10 pt-5">
                <p className="font-semibold text-white">{testimonial.name}</p>
                <p className="mt-1 text-sm text-muted-foreground">{testimonial.role}</p>
              </div>
            </motion.article>
          ))}
        </div>
      </div>
    </section>
  );
}

function PricingSection() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8" id="pricing">
      <SectionHeading
        body="Simple tiers for early catalog teams, growing sellers, and high-volume content operations."
        eyebrow="Pricing"
        title="Start small, scale the workflow"
      />
      <div className="mt-14 grid gap-4 lg:grid-cols-3">
        {pricing.map((plan) => (
          <motion.article
            className={`rounded-lg border p-6 ${
              plan.highlighted
                ? 'border-primary/50 bg-gradient-to-b from-primary/18 to-white/[0.045] shadow-[0_24px_100px_-54px_hsl(var(--primary))]'
                : 'border-white/10 bg-white/[0.045]'
            }`}
            initial={{ opacity: 0, y: 20 }}
            key={plan.name}
            viewport={{ once: true }}
            whileHover={{ y: -6 }}
            whileInView={{ opacity: 1, y: 0 }}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-white">{plan.name}</h3>
              {plan.highlighted ? (
                <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold text-primary">
                  Popular
                </span>
              ) : null}
            </div>
            <p className="mt-5 text-4xl font-semibold text-white">{plan.price}</p>
            <p className="mt-4 min-h-12 text-sm leading-6 text-muted-foreground">{plan.description}</p>
            <div className="mt-6 space-y-3">
              {plan.features.map((feature) => (
                <p className="flex items-center gap-2 text-sm text-white/85" key={feature}>
                  <Check className="size-4 text-accent" aria-hidden="true" />
                  {feature}
                </p>
              ))}
            </div>
            <Link
              className={`mt-7 inline-flex h-11 w-full items-center justify-center rounded-md text-sm font-semibold transition hover:-translate-y-0.5 ${
                plan.highlighted
                  ? 'bg-white text-slate-950 hover:bg-white/90'
                  : 'border border-white/10 bg-white/[0.06] text-white hover:bg-white/10'
              }`}
              href="/login"
            >
              Get Started
            </Link>
          </motion.article>
        ))}
      </div>
    </section>
  );
}

function FaqSection() {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section className="bg-white/[0.025] px-4 py-24 sm:px-6 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.7fr_1fr]">
        <div>
          <p className="eyebrow">FAQ</p>
          <h2 className="mt-4 text-3xl font-semibold text-white sm:text-4xl">Questions before launch</h2>
          <p className="mt-5 text-base leading-8 text-muted-foreground">
            The landing page previews the AI content workflow while keeping users pointed at the
            current product workspace.
          </p>
        </div>
        <div className="space-y-3">
          {faqs.map((faq, index) => {
            const isOpen = openIndex === index;
            return (
              <div className="rounded-lg border border-white/10 bg-background/70" key={faq.question}>
                <button
                  aria-expanded={isOpen}
                  className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left text-sm font-semibold text-white"
                  onClick={() => setOpenIndex(isOpen ? -1 : index)}
                  type="button"
                >
                  {faq.question}
                  <ChevronDown
                    className={`size-4 shrink-0 text-muted-foreground transition ${isOpen ? 'rotate-180' : ''}`}
                    aria-hidden="true"
                  />
                </button>
                <motion.div
                  animate={{ height: isOpen ? 'auto' : 0, opacity: isOpen ? 1 : 0 }}
                  className="overflow-hidden"
                  initial={false}
                  transition={{ duration: 0.25 }}
                >
                  <p className="px-5 pb-5 text-sm leading-7 text-muted-foreground">{faq.answer}</p>
                </motion.div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function FinalCta() {
  return (
    <section className="mx-auto max-w-7xl px-4 py-24 sm:px-6 lg:px-8">
      <motion.div
        className="relative overflow-hidden rounded-lg border border-white/10 bg-gradient-to-br from-primary/24 via-white/[0.06] to-accent/18 p-8 text-center shadow-[0_28px_120px_-70px_hsl(var(--primary))] sm:p-12"
        initial={{ opacity: 0, y: 24 }}
        viewport={{ once: true }}
        whileInView={{ opacity: 1, y: 0 }}
      >
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(255,255,255,0.22),transparent_28rem)]" />
        <div className="relative z-10">
          <p className="eyebrow">Automate content ops</p>
          <h2 className="mx-auto mt-4 max-w-3xl text-3xl font-semibold text-white sm:text-5xl">
            Ready to Automate Your E-commerce Content?
          </h2>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-white px-5 text-sm font-semibold text-slate-950 transition hover:-translate-y-0.5 hover:bg-white/90"
              href="/login"
            >
              Start Free
              <MousePointerClick className="size-4" aria-hidden="true" />
            </Link>
            <a
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md border border-white/10 bg-white/[0.08] px-5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-white/12"
              href="mailto:sales@catalogai.local"
            >
              Book Demo
              <Send className="size-4" aria-hidden="true" />
            </a>
          </div>
        </div>
      </motion.div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-white/10 px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <Link className="flex items-center gap-3 font-semibold text-white" href="/">
          <span className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent text-white">
            <Sparkles className="size-4" aria-hidden="true" />
          </span>
          CatalogAI
        </Link>
        <div className="flex flex-wrap gap-5 text-sm text-muted-foreground">
          <a className="transition hover:text-white" href="#features">
            Features
          </a>
          <a className="transition hover:text-white" href="#demo">
            Demo
          </a>
          <a className="transition hover:text-white" href="#pricing">
            Pricing
          </a>
          <Link className="transition hover:text-white" href="/login">
            Sign In
          </Link>
        </div>
        <p className="text-sm text-muted-foreground">AI-powered listings for modern commerce.</p>
      </div>
    </footer>
  );
}

export function LandingPage() {
  return (
    <main className="app-shell relative min-h-screen overflow-hidden">
      <GradientBackdrop />
      <div className="relative z-10">
        <Navigation />
        <HeroSection />
        <TrustBar />
        <FeatureSection />
        <WorkflowSection />
        <DemoSection />
        <GallerySection />
        <MarketplaceSection />
        <TestimonialsSection />
        <PricingSection />
        <FaqSection />
        <FinalCta />
        <Footer />
      </div>
    </main>
  );
}
