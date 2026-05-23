export default function HomePage() {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto flex max-w-5xl flex-col gap-4">
        <p className="text-sm font-medium text-primary">AI Product Listing Generator</p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-normal">
          Auth foundation ready for the MVP workflow.
        </h1>
        <p className="max-w-2xl text-base text-muted-foreground">
          Sign in with email and password to access the protected dashboard. Product uploads and AI
          generation will be implemented in later feature slices.
        </p>
        <a
          href="/login"
          className="mt-4 inline-flex h-10 w-fit items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Sign in
        </a>
      </section>
    </main>
  );
}
