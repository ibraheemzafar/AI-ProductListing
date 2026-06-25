import type {
  GeneratedListingResult,
} from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiGeneratedListing {
  id: string;
  product_id: string;
  analysis_id: string;
  listing: {
    title: string;
    short_description: string;
    long_description: string;
    seo_keywords: string[];
    product_tags: string[];
  };
  created_at: string;
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function generateListing(analysisId: string): Promise<GeneratedListingResult> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/products/analysis/${analysisId}/listing`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapGeneratedListing((await response.json()) as ApiGeneratedListing);
}

export async function getListingVersions(
  analysisId: string,
): Promise<GeneratedListingResult[]> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/products/analysis/${analysisId}/listings`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    return [];
  }

  const payload = (await response.json()) as ApiGeneratedListing[] | null;
  return (payload ?? []).map(mapGeneratedListing);
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Listing generation failed. Please try again.';
  } catch {
    return 'Listing generation failed. Please try again.';
  }
}

function mapGeneratedListing(listing: ApiGeneratedListing): GeneratedListingResult {
  return {
    id: listing.id,
    productId: listing.product_id,
    analysisId: listing.analysis_id,
    listing: {
      title: listing.listing.title,
      shortDescription: listing.listing.short_description,
      longDescription: listing.listing.long_description,
      seoKeywords: listing.listing.seo_keywords,
      productTags: listing.listing.product_tags,
    },
    createdAt: listing.created_at,
  };
}
