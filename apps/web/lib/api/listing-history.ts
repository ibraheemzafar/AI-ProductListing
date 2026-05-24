import { cookies } from 'next/headers';

import type {
  ListingDetail,
  ListingHistory,
  ListingHistoryItem,
  UploadedProductImage,
} from '@ai-product-listing/types';

import { getServerEnv } from '@/lib/env';

interface ApiUploadedImage {
  id: string;
  product_id: string;
  original_filename: string;
  image_url: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

interface ApiListingHistoryItem {
  id: string;
  product_id: string;
  analysis_id: string;
  title: string;
  short_description: string;
  image: ApiUploadedImage;
  status: string;
  created_at: string;
}

interface ApiListingHistory {
  listings: ApiListingHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

interface ApiListingDetail {
  id: string;
  product_id: string;
  analysis_id: string;
  image: ApiUploadedImage;
  analysis: {
    category: string;
    product_type: string;
    color: string;
    material: string;
    style: string;
    visible_text_brand: string;
    target_audience: string;
  };
  listing: {
    title: string;
    short_description: string;
    long_description: string;
    seo_keywords: string[];
    product_tags: string[];
  };
  status: string;
  created_at: string;
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function getListingHistory(limit = 20, offset = 0): Promise<ListingHistory> {
  const cookieStore = await cookies();
  const response = await fetch(
    `${getServerEnv().apiBaseUrl}/products/listings?limit=${limit}&offset=${offset}`,
    {
      cache: 'no-store',
      headers: {
        Cookie: cookieStore.toString(),
      },
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapListingHistory((await response.json()) as ApiListingHistory);
}

export async function getListingDetail(listingId: string): Promise<ListingDetail> {
  const cookieStore = await cookies();
  const response = await fetch(`${getServerEnv().apiBaseUrl}/products/listings/${listingId}`, {
    cache: 'no-store',
    headers: {
      Cookie: cookieStore.toString(),
    },
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapListingDetail((await response.json()) as ApiListingDetail);
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Listing history failed to load.';
  } catch {
    return 'Listing history failed to load.';
  }
}

function mapListingHistory(history: ApiListingHistory): ListingHistory {
  return {
    listings: history.listings.map(mapListingHistoryItem),
    total: history.total,
    limit: history.limit,
    offset: history.offset,
  };
}

function mapListingHistoryItem(listing: ApiListingHistoryItem): ListingHistoryItem {
  return {
    id: listing.id,
    productId: listing.product_id,
    analysisId: listing.analysis_id,
    title: listing.title,
    shortDescription: listing.short_description,
    image: mapUploadedImage(listing.image),
    status: listing.status,
    createdAt: listing.created_at,
  };
}

function mapListingDetail(detail: ApiListingDetail): ListingDetail {
  return {
    id: detail.id,
    productId: detail.product_id,
    analysisId: detail.analysis_id,
    image: mapUploadedImage(detail.image),
    analysis: {
      category: detail.analysis.category,
      productType: detail.analysis.product_type,
      color: detail.analysis.color,
      material: detail.analysis.material,
      style: detail.analysis.style,
      visibleTextBrand: detail.analysis.visible_text_brand,
      targetAudience: detail.analysis.target_audience,
    },
    listing: {
      title: detail.listing.title,
      shortDescription: detail.listing.short_description,
      longDescription: detail.listing.long_description,
      seoKeywords: detail.listing.seo_keywords,
      productTags: detail.listing.product_tags,
    },
    status: detail.status,
    createdAt: detail.created_at,
  };
}

function mapUploadedImage(image: ApiUploadedImage): UploadedProductImage {
  return {
    id: image.id,
    productId: image.product_id,
    originalFilename: image.original_filename,
    imageUrl: image.image_url,
    contentType: image.content_type,
    sizeBytes: image.size_bytes,
    createdAt: image.created_at,
  };
}
