import type { ProductAnalysisResult } from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiProductAnalysis {
  id: string;
  product_id: string;
  image_id: string;
  valid_product: boolean;
  confidence: number;
  reason: string | null;
  attributes: {
    valid_product: boolean;
    confidence: number;
    reason: string | null;
    category: string;
    product_type: string;
    color: string;
    material: string;
    style: string;
    visible_text_brand: string;
    target_audience: string;
  };
  created_at: string;
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function analyzeProductImage(imageId: string): Promise<ProductAnalysisResult> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/products/images/${imageId}/analysis`, {
    method: 'POST',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapAnalysis((await response.json()) as ApiProductAnalysis);
}

export async function getAnalysisVersions(
  imageId: string,
): Promise<ProductAnalysisResult[]> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/products/images/${imageId}/analyses`, {
    method: 'GET',
    credentials: 'include',
  });

  if (!response.ok) {
    return [];
  }

  const payload = (await response.json()) as ApiProductAnalysis[] | null;
  return (payload ?? []).map(mapAnalysis);
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Product Intelligence failed. Please try again.';
  } catch {
    return 'Product Intelligence failed. Please try again.';
  }
}

function mapAnalysis(analysis: ApiProductAnalysis): ProductAnalysisResult {
  return {
    id: analysis.id,
    productId: analysis.product_id,
    imageId: analysis.image_id,
    attributes: {
      validProduct: analysis.attributes.valid_product ?? analysis.valid_product ?? true,
      confidence: analysis.attributes.confidence ?? analysis.confidence ?? 1,
      reason: analysis.attributes.reason ?? analysis.reason ?? null,
      category: analysis.attributes.category,
      productType: analysis.attributes.product_type,
      color: analysis.attributes.color,
      material: analysis.attributes.material,
      style: analysis.attributes.style,
      visibleTextBrand: analysis.attributes.visible_text_brand,
      targetAudience: analysis.attributes.target_audience,
    },
    validProduct: analysis.valid_product ?? analysis.attributes.valid_product ?? true,
    confidence: analysis.confidence ?? analysis.attributes.confidence ?? 1,
    reason: analysis.reason ?? analysis.attributes.reason ?? null,
    createdAt: analysis.created_at,
  };
}
