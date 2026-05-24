import type { EnhancedImageResult, ImageEnhancementOperation } from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiEnhancedImage {
  id: string;
  product_id: string;
  original_image_id: string;
  operation: ImageEnhancementOperation;
  provider_name: string;
  enhanced_image_url: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function enhanceListingImage(
  listingId: string,
  operation: ImageEnhancementOperation,
): Promise<EnhancedImageResult> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/image-enhancements`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ operation }),
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapEnhancedImage((await response.json()) as ApiEnhancedImage);
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Image enhancement failed.';
  } catch {
    return 'Image enhancement failed.';
  }
}

function mapEnhancedImage(image: ApiEnhancedImage): EnhancedImageResult {
  return {
    id: image.id,
    productId: image.product_id,
    originalImageId: image.original_image_id,
    operation: image.operation,
    providerName: image.provider_name,
    enhancedImageUrl: image.enhanced_image_url,
    contentType: image.content_type,
    sizeBytes: image.size_bytes,
    createdAt: image.created_at,
  };
}
