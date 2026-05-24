'use client';

export default function GlobalError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body>
        <main style={{ minHeight: '100vh', padding: '40px 24px', fontFamily: 'sans-serif' }}>
          <section style={{ margin: '0 auto', maxWidth: 720, textAlign: 'center' }}>
            <h1>Application error</h1>
            <p>The application could not recover automatically.</p>
            <button type="button" onClick={reset}>
              Try again
            </button>
          </section>
        </main>
      </body>
    </html>
  );
}
