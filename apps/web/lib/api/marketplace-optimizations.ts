import type { Marketplace, MarketplaceOptimizationResult } from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiMarketplaceOptimization {
  id: string;
  listing_id: string;
  product_id: string;
  marketplace: Marketplace;
  optimization: {
    optimized_title: string;
    optimized_description: string;
    bullet_points: string[];
    keywords_tags: string[];
    platform_notes: string;
  };
  created_at: string;
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function optimizeListingForMarketplace(
  listingId: string,
  marketplace: Marketplace,
  force = false,
): Promise<MarketplaceOptimizationResult> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/marketplace-optimizations`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ marketplace, force }),
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapOptimization((await response.json()) as ApiMarketplaceOptimization);
}

export async function getMarketplaceOptimizations(
  listingId: string,
): Promise<MarketplaceOptimizationResult[]> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/marketplace-optimizations`,
    {
      credentials: 'include',
    },
  );

  if (!response.ok) {
    return [];
  }

  const payload = (await response.json()) as { optimizations: ApiMarketplaceOptimization[] } | null;
  return (payload?.optimizations ?? []).map(mapOptimization);
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Marketplace optimization failed.';
  } catch {
    return 'Marketplace optimization failed.';
  }
}

function mapOptimization(
  optimization: ApiMarketplaceOptimization,
): MarketplaceOptimizationResult {
  return {
    id: optimization.id,
    listingId: optimization.listing_id,
    productId: optimization.product_id,
    marketplace: optimization.marketplace,
    optimization: {
      optimizedTitle: optimization.optimization.optimized_title,
      optimizedDescription: optimization.optimization.optimized_description,
      bulletPoints: optimization.optimization.bullet_points,
      keywordsTags: optimization.optimization.keywords_tags,
      platformNotes: optimization.optimization.platform_notes,
    },
    createdAt: optimization.created_at,
  };
}
