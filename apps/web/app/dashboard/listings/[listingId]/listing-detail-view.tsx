'use client';

import {
  ArrowLeft,
  Check,
  Clipboard,
  Download,
  FileText,
  ImageIcon,
  Layers3,
  Loader2,
  Megaphone,
  RefreshCw,
  SearchCheck,
  ShoppingBag,
  Sparkles,
  Trash2,
} from 'lucide-react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { type ReactNode, useEffect, useMemo, useState } from 'react';

import type {
  GeneratedListing,
  GeneratedSceneImage,
  ListingDetail,
  ListingImprovementResult,
  ListingVersion,
  Marketplace,
  MarketplaceOptimizationResult,
  ScenePreset,
  SeoAnalysisResult,
} from '@ai-product-listing/types';
import { ConfirmationModal } from '@/components/confirmation-modal';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { notifyWalletChanged } from '@/lib/api/billing';
import { deleteListing } from '@/lib/api/delete-actions';
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
  regenerateListing,
} from '@/lib/api/listing-improvements';
import {
  getMarketplaceOptimizations,
  optimizeListingForMarketplace,
} from '@/lib/api/marketplace-optimizations';
import { analyzeListingSeo } from '@/lib/api/seo-analysis';

type ResultTab = 'overview' | 'listing' | 'images' | 'marketplace' | 'marketing' | 'history';

const RESULT_TABS: Array<{ value: ResultTab; label: string; icon: typeof FileText }> = [
  { value: 'overview', label: 'Overview', icon: Sparkles },
  { value: 'listing', label: 'Listing Studio', icon: FileText },
  { value: 'images', label: 'Creative Studio', icon: ImageIcon },
  { value: 'marketplace', label: 'Marketplace Studio', icon: ShoppingBag },
  { value: 'marketing', label: 'Marketing Studio', icon: Megaphone },
  { value: 'history', label: 'Workspace History', icon: Layers3 },
];

const MARKETPLACES: { value: Marketplace; label: string }[] = [
  { value: 'shopify', label: 'Shopify' },
  { value: 'amazon', label: 'Amazon' },
  { value: 'etsy', label: 'Etsy' },
  { value: 'daraz', label: 'Daraz' },
  { value: 'woocommerce', label: 'WooCommerce' },
  { value: 'ebay', label: 'eBay' },
  { value: 'generic_store', label: 'Generic Stores' },
];

const SCENE_OPTIONS: { value: ScenePreset; label: string }[] = [
  { value: 'studio_white_background', label: 'Studio white background' },
  { value: 'luxury_product_shot', label: 'Luxury product shot' },
  { value: 'wooden_table_setup', label: 'Wooden table setup' },
  { value: 'minimal_ecommerce_background', label: 'Minimal ecommerce background' },
  { value: 'lifestyle_home_setup', label: 'Lifestyle home setup' },
  { value: 'social_media_banner', label: 'Social media banner' },
  { value: 'marketplace_hero_image', label: 'Marketplace hero image' },
];

const SCENE_LABELS: Record<ScenePreset, string> = {
  studio_white_background: 'Studio white background',
  luxury_product_shot: 'Luxury product shot',
  wooden_table_setup: 'Wooden table setup',
  minimal_ecommerce_background: 'Minimal ecommerce background',
  lifestyle_home_setup: 'Lifestyle home setup',
  social_media_banner: 'Social media banner',
  marketplace_hero_image: 'Marketplace hero image',
  custom_prompt: 'Custom prompt',
};

const MARKETPLACE_LABELS: Record<Marketplace, string> = {
  shopify: 'Shopify',
  amazon: 'Amazon',
  etsy: 'Etsy',
  daraz: 'Daraz',
  woocommerce: 'WooCommerce',
  ebay: 'eBay',
  generic_store: 'Generic Stores',
};

interface ListingDetailViewProps {
  listing: ListingDetail;
}

export function ListingDetailView({ listing }: ListingDetailViewProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<ResultTab>('overview');
  const [activeListing, setActiveListing] = useState<GeneratedListing>(listing.listing);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [isJsonExporting, setIsJsonExporting] = useState(false);
  const [isShopifyExporting, setIsShopifyExporting] = useState(false);
  const [isSeoAnalyzing, setIsSeoAnalyzing] = useState(false);
  const [isImproving, setIsImproving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [selectedMarketplace, setSelectedMarketplace] = useState<Marketplace>('shopify');
  const [isMarketplaceOptimizing, setIsMarketplaceOptimizing] = useState(false);
  const [selectedScenePreset, setSelectedScenePreset] =
    useState<ScenePreset>('lifestyle_home_setup');
  const [isSceneGenerating, setIsSceneGenerating] = useState(false);
  const [deletingGeneratedImageId, setDeletingGeneratedImageId] = useState<string | null>(null);
  const [regeneratingImageId, setRegeneratingImageId] = useState<string | null>(null);
  const [acceptingVersionId, setAcceptingVersionId] = useState<string | null>(null);
  const [seoAnalysis, setSeoAnalysis] = useState<SeoAnalysisResult | null>(null);
  const [seoErrorMessage, setSeoErrorMessage] = useState<string | null>(null);
  const [improvement, setImprovement] = useState<ListingImprovementResult | null>(null);
  const [versions, setVersions] = useState<ListingVersion[]>([]);
  const [improvementErrorMessage, setImprovementErrorMessage] = useState<string | null>(null);
  const [marketplaceOptimizationsByMarket, setMarketplaceOptimizationsByMarket] = useState<
    Record<string, MarketplaceOptimizationResult>
  >({});
  const [marketplaceErrorMessage, setMarketplaceErrorMessage] = useState<string | null>(null);
  const [generatedImages, setGeneratedImages] = useState<GeneratedSceneImage[]>([]);
  const [generatedImageErrorMessage, setGeneratedImageErrorMessage] = useState<string | null>(null);
  const [isDeleteListingModalOpen, setIsDeleteListingModalOpen] = useState(false);
  const [isDeletingListing, setIsDeletingListing] = useState(false);
  const [deleteListingErrorMessage, setDeleteListingErrorMessage] = useState<string | null>(null);

  const marketplaceOptimization = marketplaceOptimizationsByMarket[selectedMarketplace] ?? null;
  const activeKeywords = activeListing.seoKeywords.join(', ');
  const activeTags = activeListing.productTags.join(', ');

  const assetStatus = useMemo(
    () => [
      { label: 'Listing Studio ready', active: true },
      { label: 'SEO Studio reviewed', active: Boolean(seoAnalysis) },
      { label: 'Marketplace Studio ready', active: Object.keys(marketplaceOptimizationsByMarket).length > 0 },
      { label: 'Creative Studio images', active: generatedImages.length > 0 },
    ],
    [generatedImages.length, marketplaceOptimizationsByMarket, seoAnalysis],
  );

  useEffect(() => {
    void loadVersions();
    void loadGeneratedImages();
    void loadMarketplaceOptimizations();
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

  async function copyFullListing() {
    await copyText(
      'copy-full-listing',
      [
        `Title: ${activeListing.title}`,
        `Short description: ${activeListing.shortDescription}`,
        `Long description: ${activeListing.longDescription}`,
        `SEO keywords: ${activeKeywords}`,
        `Product tags: ${activeTags}`,
      ].join('\n\n'),
    );
  }

  async function copyMarketplaceContent(result: MarketplaceOptimizationResult) {
    await copyText(
      `marketplace-${result.marketplace}`,
      [
        `Title: ${result.optimization.optimizedTitle}`,
        `Description: ${result.optimization.optimizedDescription}`,
        `Bullet points:\n${result.optimization.bulletPoints.join('\n')}`,
        `Keywords/tags: ${result.optimization.keywordsTags.join(', ')}`,
        `Platform notes: ${result.optimization.platformNotes}`,
      ].join('\n\n'),
    );
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
      showToast('SEO Studio analysis completed.');
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

  async function handleRegenerateListing() {
    setIsRegenerating(true);
    setImprovementErrorMessage(null);
    try {
      const version = await regenerateListing(listing.id);
      setVersions((current) => [version, ...current]);
      notifyWalletChanged();
      showToast('New version generated. Accept it to make it the live copy.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Listing regeneration failed.';
      setImprovementErrorMessage(message);
      showToast(message);
    } finally {
      setIsRegenerating(false);
    }
  }

  async function handleMarketplaceOptimization(force = false) {
    const alreadyOptimized = Boolean(marketplaceOptimizationsByMarket[selectedMarketplace]);
    if (force && alreadyOptimized && !window.confirm('Re-optimize for this marketplace? This spends credits.')) {
      return;
    }

    setIsMarketplaceOptimizing(true);
    setMarketplaceErrorMessage(null);
    try {
      const result = await optimizeListingForMarketplace(listing.id, selectedMarketplace, force);
      setMarketplaceOptimizationsByMarket((current) => ({
        ...current,
        [result.marketplace]: result,
      }));
      if (!alreadyOptimized || force) {
        notifyWalletChanged();
      }
      showToast(force ? 'Marketplace Studio content refreshed.' : 'Marketplace Studio content ready.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Marketplace optimization failed.';
      setMarketplaceErrorMessage(message);
      showToast(message);
    } finally {
      setIsMarketplaceOptimizing(false);
    }
  }

  async function handleGenerateImage(preset = selectedScenePreset) {
    setIsSceneGenerating(true);
    setGeneratedImageErrorMessage(null);
    try {
      const result = await generateLifestyleScene(listing.id, preset, '');
      setGeneratedImages((current) => [result, ...current]);
      notifyWalletChanged();
      showToast('Generated image saved.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Image generation failed.';
      setGeneratedImageErrorMessage(message);
      showToast(message);
    } finally {
      setIsSceneGenerating(false);
    }
  }

  async function handleRegenerateImage(image: GeneratedSceneImage) {
    setRegeneratingImageId(image.id);
    setGeneratedImageErrorMessage(null);
    try {
      const result = await generateLifestyleScene(listing.id, image.category, image.customPrompt ?? '');
      setGeneratedImages((current) => [result, ...current]);
      notifyWalletChanged();
      showToast('Image regenerated.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Image regeneration failed.';
      setGeneratedImageErrorMessage(message);
      showToast(message);
    } finally {
      setRegeneratingImageId(null);
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
          acceptedAt:
            item.id === result.acceptedVersion.id ? result.acceptedVersion.acceptedAt : null,
        })),
      );
      showToast('Version accepted.');
    } catch (error) {
      showToast(error instanceof Error ? error.message : 'Could not accept version.');
    } finally {
      setAcceptingVersionId(null);
    }
  }

  async function handleDeleteListing() {
    setIsDeletingListing(true);
    setDeleteListingErrorMessage(null);
    try {
      await deleteListing(listing.id);
      showToast('Listing deleted.');
      router.push('/dashboard');
      router.refresh();
    } catch (error) {
      setDeleteListingErrorMessage(
        error instanceof Error ? error.message : 'Could not delete listing. Please try again.',
      );
    } finally {
      setIsDeletingListing(false);
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
    } catch {
      setGeneratedImages([]);
    }
  }

  async function loadMarketplaceOptimizations() {
    try {
      const optimizations = await getMarketplaceOptimizations(listing.id);
      setMarketplaceOptimizationsByMarket(
        Object.fromEntries(optimizations.map((item) => [item.marketplace, item])),
      );
    } catch {
      setMarketplaceOptimizationsByMarket({});
    }
  }

  function showToast(message: string) {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 2500);
  }

  function showMarketingUnavailable() {
    showToast('Marketing Studio is not available yet.');
  }

  return (
    <div className="grid gap-6">
      {toastMessage ? (
        <div className="glass-panel fixed bottom-5 right-5 z-50 max-w-sm px-4 py-3 text-sm text-white">
          {toastMessage}
        </div>
      ) : null}

      <ListingWorkspaceHeader
        title={activeListing.title}
        status={listing.status}
        isExporting={isJsonExporting}
        isDeleting={isDeletingListing}
        onExport={downloadJson}
        onRequestDelete={() => {
          setDeleteListingErrorMessage(null);
          setIsDeleteListingModalOpen(true);
        }}
      />

      {isDeleteListingModalOpen ? (
        <ConfirmationModal
          title="Delete listing"
          description="This will remove the listing from Workspace History and hide it from product workspace views."
          confirmLabel="Delete listing"
          isConfirming={isDeletingListing}
          errorMessage={deleteListingErrorMessage}
          onCancel={() => setIsDeleteListingModalOpen(false)}
          onConfirm={() => void handleDeleteListing()}
        />
      ) : null}

      <ResultTabs activeTab={activeTab} onChange={setActiveTab} />

      <motion.div
        key={activeTab}
        animate={{ opacity: 1, y: 0 }}
        initial={{ opacity: 0, y: 8 }}
        transition={{ duration: 0.22 }}
      >
        {activeTab === 'overview' ? (
          <OverviewPanel
            listing={listing}
            activeListing={activeListing}
            seoAnalysis={seoAnalysis}
            assetStatus={assetStatus}
          />
        ) : null}

        {activeTab === 'listing' ? (
          <ListingPanel
            listing={activeListing}
            copiedKey={copiedKey}
            isImproving={isImproving}
            isRegenerating={isRegenerating}
            improvementErrorMessage={improvementErrorMessage}
            seoAnalysis={seoAnalysis}
            seoErrorMessage={seoErrorMessage}
            isSeoAnalyzing={isSeoAnalyzing}
            onCopyFull={copyFullListing}
            onCopyField={copyText}
            onImprove={handleImproveListing}
            onRegenerate={handleRegenerateListing}
            onAnalyzeSeo={handleAnalyzeSeo}
          />
        ) : null}

        {activeTab === 'images' ? (
          <ImageGallery
            images={generatedImages}
            selectedScenePreset={selectedScenePreset}
            isGenerating={isSceneGenerating}
            errorMessage={generatedImageErrorMessage}
            deletingImageId={deletingGeneratedImageId}
            regeneratingImageId={regeneratingImageId}
            onPresetChange={setSelectedScenePreset}
            onGenerate={() => void handleGenerateImage()}
            onDownload={downloadGeneratedImage}
            onDelete={deleteGeneratedImage}
            onRegenerate={handleRegenerateImage}
          />
        ) : null}

        {activeTab === 'marketplace' ? (
          <MarketplacePanel
            selectedMarketplace={selectedMarketplace}
            optimization={marketplaceOptimization}
            errorMessage={marketplaceErrorMessage}
            isOptimizing={isMarketplaceOptimizing}
            copiedKey={copiedKey}
            isJsonExporting={isJsonExporting}
            isShopifyExporting={isShopifyExporting}
            onMarketplaceChange={setSelectedMarketplace}
            onOptimize={() => void handleMarketplaceOptimization(false)}
            onRefresh={() => void handleMarketplaceOptimization(true)}
            onCopy={copyMarketplaceContent}
            onExportJson={downloadJson}
            onExportShopify={downloadShopifyCsv}
          />
        ) : null}

        {activeTab === 'marketing' ? (
          <MarketingPanel onGenerate={showMarketingUnavailable} />
        ) : null}

        {activeTab === 'history' ? (
          <HistoryPanel
            originalListing={listing.listing}
            activeListing={activeListing}
            improvement={improvement}
            versions={versions}
            acceptingVersionId={acceptingVersionId}
            onAccept={handleAcceptVersion}
          />
        ) : null}
      </motion.div>
    </div>
  );
}

function ListingWorkspaceHeader({
  title,
  status,
  isExporting,
  isDeleting,
  onExport,
  onRequestDelete,
}: {
  title: string;
  status: string;
  isExporting: boolean;
  isDeleting: boolean;
  onExport: () => Promise<void>;
  onRequestDelete: () => void;
}) {
  return (
    <section className="glass-panel p-4 sm:p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <Button asChild variant="secondary" className="h-9 px-3">
              <Link href="/dashboard">
                <ArrowLeft className="size-4" aria-hidden="true" />
                Back to AI Workspace
              </Link>
            </Button>
            <span className="rounded-full border border-primary/35 bg-primary/15 px-3 py-1 text-xs font-semibold capitalize text-white">
              {status}
            </span>
          </div>
          <h1 className="mt-4 max-w-4xl text-2xl font-semibold leading-tight text-white sm:text-3xl">
            {title}
          </h1>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="secondary" onClick={onRequestDelete} disabled={isDeleting}>
            {isDeleting ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              <Trash2 className="size-4" aria-hidden="true" />
            )}
            Delete
          </Button>
          <Button type="button" onClick={() => void onExport()} disabled={isExporting}>
            {isExporting ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              <Download className="size-4" aria-hidden="true" />
            )}
            {isExporting ? 'Exporting' : 'Export'}
          </Button>
        </div>
      </div>
    </section>
  );
}

function ResultTabs({
  activeTab,
  onChange,
}: {
  activeTab: ResultTab;
  onChange: (tab: ResultTab) => void;
}) {
  return (
    <div className="glass-panel overflow-x-auto p-2">
      <div className="flex min-w-max gap-1">
        {RESULT_TABS.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.value;
          return (
            <button
              key={tab.value}
              className={cn(
                'inline-flex h-10 items-center gap-2 rounded-md px-3 text-sm font-semibold transition',
                isActive
                  ? 'bg-primary text-white shadow-[0_16px_44px_-24px_hsl(var(--primary))]'
                  : 'text-muted-foreground hover:bg-white/[0.06] hover:text-white',
              )}
              type="button"
              onClick={() => onChange(tab.value)}
            >
              <Icon className="size-4" aria-hidden="true" />
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

function OverviewPanel({
  listing,
  activeListing,
  seoAnalysis,
  assetStatus,
}: {
  listing: ListingDetail;
  activeListing: GeneratedListing;
  seoAnalysis: SeoAnalysisResult | null;
  assetStatus: Array<{ label: string; active: boolean }>;
}) {
  const attributes = [
    ['Category', listing.analysis.category],
    ['Product type', listing.analysis.productType],
    ['Color', listing.analysis.color],
    ['Material', listing.analysis.material],
    ['Style', listing.analysis.style],
    ['Visible text/brand', listing.analysis.visibleTextBrand],
    ['Target audience', listing.analysis.targetAudience],
  ];

  return (
    <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
      <img
        alt={listing.image.originalFilename}
        className="aspect-square w-full rounded-lg border border-white/10 object-cover shadow-[0_24px_90px_-60px_rgba(0,0,0,1)]"
        src={listing.image.imageUrl}
      />
      <div className="grid gap-5">
        <section className="premium-card p-5">
          <p className="eyebrow">Product Intelligence</p>
          <dl className="mt-5 grid gap-3 sm:grid-cols-2">
            {attributes.map(([label, value]) => (
              <div key={label} className="rounded-md border border-white/10 bg-background/45 p-3">
                <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
                <dd className="mt-1 min-w-0 break-words text-sm font-medium text-white">{value}</dd>
              </div>
            ))}
          </dl>
        </section>

        <div className="grid gap-5 lg:grid-cols-2">
          <section className="premium-card p-5">
            <p className="eyebrow">SEO Studio</p>
            {seoAnalysis ? (
              <div className="mt-5 grid gap-4">
                <ScoreMeter label="SEO score" value={seoAnalysis.analysis.seoScore} />
                <ScoreMeter label="Readability" value={seoAnalysis.analysis.readabilityScore} />
              </div>
            ) : (
              <EmptyState
                icon={SearchCheck}
                title="No SEO Studio score yet"
                body="Run SEO Studio analysis from the Listing Studio tab to see quality scores here."
              />
            )}
          </section>

          <section className="premium-card p-5">
            <p className="eyebrow">Workspace Status</p>
            <div className="mt-5 grid gap-3">
              {assetStatus.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-background/45 px-3 py-2"
                >
                  <span className="text-sm text-white">{item.label}</span>
                  <span
                    className={cn(
                      'rounded-full px-2.5 py-1 text-xs font-semibold',
                      item.active
                        ? 'bg-primary/20 text-white'
                        : 'bg-white/[0.05] text-muted-foreground',
                    )}
                  >
                    {item.active ? 'Ready' : 'Pending'}
                  </span>
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="premium-card p-5">
          <p className="eyebrow">Live Commerce Copy</p>
          <h2 className="mt-3 text-xl font-semibold text-white">{activeListing.title}</h2>
          <p className="mt-3 text-sm leading-7 text-muted-foreground">
            {activeListing.shortDescription}
          </p>
        </section>
      </div>
    </div>
  );
}

function ListingPanel({
  listing,
  copiedKey,
  isImproving,
  isRegenerating,
  improvementErrorMessage,
  seoAnalysis,
  seoErrorMessage,
  isSeoAnalyzing,
  onCopyFull,
  onCopyField,
  onImprove,
  onRegenerate,
  onAnalyzeSeo,
}: {
  listing: GeneratedListing;
  copiedKey: string | null;
  isImproving: boolean;
  isRegenerating: boolean;
  improvementErrorMessage: string | null;
  seoAnalysis: SeoAnalysisResult | null;
  seoErrorMessage: string | null;
  isSeoAnalyzing: boolean;
  onCopyFull: () => Promise<void>;
  onCopyField: (key: string, value: string) => Promise<void>;
  onImprove: () => Promise<void>;
  onRegenerate: () => Promise<void>;
  onAnalyzeSeo: () => Promise<void>;
}) {
  return (
    <div className="grid gap-5">
      <section className="glass-panel p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="eyebrow">Listing Studio</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Review launch-ready product copy and refine only when needed.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => void onCopyFull()}>
              <Clipboard className="size-4" aria-hidden="true" />
              {copiedKey === 'copy-full-listing' ? 'Copied' : 'Copy full copy'}
            </Button>
            <Button type="button" variant="secondary" onClick={() => void onImprove()} disabled={isImproving}>
              {isImproving ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
              {isImproving ? 'Improving' : 'Improve'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={() => void onRegenerate()}
              disabled={isRegenerating}
            >
              {isRegenerating ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
              {isRegenerating ? 'Regenerating' : 'Regenerate'}
            </Button>
          </div>
        </div>
      </section>

      {improvementErrorMessage ? <ErrorMessage message={improvementErrorMessage} /> : null}

      <div className="grid gap-4">
        <ContentCard
          label="Title"
          value={listing.title}
          copyKey="title"
          copiedKey={copiedKey}
          onCopy={onCopyField}
        />
        <ContentCard
          label="Short description"
          value={listing.shortDescription}
          copyKey="short-description"
          copiedKey={copiedKey}
          onCopy={onCopyField}
        />
        <ContentCard
          label="Long description"
          value={listing.longDescription}
          copyKey="long-description"
          copiedKey={copiedKey}
          onCopy={onCopyField}
        />
        <TagSection
          title="SEO Studio keywords"
          values={listing.seoKeywords}
          copyKey="seo-keywords"
          copiedKey={copiedKey}
          onCopy={onCopyField}
        />
        <TagSection
          title="Product tags"
          values={listing.productTags}
          copyKey="product-tags"
          copiedKey={copiedKey}
          onCopy={onCopyField}
        />
      </div>

      <section className="premium-card p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-base font-semibold text-white">SEO Studio quality</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Run this when you want a score and improvement guidance.
            </p>
          </div>
          <Button type="button" variant="secondary" onClick={() => void onAnalyzeSeo()} disabled={isSeoAnalyzing}>
            {isSeoAnalyzing ? <Loader2 className="size-4 animate-spin" /> : <SearchCheck className="size-4" />}
              {isSeoAnalyzing ? 'Analyzing' : 'Analyze in SEO Studio'}
          </Button>
        </div>
        {seoErrorMessage ? <div className="mt-4"><ErrorMessage message={seoErrorMessage} /></div> : null}
        {seoAnalysis ? <SeoAnalysisSummary result={seoAnalysis} /> : null}
      </section>
    </div>
  );
}

function ImageGallery({
  images,
  selectedScenePreset,
  isGenerating,
  errorMessage,
  deletingImageId,
  regeneratingImageId,
  onPresetChange,
  onGenerate,
  onDownload,
  onDelete,
  onRegenerate,
}: {
  images: GeneratedSceneImage[];
  selectedScenePreset: ScenePreset;
  isGenerating: boolean;
  errorMessage: string | null;
  deletingImageId: string | null;
  regeneratingImageId: string | null;
  onPresetChange: (preset: ScenePreset) => void;
  onGenerate: () => void;
  onDownload: (image: GeneratedSceneImage) => Promise<void>;
  onDelete: (image: GeneratedSceneImage) => Promise<void>;
  onRegenerate: (image: GeneratedSceneImage) => Promise<void>;
}) {
  return (
    <div className="grid gap-5">
      <section className="glass-panel p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="eyebrow">Creative Studio</p>
            <p className="mt-2 text-sm text-muted-foreground">
              Generate and manage product scene images for storefronts and campaigns.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <select
              aria-label="Image preset"
              className="field-surface h-10 min-w-56"
              value={selectedScenePreset}
              onChange={(event) => onPresetChange(event.target.value as ScenePreset)}
              disabled={isGenerating}
            >
              {SCENE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
            <Button type="button" onClick={onGenerate} disabled={isGenerating}>
              {isGenerating ? <Loader2 className="size-4 animate-spin" /> : <ImageIcon className="size-4" />}
              {isGenerating ? 'Generating' : 'Generate creative'}
            </Button>
          </div>
        </div>
      </section>

      {errorMessage ? <ErrorMessage message={errorMessage} /> : null}

      {images.length > 0 ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {images.map((image) => (
            <article
              key={image.id}
              className="group relative overflow-hidden rounded-lg border border-white/10 bg-secondary/70"
            >
              <img
                alt={`${SCENE_LABELS[image.category]} preview`}
                className="aspect-square w-full object-cover transition duration-500 group-hover:scale-105"
                src={image.generatedImageUrl}
              />
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 via-black/45 to-transparent p-4">
                <p className="text-sm font-semibold text-white">{SCENE_LABELS[image.category]}</p>
                <p className="mt-1 text-xs text-white/70">{formatDate(image.createdAt)}</p>
              </div>
              <div className="absolute inset-0 flex items-end justify-end gap-2 bg-black/35 p-3 opacity-0 transition group-hover:opacity-100">
                <IconAction label="Download" onClick={() => void onDownload(image)}>
                  <Download className="size-4" />
                </IconAction>
                <IconAction
                  label="Regenerate"
                  disabled={regeneratingImageId === image.id}
                  onClick={() => void onRegenerate(image)}
                >
                  {regeneratingImageId === image.id ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <RefreshCw className="size-4" />
                  )}
                </IconAction>
                <IconAction
                  label="Delete"
                  disabled={deletingImageId === image.id}
                  onClick={() => void onDelete(image)}
                >
                  {deletingImageId === image.id ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <Trash2 className="size-4" />
                  )}
                </IconAction>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={ImageIcon}
          title="No Creative Studio images yet"
          body="Choose a preset and generate a product image for this launch workflow."
          action={<Button type="button" onClick={onGenerate}>Generate creative</Button>}
        />
      )}
    </div>
  );
}

function MarketplacePanel({
  selectedMarketplace,
  optimization,
  errorMessage,
  isOptimizing,
  copiedKey,
  isJsonExporting,
  isShopifyExporting,
  onMarketplaceChange,
  onOptimize,
  onRefresh,
  onCopy,
  onExportJson,
  onExportShopify,
}: {
  selectedMarketplace: Marketplace;
  optimization: MarketplaceOptimizationResult | null;
  errorMessage: string | null;
  isOptimizing: boolean;
  copiedKey: string | null;
  isJsonExporting: boolean;
  isShopifyExporting: boolean;
  onMarketplaceChange: (marketplace: Marketplace) => void;
  onOptimize: () => void;
  onRefresh: () => void;
  onCopy: (result: MarketplaceOptimizationResult) => Promise<void>;
  onExportJson: () => Promise<void>;
  onExportShopify: () => Promise<void>;
}) {
  return (
    <div className="grid gap-5">
      <section className="glass-panel p-4">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-end">
          <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_280px] sm:items-end">
            <div>
              <p className="eyebrow">Marketplace Studio</p>
              <h2 className="mt-2 text-xl font-semibold text-white">
                {MARKETPLACE_LABELS[selectedMarketplace]} output
              </h2>
              <p className="mt-2 text-sm text-muted-foreground">
                Select a marketplace, generate channel-ready content, then copy or export it.
              </p>
            </div>
            <label className="grid gap-2 text-sm font-medium text-white">
              Marketplace Studio channel
              <select
                aria-label="Select marketplace"
                className="field-surface h-10"
                value={selectedMarketplace}
                onChange={(event) => onMarketplaceChange(event.target.value as Marketplace)}
                disabled={isOptimizing}
              >
                {MARKETPLACES.map((marketplace) => (
                  <option key={marketplace.value} value={marketplace.value}>
                    {marketplace.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={optimization ? onRefresh : onOptimize} disabled={isOptimizing}>
              {isOptimizing ? <Loader2 className="size-4 animate-spin" /> : <Sparkles className="size-4" />}
              {optimization ? 'Refresh content' : 'Create channel content'}
            </Button>
            {optimization ? (
              <Button type="button" variant="secondary" onClick={() => void onCopy(optimization)}>
                <Clipboard className="size-4" />
                {copiedKey === `marketplace-${optimization.marketplace}` ? 'Copied' : 'Copy content'}
              </Button>
            ) : null}
            <Button type="button" variant="secondary" onClick={() => void onExportJson()} disabled={isJsonExporting}>
              <Download className="size-4" />
              JSON
            </Button>
            {selectedMarketplace === 'shopify' ? (
              <Button type="button" variant="secondary" onClick={() => void onExportShopify()} disabled={isShopifyExporting}>
                <Download className="size-4" />
                Shopify CSV
              </Button>
            ) : null}
          </div>
        </div>
      </section>

      {errorMessage ? <ErrorMessage message={errorMessage} /> : null}

      {optimization ? (
        <section className="premium-card p-5">
          <div className="grid gap-5">
            <OutputBlock title="Optimized title" value={optimization.optimization.optimizedTitle} />
            <OutputBlock
              title="Optimized description"
              value={optimization.optimization.optimizedDescription}
            />
            <OutputBlock title="Bullet points" value={optimization.optimization.bulletPoints.join('\n')} />
            <TagList title="Keywords / tags" values={optimization.optimization.keywordsTags} />
            <OutputBlock title="Platform notes" value={optimization.optimization.platformNotes} />
          </div>
        </section>
      ) : (
        <EmptyState
          icon={ShoppingBag}
          title={`No ${MARKETPLACE_LABELS[selectedMarketplace]} content yet`}
          body="Create Marketplace Studio content to see optimized titles, descriptions, bullets, tags, and notes."
          action={<Button type="button" onClick={onOptimize}>Create channel content</Button>}
        />
      )}
    </div>
  );
}

function MarketingPanel({ onGenerate }: { onGenerate: () => void }) {
  return (
    <EmptyState
      icon={Megaphone}
      title="Marketing Studio is ready for campaign copy."
      body="Facebook ads, Instagram captions, Google ads, email copy, and TikTok captions will appear here when this workflow is available."
      action={<Button type="button" onClick={onGenerate}>Open Marketing Studio</Button>}
    />
  );
}

function HistoryPanel({
  originalListing,
  activeListing,
  improvement,
  versions,
  acceptingVersionId,
  onAccept,
}: {
  originalListing: GeneratedListing;
  activeListing: GeneratedListing;
  improvement: ListingImprovementResult | null;
  versions: ListingVersion[];
  acceptingVersionId: string | null;
  onAccept: (version: ListingVersion) => Promise<void>;
}) {
  return (
    <div className="grid gap-5">
      <section className="premium-card p-5">
        <p className="eyebrow">Workspace History</p>
        <div className="mt-5 grid gap-4">
          <VersionCard
            title="Original version"
            detail="Initial Listing Studio output"
            listing={originalListing}
            isLive={sameListing(originalListing, activeListing)}
            createdAt={null}
          />
          {versions.map((version) => (
            <VersionCard
              key={version.id}
              title={`Version ${version.versionNumber}`}
              detail={VERSION_SOURCE_LABELS[version.source] ?? version.source}
              listing={version.listing}
              isLive={version.isAccepted}
              createdAt={version.createdAt}
              action={
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => void onAccept(version)}
                  disabled={version.isAccepted || acceptingVersionId === version.id}
                >
                  {acceptingVersionId === version.id ? 'Accepting' : version.isAccepted ? 'Live' : 'Accept'}
                </Button>
              }
            />
          ))}
        </div>
      </section>

      {improvement ? (
        <section className="glass-panel p-5">
          <h2 className="text-base font-semibold text-white">Latest improvement preview</h2>
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            <ListingSnapshot title="Before" listing={improvement.originalListing} />
            <ListingSnapshot title="After" listing={improvement.improvedVersion.listing} />
          </div>
        </section>
      ) : null}
    </div>
  );
}

const VERSION_SOURCE_LABELS: Record<string, string> = {
  ai_improvement: 'AI improvement',
  regeneration: 'Regenerated',
};

function ContentCard({
  label,
  value,
  copyKey,
  copiedKey,
  onCopy,
}: {
  label: string;
  value: string;
  copyKey: string;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => Promise<void>;
}) {
  return (
    <section className="premium-card p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-white">{label}</h2>
        <CopyAction
          copied={copiedKey === copyKey}
          onClick={() => void onCopy(copyKey, value)}
        />
      </div>
      <p className="mt-3 whitespace-pre-wrap break-words text-sm leading-7 text-muted-foreground">
        {value}
      </p>
    </section>
  );
}

function TagSection({
  title,
  values,
  copyKey,
  copiedKey,
  onCopy,
}: {
  title: string;
  values: string[];
  copyKey: string;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => Promise<void>;
}) {
  return (
    <section className="premium-card p-5">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-white">{title}</h2>
        <CopyAction
          copied={copiedKey === copyKey}
          onClick={() => void onCopy(copyKey, values.join(', '))}
        />
      </div>
      <TagList title="" values={values} />
    </section>
  );
}

function CopyAction({ copied, onClick }: { copied: boolean; onClick: () => void }) {
  return (
    <button
      className="inline-flex size-9 items-center justify-center rounded-md border border-white/10 bg-white/[0.04] text-muted-foreground transition hover:bg-white/[0.08] hover:text-white"
      type="button"
      onClick={onClick}
      title={copied ? 'Copied' : 'Copy'}
    >
      {copied ? <Check className="size-4" aria-hidden="true" /> : <Clipboard className="size-4" aria-hidden="true" />}
    </button>
  );
}

function IconAction({
  label,
  disabled,
  children,
  onClick,
}: {
  label: string;
  disabled?: boolean;
  children: ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      className="inline-flex size-9 items-center justify-center rounded-md border border-white/10 bg-black/45 text-white backdrop-blur transition hover:bg-white/15 disabled:opacity-50"
      type="button"
      disabled={disabled}
      onClick={onClick}
      title={label}
    >
      {children}
    </button>
  );
}

function SeoAnalysisSummary({ result }: { result: SeoAnalysisResult }) {
  return (
    <div className="mt-5 grid gap-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <ScoreMeter label="SEO score" value={result.analysis.seoScore} />
        <ScoreMeter label="Readability" value={result.analysis.readabilityScore} />
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        <FeedbackList title="Strengths" values={result.analysis.strengths} />
        <FeedbackList title="Weaknesses" values={result.analysis.weaknesses} />
        <FeedbackList title="Suggestions" values={result.analysis.improvementSuggestions} />
      </div>
    </div>
  );
}

function ScoreMeter({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.04] p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-lg font-semibold text-white">{value}/100</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded bg-muted">
        <div
          className="h-full bg-gradient-to-r from-primary to-accent"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}

function FeedbackList({ title, values }: { title: string; values: string[] }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <ul className="mt-2 grid gap-2">
        {values.map((value) => (
          <li key={value} className="rounded-md border border-white/10 bg-background/45 px-3 py-2 text-sm text-muted-foreground">
            {value}
          </li>
        ))}
      </ul>
    </div>
  );
}

function OutputBlock({ title, value }: { title: string; value: string }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7 text-muted-foreground">
        {value}
      </p>
    </div>
  );
}

function TagList({ title, values }: { title: string; values: string[] }) {
  return (
    <div>
      {title ? <h3 className="text-sm font-semibold text-white">{title}</h3> : null}
      <div className={cn('flex flex-wrap gap-2', title ? 'mt-3' : 'mt-3')}>
        {values.map((value) => (
          <span
            key={value}
            className="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-xs text-white/85"
          >
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}

function EmptyState({
  icon: Icon,
  title,
  body,
  action,
}: {
  icon: typeof Sparkles;
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <section className="glass-panel px-6 py-12 text-center">
      <span className="mx-auto flex size-14 items-center justify-center rounded-lg bg-primary/15 text-primary">
        <Icon className="size-7" aria-hidden="true" />
      </span>
      <h2 className="mx-auto mt-5 max-w-xl text-xl font-semibold text-white">{title}</h2>
      <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-muted-foreground">{body}</p>
      {action ? <div className="mt-6 flex justify-center">{action}</div> : null}
    </section>
  );
}

function VersionCard({
  title,
  detail,
  listing,
  isLive,
  createdAt,
  action,
}: {
  title: string;
  detail: string;
  listing: GeneratedListing;
  isLive: boolean;
  createdAt: string | null;
  action?: ReactNode;
}) {
  return (
    <article
      className={cn(
        'grid gap-4 rounded-lg border p-4 lg:grid-cols-[minmax(0,1fr)_auto]',
        isLive ? 'border-primary/50 bg-primary/10' : 'border-white/10 bg-white/[0.04]',
      )}
    >
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="text-base font-semibold text-white">{title}</h3>
          <span className="rounded-full border border-white/10 bg-white/[0.06] px-2.5 py-1 text-xs text-muted-foreground">
            {detail}
          </span>
          {isLive ? (
            <span className="rounded-full border border-primary/50 bg-primary/20 px-2.5 py-1 text-xs font-semibold text-white">
              Live
            </span>
          ) : null}
        </div>
        <p className="mt-2 truncate text-sm font-medium text-white">{listing.title}</p>
        <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">
          {listing.shortDescription}
        </p>
        <p className="mt-3 text-xs text-muted-foreground">
          {createdAt ? formatDate(createdAt) : 'Original generation'}
        </p>
      </div>
      {action ? <div className="flex items-start">{action}</div> : null}
    </article>
  );
}

function ListingSnapshot({ title, listing }: { title: string; listing: GeneratedListing }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.04] p-4">
      <h3 className="text-sm font-semibold text-white">{title}</h3>
      <p className="mt-3 text-sm font-medium text-white">{listing.title}</p>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{listing.shortDescription}</p>
    </div>
  );
}

function ErrorMessage({ message }: { message: string }) {
  return (
    <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
      {message}
    </p>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('en', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

function sameListing(first: GeneratedListing, second: GeneratedListing) {
  return (
    first.title === second.title &&
    first.shortDescription === second.shortDescription &&
    first.longDescription === second.longDescription
  );
}
