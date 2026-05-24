'use client';

import {
  Clipboard,
  Download,
  ImageIcon,
  SearchCheck,
  ShoppingBag,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import type {
  GeneratedListing,
  GeneratedSceneImage,
  EnhancedImageResult,
  ImageEnhancementOperation,
  ListingDetail,
  ListingImprovementResult,
  ListingVersion,
  Marketplace,
  MarketplaceOptimizationResult,
  ScenePreset,
  SeoAnalysisResult,
} from '@ai-product-listing/types';
import { Button } from '@/components/ui/button';
import { enhanceListingImage } from '@/lib/api/image-enhancements';
import {
  deleteGeneratedLifestyleScene,
  downloadGeneratedLifestyleScene,
  generateLifestyleScene,
  getGeneratedLifestyleScenes,
} from '@/lib/api/lifestyle-scenes';
import { getListingJsonExport, getListingShopifyCsvExport } from '@/lib/api/listing-exports';
import {
  acceptListingVersion,
  getListingVersions,
  improveListing,
} from '@/lib/api/listing-improvements';
import { optimizeListingForMarketplace } from '@/lib/api/marketplace-optimizations';
import { analyzeListingSeo } from '@/lib/api/seo-analysis';

interface ListingDetailViewProps {
  listing: ListingDetail;
}

export function ListingDetailView({ listing }: ListingDetailViewProps) {
  const [activeListing, setActiveListing] = useState<GeneratedListing>(listing.listing);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isJsonExporting, setIsJsonExporting] = useState(false);
  const [isShopifyExporting, setIsShopifyExporting] = useState(false);
  const [isSeoAnalyzing, setIsSeoAnalyzing] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [isMarketplaceOptimizing, setIsMarketplaceOptimizing] = useState(false);
  const [isImageEnhancing, setIsImageEnhancing] = useState(false);
  const [selectedMarketplace, setSelectedMarketplace] = useState<Marketplace>('shopify');
  const [selectedEnhancement, setSelectedEnhancement] =
    useState<ImageEnhancementOperation>('background_removal');
  const [selectedSceneCategory, setSelectedSceneCategory] =
    useState<ScenePreset>('marketplace_hero_image');
  const [customScenePrompt, setCustomScenePrompt] = useState('');
  const [acceptingVersionId, setAcceptingVersionId] = useState<string | null>(null);
  const [seoAnalysis, setSeoAnalysis] = useState<SeoAnalysisResult | null>(null);
  const [seoErrorMessage, setSeoErrorMessage] = useState<string | null>(null);
  const [improvement, setImprovement] = useState<ListingImprovementResult | null>(null);
  const [versions, setVersions] = useState<ListingVersion[]>([]);
  const [improvementErrorMessage, setImprovementErrorMessage] = useState<string | null>(null);
  const [marketplaceOptimization, setMarketplaceOptimization] =
    useState<MarketplaceOptimizationResult | null>(null);
  const [marketplaceErrorMessage, setMarketplaceErrorMessage] = useState<string | null>(null);
  const [enhancedImage, setEnhancedImage] = useState<EnhancedImageResult | null>(null);
  const [imageEnhancementErrorMessage, setImageEnhancementErrorMessage] =
    useState<string | null>(null);
  const [isSceneGenerating, setIsSceneGenerating] = useState(false);
  const [generatedImage, setGeneratedImage] = useState<GeneratedSceneImage | null>(null);
  const [generatedImages, setGeneratedImages] = useState<GeneratedSceneImage[]>([]);
  const [generatedImageErrorMessage, setGeneratedImageErrorMessage] = useState<string | null>(null);
  const [deletingGeneratedImageId, setDeletingGeneratedImageId] = useState<string | null>(null);
  const keywords = activeListing.seoKeywords.join(', ');
  const tags = activeListing.productTags.join(', ');

  useEffect(() => {
    void loadVersions();
    void loadGeneratedImages();
  }, []);

  async function copyText(key: string, value: string) {
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
      showToast('Copied to clipboard.');
      window.setTimeout(() => setCopiedKey(null), 1500);
    } catch {
      showToast('Copy failed. Please try again.');
    }
  }

  async function copyAll() {
    try {
      const exportData = await getListingJsonExport(listing.id);
      await navigator.clipboard.writeText(JSON.stringify(exportData, null, 2));
      setCopiedKey('copy-all');
      showToast('Full listing copied.');
      window.setTimeout(() => setCopiedKey(null), 1500);
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Copy failed. Please try again.');
    }
  }

  async function downloadJson() {
    setIsJsonExporting(true);
    try {
      const exportData = await getListingJsonExport(listing.id);
      const json = JSON.stringify(exportData, null, 2);
      const url = URL.createObjectURL(new Blob([json], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${listing.id}.json`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('JSON export downloaded.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Download failed. Please try again.');
    } finally {
      setIsJsonExporting(false);
    }
  }

  async function downloadShopifyCsv() {
    setIsShopifyExporting(true);
    try {
      const csv = await getListingShopifyCsvExport(listing.id);
      const url = URL.createObjectURL(csv);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${listing.id}-shopify.csv`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('Shopify CSV downloaded.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Download failed. Please try again.');
    } finally {
      setIsShopifyExporting(false);
    }
  }

  async function handleAnalyzeSeo() {
    setIsSeoAnalyzing(true);
    setSeoErrorMessage(null);
    try {
      const result = await analyzeListingSeo(listing.id);
      setSeoAnalysis(result);
      showToast('SEO analysis completed.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'SEO analysis failed.';
      setSeoErrorMessage(message);
      showToast(message);
    } finally {
      setIsSeoAnalyzing(false);
    }
  }

  async function handleImproveListing() {
    setIsImproving(true);
    setImprovementErrorMessage(null);
    try {
      const result = await improveListing(listing.id);
      setImprovement(result);
      setVersions((current) => [result.improvedVersion, ...current]);
      showToast('Improved version created.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Listing improvement failed.';
      setImprovementErrorMessage(message);
      showToast(message);
    } finally {
      setIsImproving(false);
    }
  }

  async function handleMarketplaceOptimization() {
    setIsMarketplaceOptimizing(true);
    setMarketplaceErrorMessage(null);
    try {
      const result = await optimizeListingForMarketplace(listing.id, selectedMarketplace);
      setMarketplaceOptimization(result);
      showToast('Marketplace optimization completed.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Marketplace optimization failed.';
      setMarketplaceErrorMessage(message);
      showToast(message);
    } finally {
      setIsMarketplaceOptimizing(false);
    }
  }

  async function handleEnhanceImage() {
    setIsImageEnhancing(true);
    setImageEnhancementErrorMessage(null);
    try {
      const result = await enhanceListingImage(listing.id, selectedEnhancement);
      setEnhancedImage(result);
      showToast('Image enhancement completed.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Image enhancement failed.';
      setImageEnhancementErrorMessage(message);
      showToast(message);
    } finally {
      setIsImageEnhancing(false);
    }
  }

  function downloadEnhancedImage() {
    if (!enhancedImage) {
      return;
    }
    const link = document.createElement('a');
    link.href = enhancedImage.enhancedImageUrl;
    link.download = `${listing.id}-${enhancedImage.operation}.png`;
    link.click();
    showToast('Enhanced image download started.');
  }

  async function handleGenerateImage() {
    setIsSceneGenerating(true);
    setGeneratedImageErrorMessage(null);
    try {
      const result = await generateLifestyleScene(
        listing.id,
        selectedSceneCategory,
        customScenePrompt,
      );
      setGeneratedImage(result);
      setGeneratedImages((current) => [result, ...current]);
      showToast('Generated image saved.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Image generation failed.';
      setGeneratedImageErrorMessage(message);
      showToast(message);
    } finally {
      setIsSceneGenerating(false);
    }
  }

  async function downloadGeneratedImage(image: GeneratedSceneImage) {
    try {
      const blob = await downloadGeneratedLifestyleScene(listing.id, image.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${listing.id}-${image.category}.png`;
      link.click();
      URL.revokeObjectURL(url);
      showToast('Generated image download started.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Download failed. Please try again.');
    }
  }

  async function deleteGeneratedImage(image: GeneratedSceneImage) {
    const confirmed = window.confirm('Delete this generated image?');
    if (!confirmed) {
      return;
    }

    setDeletingGeneratedImageId(image.id);
    try {
      await deleteGeneratedLifestyleScene(listing.id, image.id);
      setGeneratedImages((current) => current.filter((item) => item.id !== image.id));
      setGeneratedImage((current) => (current?.id === image.id ? null : current));
      showToast('Generated image deleted.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Delete failed. Please try again.');
    } finally {
      setDeletingGeneratedImageId(null);
    }
  }

  async function handleAcceptVersion(version: ListingVersion) {
    setAcceptingVersionId(version.id);
    try {
      const result = await acceptListingVersion(listing.id, version.id);
      setActiveListing(result.activeListing);
      setVersions((current) =>
        current.map((item) => ({
          ...item,
          isAccepted: item.id === result.acceptedVersion.id,
          acceptedAt: item.id === result.acceptedVersion.id ? result.acceptedVersion.acceptedAt : null,
        })),
      );
      showToast('Improved version accepted.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Could not accept version.');
    } finally {
      setAcceptingVersionId(null);
    }
  }

  async function loadVersions() {
    try {
      const history = await getListingVersions(listing.id);
      setVersions(history.versions);
    } catch {
      setVersions([]);
    }
  }

  async function loadGeneratedImages() {
    try {
      const gallery = await getGeneratedLifestyleScenes(listing.id);
      setGeneratedImages(gallery.images);
      setGeneratedImage(gallery.images[0] ?? null);
    } catch {
      setGeneratedImages([]);
    }
  }

  function showToast(message: string) {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 2500);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[360px_minmax(0,1fr)]">
      <section className="grid gap-5">
        <img
          alt={listing.image.originalFilename}
          className="aspect-square w-full rounded-md object-cover"
          src={listing.image.imageUrl}
        />
        <div className="rounded-md border border-border p-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-medium">Product analysis</h2>
            <span className="rounded bg-muted px-2 py-1 text-xs capitalize text-muted-foreground">
              {listing.status}
            </span>
          </div>
          <dl className="mt-4 grid gap-2 text-sm">
            {[
              ['Category', listing.analysis.category],
              ['Product type', listing.analysis.productType],
              ['Color', listing.analysis.color],
              ['Material', listing.analysis.material],
              ['Style', listing.analysis.style],
              ['Visible text/brand', listing.analysis.visibleTextBrand],
              ['Target audience', listing.analysis.targetAudience],
            ].map(([label, value]) => (
              <div key={label} className="grid grid-cols-[130px_minmax(0,1fr)] gap-3">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="min-w-0 break-words font-medium">{value}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      <section className="grid gap-4">
        {toastMessage ? (
          <div className="rounded-md border border-border bg-muted px-4 py-3 text-sm">
            {toastMessage}
          </div>
        ) : null}

        <div className="flex flex-wrap gap-3 rounded-md border border-border p-4">
          <Button type="button" onClick={copyAll}>
            <Clipboard className="mr-2 size-4" aria-hidden="true" />
            {copiedKey === 'copy-all' ? 'Copied All' : 'Copy All'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={downloadJson}
            disabled={isJsonExporting}
          >
            <Download className="mr-2 size-4" aria-hidden="true" />
            {isJsonExporting ? 'Downloading' : 'Download JSON'}
          </Button>
          <Button
            type="button"
            variant="secondary"
            onClick={downloadShopifyCsv}
            disabled={isShopifyExporting}
          >
            <Download className="mr-2 size-4" aria-hidden="true" />
            {isShopifyExporting ? 'Downloading' : 'Download Shopify CSV'}
          </Button>
          <Button type="button" onClick={handleAnalyzeSeo} disabled={isSeoAnalyzing}>
            <SearchCheck className="mr-2 size-4" aria-hidden="true" />
            {isSeoAnalyzing ? 'Analyzing SEO' : 'Analyze SEO'}
          </Button>
          <Button type="button" onClick={handleImproveListing} disabled={isImproving}>
            <Sparkles className="mr-2 size-4" aria-hidden="true" />
            {isImproving ? 'Improving' : 'Improve with AI'}
          </Button>
          <div className="flex flex-wrap gap-2">
            <select
              aria-label="Marketplace"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={selectedMarketplace}
              onChange={(event) => setSelectedMarketplace(event.target.value as Marketplace)}
              disabled={isMarketplaceOptimizing}
            >
              <option value="shopify">Shopify</option>
              <option value="amazon">Amazon</option>
              <option value="etsy">Etsy</option>
              <option value="daraz">Daraz</option>
            </select>
            <Button
              type="button"
              onClick={handleMarketplaceOptimization}
              disabled={isMarketplaceOptimizing}
            >
              <ShoppingBag className="mr-2 size-4" aria-hidden="true" />
              {isMarketplaceOptimizing ? 'Optimizing' : 'Optimize for Marketplace'}
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              aria-label="Image enhancement"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={selectedEnhancement}
              onChange={(event) =>
                setSelectedEnhancement(event.target.value as ImageEnhancementOperation)
              }
              disabled={isImageEnhancing}
            >
              <option value="background_removal">Background removal</option>
              <option value="image_cleanup">Image cleanup</option>
              <option value="image_optimization">Image optimization</option>
            </select>
            <Button type="button" onClick={handleEnhanceImage} disabled={isImageEnhancing}>
              <ImageIcon className="mr-2 size-4" aria-hidden="true" />
              {isImageEnhancing ? 'Enhancing Image' : 'Enhance Image'}
            </Button>
          </div>
          <div className="grid w-full gap-2 md:grid-cols-[220px_minmax(0,1fr)_auto]">
            <select
              aria-label="Image generation category"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              value={selectedSceneCategory}
              onChange={(event) => setSelectedSceneCategory(event.target.value as ScenePreset)}
              disabled={isSceneGenerating}
            >
              <option value="studio_white_background">Studio white background</option>
              <option value="luxury_product_shot">Luxury product shot</option>
              <option value="wooden_table_setup">Wooden table setup</option>
              <option value="minimal_ecommerce_background">Minimal ecommerce background</option>
              <option value="lifestyle_home_setup">Lifestyle home setup</option>
              <option value="social_media_banner">Social media banner</option>
              <option value="marketplace_hero_image">Marketplace hero image</option>
              <option value="custom_prompt">Custom prompt</option>
            </select>
            {selectedSceneCategory === 'custom_prompt' ? (
              <input
                aria-label="Custom image generation prompt"
                className="h-10 min-w-0 rounded-md border border-input bg-background px-3 text-sm"
                value={customScenePrompt}
                onChange={(event) => setCustomScenePrompt(event.target.value)}
                placeholder="Describe the generated product scene"
                disabled={isSceneGenerating}
              />
            ) : (
              <div className="hidden md:block" />
            )}
            <Button
              type="button"
              onClick={handleGenerateImage}
              disabled={
                isSceneGenerating ||
                (selectedSceneCategory === 'custom_prompt' && !customScenePrompt.trim())
              }
            >
              <ImageIcon className="mr-2 size-4" aria-hidden="true" />
              {isSceneGenerating ? 'Generating' : 'Generate Image'}
            </Button>
          </div>
        </div>

        {seoErrorMessage ? <p className="text-sm text-red-600">{seoErrorMessage}</p> : null}

        {seoAnalysis ? <SeoAnalysisPanel result={seoAnalysis} /> : null}

        {improvementErrorMessage ? (
          <p className="text-sm text-red-600">{improvementErrorMessage}</p>
        ) : null}

        {improvement ? (
          <BeforeAfterComparison
            improvement={improvement}
            acceptingVersionId={acceptingVersionId}
            onAccept={handleAcceptVersion}
          />
        ) : null}

        {marketplaceErrorMessage ? (
          <p className="text-sm text-red-600">{marketplaceErrorMessage}</p>
        ) : null}

        {marketplaceOptimization ? (
          <MarketplaceOptimizationPanel
            result={marketplaceOptimization}
            copiedKey={copiedKey}
            onCopy={copyText}
          />
        ) : null}

        {imageEnhancementErrorMessage ? (
          <p className="text-sm text-red-600">{imageEnhancementErrorMessage}</p>
        ) : null}

        {isImageEnhancing ? <ImageProcessingProgress /> : null}

        {enhancedImage ? (
          <ImageEnhancementPanel
            originalImageUrl={listing.image.imageUrl}
            enhancedImage={enhancedImage}
            onDownload={downloadEnhancedImage}
          />
        ) : null}

        {generatedImageErrorMessage ? (
          <p className="text-sm text-red-600">{generatedImageErrorMessage}</p>
        ) : null}

        {isSceneGenerating ? <ImageProcessingProgress label="Generating image" /> : null}

        {generatedImage ? (
          <GeneratedImagePanel
            image={generatedImage}
            onDownload={downloadGeneratedImage}
            onDelete={deleteGeneratedImage}
            isDeleting={deletingGeneratedImageId === generatedImage.id}
          />
        ) : null}

        <GeneratedImageGallery
          images={generatedImages}
          deletingGeneratedImageId={deletingGeneratedImageId}
          onDownload={downloadGeneratedImage}
          onDelete={deleteGeneratedImage}
        />

        <VersionHistory
          versions={versions}
          acceptingVersionId={acceptingVersionId}
          onAccept={handleAcceptVersion}
        />

        <CopyField
          label="Title"
          value={activeListing.title}
          copyKey="title"
          copiedKey={copiedKey}
          onCopy={copyText}
        />
        <CopyField
          label="Short description"
          value={activeListing.shortDescription}
          copyKey="short-description"
          copiedKey={copiedKey}
          onCopy={copyText}
        />
        <CopyField
          label="Long description"
          value={activeListing.longDescription}
          copyKey="long-description"
          copiedKey={copiedKey}
          onCopy={copyText}
        />
        <CopyField
          label="SEO keywords"
          value={keywords}
          copyKey="seo-keywords"
          copiedKey={copiedKey}
          onCopy={copyText}
        />
        <CopyField
          label="Product tags"
          value={tags}
          copyKey="product-tags"
          copiedKey={copiedKey}
          onCopy={copyText}
        />
      </section>
    </div>
  );
}

function ImageProcessingProgress({ label = 'Image processing' }: { label?: string }) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-medium">{label}</h2>
        <span className="text-sm text-muted-foreground">In progress</span>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded bg-muted">
        <div className="h-full w-2/3 animate-pulse bg-primary" />
      </div>
      <ol className="mt-4 grid gap-2 text-sm text-muted-foreground sm:grid-cols-3">
        <li className="rounded bg-muted px-3 py-2">Preparing image</li>
        <li className="rounded bg-muted px-3 py-2">Processing image</li>
        <li className="rounded bg-muted px-3 py-2">Saving result</li>
      </ol>
    </section>
  );
}

const sceneCategoryLabels: Record<ScenePreset, string> = {
  studio_white_background: 'Studio white background',
  luxury_product_shot: 'Luxury product shot',
  wooden_table_setup: 'Wooden table setup',
  minimal_ecommerce_background: 'Minimal ecommerce background',
  lifestyle_home_setup: 'Lifestyle home setup',
  social_media_banner: 'Social media banner',
  marketplace_hero_image: 'Marketplace hero image',
  custom_prompt: 'Custom prompt',
};

interface GeneratedImagePanelProps {
  image: GeneratedSceneImage;
  onDownload: (image: GeneratedSceneImage) => Promise<void>;
  onDelete: (image: GeneratedSceneImage) => Promise<void>;
  isDeleting: boolean;
}

function GeneratedImagePanel({
  image,
  onDownload,
  onDelete,
  isDeleting,
}: GeneratedImagePanelProps) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-medium">Generated image</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {sceneCategoryLabels[image.category]} via {image.provider}
          </p>
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="secondary" onClick={() => onDownload(image)}>
            <Download className="mr-2 size-4" aria-hidden="true" />
            Download
          </Button>
          <Button type="button" variant="secondary" onClick={() => onDelete(image)} disabled={isDeleting}>
            <Trash2 className="mr-2 size-4" aria-hidden="true" />
            {isDeleting ? 'Deleting' : 'Delete'}
          </Button>
        </div>
      </div>
      <img
        alt={`${sceneCategoryLabels[image.category]} generated product image`}
        className="mt-4 aspect-square w-full rounded-md border border-border object-cover"
        src={image.generatedImageUrl}
      />
    </section>
  );
}

interface GeneratedImageGalleryProps {
  images: GeneratedSceneImage[];
  deletingGeneratedImageId: string | null;
  onDownload: (image: GeneratedSceneImage) => Promise<void>;
  onDelete: (image: GeneratedSceneImage) => Promise<void>;
}

function GeneratedImageGallery({
  images,
  deletingGeneratedImageId,
  onDownload,
  onDelete,
}: GeneratedImageGalleryProps) {
  return (
    <section className="rounded-md border border-border p-4">
      <h2 className="text-base font-medium">Generated images</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {images.length > 0 ? (
          images.map((image) => (
            <div key={image.id} className="rounded-md border border-border p-3">
              <img
                alt={`${sceneCategoryLabels[image.category]} preview`}
                className="aspect-square w-full rounded-md object-cover"
                src={image.generatedImageUrl}
              />
              <div className="mt-3 grid gap-1">
                <p className="text-sm font-medium">{sceneCategoryLabels[image.category]}</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(image.createdAt).toLocaleDateString()}
                </p>
              </div>
              <div className="mt-3 flex gap-2">
                <Button type="button" variant="secondary" onClick={() => onDownload(image)}>
                  <Download className="mr-2 size-4" aria-hidden="true" />
                  Download
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => onDelete(image)}
                  disabled={deletingGeneratedImageId === image.id}
                >
                  <Trash2 className="mr-2 size-4" aria-hidden="true" />
                  {deletingGeneratedImageId === image.id ? 'Deleting' : 'Delete'}
                </Button>
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No generated images yet.</p>
        )}
      </div>
    </section>
  );
}

interface ImageEnhancementPanelProps {
  originalImageUrl: string;
  enhancedImage: EnhancedImageResult;
  onDownload: () => void;
}

function ImageEnhancementPanel({
  originalImageUrl,
  enhancedImage,
  onDownload,
}: ImageEnhancementPanelProps) {
  const operationLabels: Record<ImageEnhancementOperation, string> = {
    background_removal: 'Background removal',
    image_cleanup: 'Image cleanup',
    image_optimization: 'Image optimization',
  };

  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-medium">Image enhancement</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {operationLabels[enhancedImage.operation]} via {enhancedImage.providerName}
          </p>
        </div>
        <Button type="button" variant="secondary" onClick={onDownload}>
          <Download className="mr-2 size-4" aria-hidden="true" />
          Download enhanced image
        </Button>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <ImageComparisonFrame label="Before" imageUrl={originalImageUrl} />
        <ImageComparisonFrame label="After" imageUrl={enhancedImage.enhancedImageUrl} />
      </div>
    </section>
  );
}

function ImageComparisonFrame({ label, imageUrl }: { label: string; imageUrl: string }) {
  return (
    <div>
      <h3 className="text-sm font-medium">{label}</h3>
      <img
        alt={`${label} product image`}
        className="mt-2 aspect-square w-full rounded-md border border-border object-cover"
        src={imageUrl}
      />
    </div>
  );
}

interface MarketplaceOptimizationPanelProps {
  result: MarketplaceOptimizationResult;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => Promise<void>;
}

function MarketplaceOptimizationPanel({
  result,
  copiedKey,
  onCopy,
}: MarketplaceOptimizationPanelProps) {
  const marketplaceLabels: Record<Marketplace, string> = {
    shopify: 'Shopify',
    amazon: 'Amazon',
    etsy: 'Etsy',
    daraz: 'Daraz',
  };
  const marketplaceLabel = marketplaceLabels[result.marketplace];
  const bullets = result.optimization.bulletPoints.join('\n');
  const keywords = result.optimization.keywordsTags.join(', ');

  return (
    <section className="rounded-md border border-border p-4">
      <h2 className="text-base font-medium">{marketplaceLabel} optimized output</h2>
      <div className="mt-4 grid gap-4">
        <MarketplaceCopySection
          label="Optimized title"
          value={result.optimization.optimizedTitle}
          copyKey="marketplace-title"
          copiedKey={copiedKey}
          onCopy={onCopy}
        />
        <MarketplaceCopySection
          label="Optimized description"
          value={result.optimization.optimizedDescription}
          copyKey="marketplace-description"
          copiedKey={copiedKey}
          onCopy={onCopy}
        />
        <MarketplaceCopySection
          label="Bullet points"
          value={bullets}
          copyKey="marketplace-bullets"
          copiedKey={copiedKey}
          onCopy={onCopy}
        />
        <MarketplaceCopySection
          label="Keywords / tags"
          value={keywords}
          copyKey="marketplace-keywords"
          copiedKey={copiedKey}
          onCopy={onCopy}
        />
        <MarketplaceCopySection
          label="Platform notes"
          value={result.optimization.platformNotes}
          copyKey="marketplace-notes"
          copiedKey={copiedKey}
          onCopy={onCopy}
        />
      </div>
    </section>
  );
}

function MarketplaceCopySection({
  label,
  value,
  copyKey,
  copiedKey,
  onCopy,
}: CopyFieldProps) {
  return (
    <div className="border-t border-border pt-4 first:border-t-0 first:pt-0">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-medium">{label}</h3>
        <Button type="button" variant="secondary" onClick={() => onCopy(copyKey, value)}>
          <Clipboard className="mr-2 size-4" aria-hidden="true" />
          {copiedKey === copyKey ? 'Copied' : 'Copy'}
        </Button>
      </div>
      <p className="mt-3 whitespace-pre-wrap break-words text-sm text-muted-foreground">{value}</p>
    </div>
  );
}

interface BeforeAfterComparisonProps {
  improvement: ListingImprovementResult;
  acceptingVersionId: string | null;
  onAccept: (version: ListingVersion) => Promise<void>;
}

function BeforeAfterComparison({
  improvement,
  acceptingVersionId,
  onAccept,
}: BeforeAfterComparisonProps) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-medium">Before / after comparison</h2>
        <Button
          type="button"
          onClick={() => onAccept(improvement.improvedVersion)}
          disabled={acceptingVersionId === improvement.improvedVersion.id}
        >
          {acceptingVersionId === improvement.improvedVersion.id ? 'Accepting' : 'Accept improved version'}
        </Button>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <ListingSnapshot title="Before" listing={improvement.originalListing} />
        <ListingSnapshot title="After" listing={improvement.improvedVersion.listing} />
      </div>
    </section>
  );
}

function ListingSnapshot({ title, listing }: { title: string; listing: GeneratedListing }) {
  return (
    <div className="rounded-md border border-border p-3">
      <h3 className="text-sm font-medium">{title}</h3>
      <dl className="mt-3 grid gap-3 text-sm">
        <div>
          <dt className="text-muted-foreground">Title</dt>
          <dd className="mt-1 font-medium">{listing.title}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Short description</dt>
          <dd className="mt-1">{listing.shortDescription}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">SEO keywords</dt>
          <dd className="mt-1">{listing.seoKeywords.join(', ')}</dd>
        </div>
        <div>
          <dt className="text-muted-foreground">Product tags</dt>
          <dd className="mt-1">{listing.productTags.join(', ')}</dd>
        </div>
      </dl>
    </div>
  );
}

interface VersionHistoryProps {
  versions: ListingVersion[];
  acceptingVersionId: string | null;
  onAccept: (version: ListingVersion) => Promise<void>;
}

function VersionHistory({ versions, acceptingVersionId, onAccept }: VersionHistoryProps) {
  return (
    <section className="rounded-md border border-border p-4">
      <h2 className="text-base font-medium">Version history</h2>
      <div className="mt-3 grid gap-3">
        {versions.length > 0 ? (
          versions.map((version) => (
            <div
              key={version.id}
              className="grid gap-3 rounded-md border border-border p-3 sm:grid-cols-[minmax(0,1fr)_auto]"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium">
                  Version {version.versionNumber}
                  {version.isAccepted ? ' - accepted' : ''}
                </p>
                <p className="mt-1 truncate text-sm text-muted-foreground">
                  {version.listing.title}
                </p>
              </div>
              <Button
                type="button"
                variant="secondary"
                onClick={() => onAccept(version)}
                disabled={version.isAccepted || acceptingVersionId === version.id}
              >
                {acceptingVersionId === version.id ? 'Accepting' : 'Accept'}
              </Button>
            </div>
          ))
        ) : (
          <p className="text-sm text-muted-foreground">No improved versions yet.</p>
        )}
      </div>
    </section>
  );
}

function SeoAnalysisPanel({ result }: { result: SeoAnalysisResult }) {
  return (
    <section className="rounded-md border border-border p-4">
      <h2 className="text-base font-medium">SEO quality</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <ScoreMeter label="SEO score" value={result.analysis.seoScore} />
        <ScoreMeter label="Readability" value={result.analysis.readabilityScore} />
      </div>

      <div className="mt-5 grid gap-4">
        <FeedbackBlock
          title="Keyword optimization"
          value={result.analysis.keywordOptimizationFeedback}
        />
        <FeedbackBlock title="Title quality" value={result.analysis.titleQualityFeedback} />
        <FeedbackBlock
          title="Description quality"
          value={result.analysis.descriptionQualityFeedback}
        />
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-3">
        <ListBlock title="Strengths" values={result.analysis.strengths} />
        <ListBlock title="Weaknesses" values={result.analysis.weaknesses} />
        <ListBlock title="Suggested improvements" values={result.analysis.improvementSuggestions} />
      </div>
    </section>
  );
}

function ScoreMeter({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-border p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-lg font-semibold">{value}/100</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded bg-muted">
        <div className="h-full bg-primary" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}

function FeedbackBlock({ title, value }: { title: string; value: string }) {
  return (
    <div>
      <h3 className="text-sm font-medium">{title}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{value}</p>
    </div>
  );
}

function ListBlock({ title, values }: { title: string; values: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-medium">{title}</h3>
      <ul className="mt-2 grid gap-2 text-sm text-muted-foreground">
        {values.map((value) => (
          <li key={value} className="rounded bg-muted px-3 py-2">
            {value}
          </li>
        ))}
      </ul>
    </div>
  );
}

interface CopyFieldProps {
  label: string;
  value: string;
  copyKey: string;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => Promise<void>;
}

function CopyField({ label, value, copyKey, copiedKey, onCopy }: CopyFieldProps) {
  return (
    <section className="rounded-md border border-border p-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-medium">{label}</h2>
        <Button type="button" variant="secondary" onClick={() => onCopy(copyKey, value)}>
          <Clipboard className="mr-2 size-4" aria-hidden="true" />
          {copiedKey === copyKey ? 'Copied' : 'Copy'}
        </Button>
      </div>
      <p className="mt-3 whitespace-pre-wrap break-words text-sm text-muted-foreground">{value}</p>
    </section>
  );
}
