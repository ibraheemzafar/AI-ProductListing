import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  transpilePackages: ['@ai-product-listing/ui', '@ai-product-listing/types'],
};

export default nextConfig;

