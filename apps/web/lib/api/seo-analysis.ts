import type { SeoAnalysisResult } from '@ai-product-listing/types';

import { getPublicEnv } from '@/lib/env';

interface ApiSeoAnalysis {
  id: string;
  listing_id: string;
  product_id: string;
  analysis: {
    seo_score: number;
    readability_score: number;
    keyword_optimization_feedback: string;
    title_quality_feedback: string;
    description_quality_feedback: string;
    strengths: string[];
    weaknesses: string[];
    improvement_suggestions: string[];
  };
  created_at: string;
}

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function analyzeListingSeo(listingId: string): Promise<SeoAnalysisResult> {
  const response = await fetch(
    `${getPublicEnv().apiBaseUrl}/products/listings/${listingId}/seo-analysis`,
    {
      method: 'POST',
      credentials: 'include',
    },
  );

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  return mapSeoAnalysis((await response.json()) as ApiSeoAnalysis);
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? 'SEO analysis failed. Please try again.';
  } catch {
    return 'SEO analysis failed. Please try again.';
  }
}

function mapSeoAnalysis(analysis: ApiSeoAnalysis): SeoAnalysisResult {
  return {
    id: analysis.id,
    listingId: analysis.listing_id,
    productId: analysis.product_id,
    analysis: {
      seoScore: analysis.analysis.seo_score,
      readabilityScore: analysis.analysis.readability_score,
      keywordOptimizationFeedback: analysis.analysis.keyword_optimization_feedback,
      titleQualityFeedback: analysis.analysis.title_quality_feedback,
      descriptionQualityFeedback: analysis.analysis.description_quality_feedback,
      strengths: analysis.analysis.strengths,
      weaknesses: analysis.analysis.weaknesses,
      improvementSuggestions: analysis.analysis.improvement_suggestions,
    },
    createdAt: analysis.created_at,
  };
}
