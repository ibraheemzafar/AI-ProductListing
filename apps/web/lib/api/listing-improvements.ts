import type {
  AcceptListingVersionResult,
  GeneratedListing,
  ListingImprovementResult,
  ListingVersion,
  ListingVersionHistory,
} from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiListingContent {
  title: string;
  short_description: string;
  long_description: string;
  seo_keywords: string[];
  product_tags: string[];
}

interface ApiListingVersion {
  id: string;
  listing_id: string;
  product_id: string;
  version_number: number;
  listing: ApiListingContent;
  source: string;
  is_accepted: boolean;
  created_at: string;
  accepted_at: string | null;
}

interface ApiListingImprovement {
  original_listing: ApiListingContent;
  improved_version: ApiListingVersion;
}

interface ApiListingVersionHistory {
  versions: ApiListingVersion[];
}

interface ApiAcceptListingVersion {
  listing_id: string;
  accepted_version: ApiListingVersion;
  active_listing: ApiListingContent;
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function improveListing(listingId: string): Promise<ListingImprovementResult> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/improvements`,
    {
      method: 'POST',
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapImprovement((await response.json()) as ApiListingImprovement);
}

export async function getListingVersions(listingId: string): Promise<ListingVersionHistory> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/versions`,
    {
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return {
    versions: ((await response.json()) as ApiListingVersionHistory).versions.map(mapVersion),
  };
}

export async function acceptListingVersion(
  listingId: string,
  versionId: string,
): Promise<AcceptListingVersionResult> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/versions/${versionId}/accept`,
    {
      method: 'POST',
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  const payload = (await response.json()) as ApiAcceptListingVersion;
  return {
    listingId: payload.listing_id,
    acceptedVersion: mapVersion(payload.accepted_version),
    activeListing: mapListing(payload.active_listing),
  };
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Listing improvement failed.';
  } catch {
    return 'Listing improvement failed.';
  }
}

function mapImprovement(improvement: ApiListingImprovement): ListingImprovementResult {
  return {
    originalListing: mapListing(improvement.original_listing),
    improvedVersion: mapVersion(improvement.improved_version),
  };
}

function mapVersion(version: ApiListingVersion): ListingVersion {
  return {
    id: version.id,
    listingId: version.listing_id,
    productId: version.product_id,
    versionNumber: version.version_number,
    listing: mapListing(version.listing),
    source: version.source,
    isAccepted: version.is_accepted,
    createdAt: version.created_at,
    acceptedAt: version.accepted_at,
  };
}

function mapListing(listing: ApiListingContent): GeneratedListing {
  return {
    title: listing.title,
    shortDescription: listing.short_description,
    longDescription: listing.long_description,
    seoKeywords: listing.seo_keywords,
    productTags: listing.product_tags,
  };
}
