import type { NextConfig } from 'next';
import path from 'path';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@ai-product-listing/ui', '@ai-product-listing/types'],
  // Pin the workspace root so Next stops inferring the home directory (a stray
  // ~/package-lock.json otherwise wins), which breaks PostCSS/Tailwind resolution.
  outputFileTracingRoot: path.join(__dirname, '../../'),
};

export default nextConfig;
