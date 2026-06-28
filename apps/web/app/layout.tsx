import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';

export const metadata: Metadata = {
  title: 'CatalogAI | AI Commerce Workspace',
  description: 'Launch products faster with AI-generated commerce assets from one product image.',
};

interface RootLayoutProps {
  children: ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
