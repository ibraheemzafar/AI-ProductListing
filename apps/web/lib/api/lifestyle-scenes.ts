import type { GeneratedSceneGallery, GeneratedSceneImage, ScenePreset } from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiGeneratedSceneImage {
  id: string;
  user_id: string;
  product_id: string;
  listing_id: string;
  source_product_image_id: string;
  source_enhanced_image_id: string | null;
  category: ScenePreset;
  custom_prompt: string | null;
  prompt: string;
  provider: string;
  generated_image_url: string;
  content_type: string;
  size_bytes: number;
  generation_time_ms: number;
  status: string;
  created_at: string;
}

interface ApiGeneratedSceneGallery {
  images: ApiGeneratedSceneImage[];
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function generateLifestyleScene(
  listingId: string,
  category: ScenePreset,
  customPrompt: string,
): Promise<GeneratedSceneImage> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/generated-images`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        category,
        custom_prompt: customPrompt.trim() || null,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapGeneratedScene((await response.json()) as ApiGeneratedSceneImage);
}

export async function getGeneratedLifestyleScenes(
  listingId: string,
): Promise<GeneratedSceneGallery> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/generated-images`,
    {
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  const payload = (await response.json()) as ApiGeneratedSceneGallery;
  return {
    images: payload.images.map(mapGeneratedScene),
  };
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Lifestyle scene generation failed.';
  } catch {
    return 'Lifestyle scene generation failed.';
  }
}

function mapGeneratedScene(image: ApiGeneratedSceneImage): GeneratedSceneImage {
  return {
    id: image.id,
    userId: image.user_id,
    productId: image.product_id,
    listingId: image.listing_id,
    sourceProductImageId: image.source_product_image_id,
    sourceEnhancedImageId: image.source_enhanced_image_id,
    category: image.category,
    customPrompt: image.custom_prompt,
    prompt: image.prompt,
    provider: image.provider,
    generatedImageUrl: image.generated_image_url,
    contentType: image.content_type,
    sizeBytes: image.size_bytes,
    generationTimeMs: image.generation_time_ms,
    status: image.status,
    createdAt: image.created_at,
  };
}

export async function downloadGeneratedLifestyleScene(
  listingId: string,
  imageId: string,
): Promise<Blob> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/generated-images/${imageId}/download`,
    {
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return response.blob();
}

export async function deleteGeneratedLifestyleScene(
  listingId: string,
  imageId: string,
): Promise<void> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/generated-images/${imageId}`,
    {
      method: 'DELETE',
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
}
