export default function DashboardLoading() {
  return (
    <main className="min-h-screen px-6 py-10">
      <section className="mx-auto flex max-w-6xl flex-col gap-6">
        <div className="h-24 rounded-md bg-muted" />
        <div className="grid gap-4 md:grid-cols-2">
          <div className="h-40 rounded-md bg-muted" />
          <div className="h-40 rounded-md bg-muted" />
        </div>
      </section>
    </main>
  );
}
