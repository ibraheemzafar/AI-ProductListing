export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto flex max-w-5xl flex-col gap-4">
        <p className="text-sm font-medium text-primary">AI Product Listing Generator</p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-normal">
          Monorepo scaffold ready for the MVP workflow.
        </h1>
        <p className="max-w-2xl text-base text-muted-foreground">
          This Next.js app is initialized with TypeScript, Tailwind CSS, and shared package
          boundaries. Product workflows will be implemented in future feature slices.
        </p>
      </section>
    </main>
  );
}

