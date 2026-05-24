import type { ListingJsonExport } from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiListingJsonExport {
  listing_id: string;
  product_id: string;
  analysis_id: string;
  product_image_url: string;
  product_analysis: {
    category: string;
    product_type: string;
    color: string;
    material: string;
    style: string;
    visible_text_brand: string;
    target_audience: string;
  };
  generated_listing: {
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

export async function getListingJsonExport(listingId: string): Promise<ListingJsonExport> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/export/json`,
    {
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapListingJsonExport((await response.json()) as ApiListingJsonExport);
}

export async function getListingShopifyCsvExport(listingId: string): Promise<Blob> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/export/shopify.csv`,
    {
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return await response.blob();
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Listing export failed. Please try again.';
  } catch {
    return 'Listing export failed. Please try again.';
  }
}

function mapListingJsonExport(exportData: ApiListingJsonExport): ListingJsonExport {
  return {
    listingId: exportData.listing_id,
    productId: exportData.product_id,
    analysisId: exportData.analysis_id,
    productImageUrl: exportData.product_image_url,
    productAnalysis: {
      category: exportData.product_analysis.category,
      productType: exportData.product_analysis.product_type,
      color: exportData.product_analysis.color,
      material: exportData.product_analysis.material,
      style: exportData.product_analysis.style,
      visibleTextBrand: exportData.product_analysis.visible_text_brand,
      targetAudience: exportData.product_analysis.target_audience,
    },
    generatedListing: {
      title: exportData.generated_listing.title,
      shortDescription: exportData.generated_listing.short_description,
      longDescription: exportData.generated_listing.long_description,
      seoKeywords: exportData.generated_listing.seo_keywords,
      productTags: exportData.generated_listing.product_tags,
    },
    createdAt: exportData.created_at,
  };
}
