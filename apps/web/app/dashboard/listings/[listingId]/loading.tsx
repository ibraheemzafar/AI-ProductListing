export default function ListingDetailLoading() {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto grid max-w-6xl gap-8 lg:grid-cols-[360px_minmax(0,1fr)]">
        <div className="h-96 rounded-md bg-muted" />
        <div className="grid gap-4">
          <div className="h-28 rounded-md bg-muted" />
          <div className="h-36 rounded-md bg-muted" />
          <div className="h-48 rounded-md bg-muted" />
        </div>
      </section>
    </main>
  );
}
