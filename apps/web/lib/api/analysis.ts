import type { ProductAnalysisResult } from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiProductAnalysis {
  id: string;
  product_id: string;
  image_id: string;
  attributes: {
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

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'Product analysis failed. Please try again.';
  } catch {
    return 'Product analysis failed. Please try again.';
  }
}

function mapAnalysis(analysis: ApiProductAnalysis): ProductAnalysisResult {
  return {
    id: analysis.id,
    productId: analysis.product_id,
    imageId: analysis.image_id,
    attributes: {
      category: analysis.attributes.category,
      productType: analysis.attributes.product_type,
      color: analysis.attributes.color,
      material: analysis.attributes.material,
      style: analysis.attributes.style,
      visibleTextBrand: analysis.attributes.visible_text_brand,
      targetAudience: analysis.attributes.target_audience,
    },
    createdAt: analysis.created_at,
  };
}
