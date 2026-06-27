export interface ApiError {
  code: string;
  message: string;
}

export interface ApiResponse<TData> {
  data: TData;
  error: ApiError | null;
}

export interface GeneratedListingDraft {
  title: string;
  shortDescription: string;
  seoKeywords: string[];
}

export interface AuthenticatedUser {
  id: string;
  email: string;
  name: string | null;
  avatarUrl: string | null;
}

export interface AuthSession {
  user: AuthenticatedUser;
}

export interface UploadedProductImage {
  id: string;
  productId: string;
  originalFilename: string;
  imageUrl: string;
  contentType: string;
  sizeBytes: number;
  createdAt: string;
}

export interface ProductImageList {
  images: UploadedProductImage[];
}

export interface ProductUploadResult {
  productId: string;
  images: UploadedProductImage[];
}

export interface ProductAttributes {
  category: string;
  productType: string;
  color: string;
  material: string;
  style: string;
  visibleTextBrand: string;
  targetAudience: string;
}

export interface ProductAnalysisResult {
  id: string;
  productId: string;
  imageId: string;
  attributes: ProductAttributes;
  createdAt: string;
}

export interface GeneratedListing {
  title: string;
  shortDescription: string;
  longDescription: string;
  seoKeywords: string[];
  productTags: string[];
}

export interface GeneratedListingResult {
  id: string;
  productId: string;
  analysisId: string;
  listing: GeneratedListing;
  createdAt: string;
}

export interface ListingHistoryItem {
  id: string;
  productId: string;
  analysisId: string;
  title: string;
  shortDescription: string;
  image: UploadedProductImage;
  status: string;
  createdAt: string;
}

export interface ListingHistory {
  listings: ListingHistoryItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface ListingDetail {
  id: string;
  productId: string;
  analysisId: string;
  image: UploadedProductImage;
  analysis: ProductAttributes;
  listing: GeneratedListing;
  status: string;
  createdAt: string;
}

export interface ListingJsonExport {
  listingId: string;
  productId: string;
  analysisId: string;
  productImageUrl: string;
  productAnalysis: ProductAttributes;
  generatedListing: GeneratedListing;
  createdAt: string;
}

export interface SeoEvaluation {
  seoScore: number;
  readabilityScore: number;
  keywordOptimizationFeedback: string;
  titleQualityFeedback: string;
  descriptionQualityFeedback: string;
  strengths: string[];
  weaknesses: string[];
  improvementSuggestions: string[];
}

export interface SeoAnalysisResult {
  id: string;
  listingId: string;
  productId: string;
  analysis: SeoEvaluation;
  createdAt: string;
}

export interface ListingVersion {
  id: string;
  listingId: string;
  productId: string;
  versionNumber: number;
  listing: GeneratedListing;
  source: string;
  isAccepted: boolean;
  createdAt: string;
  acceptedAt: string | null;
}

export interface ListingImprovementResult {
  originalListing: GeneratedListing;
  improvedVersion: ListingVersion;
}

export interface ListingVersionHistory {
  versions: ListingVersion[];
}

export interface AcceptListingVersionResult {
  listingId: string;
  acceptedVersion: ListingVersion;
  activeListing: GeneratedListing;
}

export type Marketplace =
  | 'shopify'
  | 'amazon'
  | 'etsy'
  | 'daraz'
  | 'woocommerce'
  | 'ebay'
  | 'generic_store';

export interface MarketplaceOptimization {
  optimizedTitle: string;
  optimizedDescription: string;
  bulletPoints: string[];
  keywordsTags: string[];
  platformNotes: string;
}

export interface MarketplaceOptimizationResult {
  id: string;
  listingId: string;
  productId: string;
  marketplace: Marketplace;
  optimization: MarketplaceOptimization;
  createdAt: string;
}

export type ImageEnhancementOperation =
  | 'background_removal'
  | 'image_cleanup'
  | 'image_optimization';

export interface EnhancedImageResult {
  id: string;
  productId: string;
  originalImageId: string;
  operation: ImageEnhancementOperation;
  providerName: string;
  enhancedImageUrl: string;
  contentType: string;
  sizeBytes: number;
  createdAt: string;
}

export type ScenePreset =
  | 'studio_white_background'
  | 'luxury_product_shot'
  | 'wooden_table_setup'
  | 'minimal_ecommerce_background'
  | 'lifestyle_home_setup'
  | 'social_media_banner'
  | 'marketplace_hero_image'
  | 'custom_prompt';

export interface GeneratedSceneImage {
  id: string;
  userId: string;
  productId: string;
  listingId: string;
  sourceProductImageId: string;
  sourceEnhancedImageId: string | null;
  category: ScenePreset;
  customPrompt: string | null;
  prompt: string;
  provider: string;
  generatedImageUrl: string;
  contentType: string;
  sizeBytes: number;
  generationTimeMs: number;
  status: string;
  createdAt: string;
}

export interface GeneratedSceneGallery {
  images: GeneratedSceneImage[];
}
