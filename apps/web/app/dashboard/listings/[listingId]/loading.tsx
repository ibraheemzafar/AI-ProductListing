export default function ListingDetailLoading() {
  return (
    <main className="app-shell min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <section className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[380px_minmax(0,1fr)]">
        <div className="skeleton h-96" />
        <div className="grid gap-4">
          <div className="skeleton h-28" />
          <div className="skeleton h-36" />
          <div className="skeleton h-48" />
        </div>
      </section>
    </main>
  );
}
