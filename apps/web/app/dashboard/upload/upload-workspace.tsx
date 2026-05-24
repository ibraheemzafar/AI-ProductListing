'use client';

import { Clipboard, Sparkles, WandSparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

import type {
  GeneratedListingResult,
  ProductAnalysisResult,
  UploadedProductImage,
} from '@ai-product-listing/types';
import { Button } from '@/components/ui/button';
import { analyzeProductImage } from '@/lib/api/analysis';
import { generateListing } from '@/lib/api/listings';
import { UploadForm } from './upload-form';

interface UploadWorkspaceProps {
  initialImages: UploadedProductImage[];
}

export function UploadWorkspace({ initialImages }: UploadWorkspaceProps) {
  const router = useRouter();
  const [analysisByImageId, setAnalysisByImageId] = useState<Record<string, ProductAnalysisResult>>(
    {},
  );
  const [listingByAnalysisId, setListingByAnalysisId] = useState<
    Record<string, GeneratedListingResult>
  >({});
  const [loadingImageId, setLoadingImageId] = useState<string | null>(null);
  const [loadingAnalysisId, setLoadingAnalysisId] = useState<string | null>(null);
  const [errorByImageId, setErrorByImageId] = useState<Record<string, string>>({});
  const [errorByAnalysisId, setErrorByAnalysisId] = useState<Record<string, string>>({});
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  async function handleAnalyzeImage(imageId: string) {
    setLoadingImageId(imageId);
    setErrorByImageId((current) => {
      const next = { ...current };
      delete next[imageId];
      return next;
    });

    try {
      const analysis = await analyzeProductImage(imageId);
      setAnalysisByImageId((current) => ({ ...current, [imageId]: analysis }));
      showToast('Product analysis completed.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Product analysis failed.';
      setErrorByImageId((current) => ({
        ...current,
        [imageId]: message,
      }));
      showToast(message);
    } finally {
      setLoadingImageId(null);
    }
  }

  async function handleGenerateListing(analysisId: string) {
    setLoadingAnalysisId(analysisId);
    setErrorByAnalysisId((current) => {
      const next = { ...current };
      delete next[analysisId];
      return next;
    });

    try {
      const listing = await generateListing(analysisId);
      setListingByAnalysisId((current) => ({ ...current, [analysisId]: listing }));
      showToast('Listing generated.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Listing generation failed.';
      setErrorByAnalysisId((current) => ({
        ...current,
        [analysisId]: message,
      }));
      showToast(message);
    } finally {
      setLoadingAnalysisId(null);
    }
  }

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

  function showToast(message: string) {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 2500);
  }

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
      {toastMessage ? (
        <div
          className="glass-panel fixed bottom-5 right-5 z-50 max-w-sm px-4 py-3 text-sm text-white"
          role="status"
        >
          {toastMessage}
        </div>
      ) : null}

      <section className="glass-panel p-5">
        <h2 className="text-lg font-semibold text-white">Upload product images</h2>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">
          Preview images before uploading them to your product workspace.
        </p>
        <div className="mt-5">
          <UploadForm onUploadComplete={() => router.refresh()} />
        </div>
      </section>

      <section className="glass-panel p-5">
        <h2 className="text-lg font-semibold text-white">Uploaded images</h2>
        <div className="mt-5 grid gap-3">
          {initialImages.length > 0 ? (
            initialImages.map((image) => {
              const analysis = analysisByImageId[image.id];
              const listing = analysis ? listingByAnalysisId[analysis.id] : undefined;

              return (
                <div
                  key={image.id}
                  className="rounded-lg border border-white/10 bg-secondary/60 p-3 transition hover:border-primary/35"
                >
                  <div className="flex gap-3">
                    <img
                      alt={image.originalFilename}
                      className="size-20 rounded-md object-cover"
                      src={image.imageUrl}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-white">
                        {image.originalFilename}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {(image.sizeBytes / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <Button
                        className="mt-3 h-9 px-3"
                        type="button"
                        onClick={() => handleAnalyzeImage(image.id)}
                        disabled={loadingImageId === image.id}
                      >
                        <Sparkles className="mr-2 size-4" aria-hidden="true" />
                        {loadingImageId === image.id ? 'Analyzing' : 'Analyze Product'}
                      </Button>
                    </div>
                  </div>

                  {errorByImageId[image.id] ? (
                    <p className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                      {errorByImageId[image.id]}
                    </p>
                  ) : null}

                  {analysis ? (
                    <div className="mt-4 border-t border-white/10 pt-3">
                      <AnalysisAttributes analysis={analysis} />
                      <Button
                        className="mt-4 h-9 px-3"
                        type="button"
                        onClick={() => handleGenerateListing(analysis.id)}
                        disabled={loadingAnalysisId === analysis.id}
                      >
                        <WandSparkles className="mr-2 size-4" aria-hidden="true" />
                        {loadingAnalysisId === analysis.id ? 'Generating' : 'Generate Listing'}
                      </Button>

                      {errorByAnalysisId[analysis.id] ? (
                        <p className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                          {errorByAnalysisId[analysis.id]}
                        </p>
                      ) : null}

                      {listing ? (
                        <GeneratedListingPanel
                          listing={listing}
                          copiedKey={copiedKey}
                          onCopy={copyText}
                        />
                      ) : null}
                    </div>
                  ) : null}
                </div>
              );
            })
          ) : (
            <div className="rounded-lg border border-dashed border-white/15 bg-white/[0.03] p-8 text-center">
              <p className="text-sm font-medium text-white">No uploaded images yet.</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Uploaded assets will appear here for AI analysis.
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function AnalysisAttributes({ analysis }: { analysis: ProductAnalysisResult }) {
  const attributes = [
    ['Category', analysis.attributes.category],
    ['Product type', analysis.attributes.productType],
    ['Color', analysis.attributes.color],
    ['Material', analysis.attributes.material],
    ['Style', analysis.attributes.style],
    ['Visible text/brand', analysis.attributes.visibleTextBrand],
    ['Target audience', analysis.attributes.targetAudience],
  ];

  return (
    <dl className="grid gap-2 text-sm">
      {attributes.map(([label, value]) => (
        <div key={label} className="grid grid-cols-[120px_minmax(0,1fr)] gap-3">
          <dt className="text-muted-foreground">{label}</dt>
          <dd className="min-w-0 break-words font-medium text-white">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

interface GeneratedListingPanelProps {
  listing: GeneratedListingResult;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => Promise<void>;
}

function GeneratedListingPanel({ listing, copiedKey, onCopy }: GeneratedListingPanelProps) {
  const keywordText = listing.listing.seoKeywords.join(', ');
  const tagText = listing.listing.productTags.join(', ');

  return (
    <div className="mt-4 grid gap-4 border-t border-white/10 pt-4 text-sm">
      <ListingField
        label="Title"
        value={listing.listing.title}
        copyKey={`${listing.id}:title`}
        copiedKey={copiedKey}
        onCopy={onCopy}
      />
      <ListingField
        label="Short description"
        value={listing.listing.shortDescription}
        copyKey={`${listing.id}:short`}
        copiedKey={copiedKey}
        onCopy={onCopy}
      />
      <ListingField
        label="Long description"
        value={listing.listing.longDescription}
        copyKey={`${listing.id}:long`}
        copiedKey={copiedKey}
        onCopy={onCopy}
      />
      <ListingField
        label="SEO keywords"
        value={keywordText}
        copyKey={`${listing.id}:keywords`}
        copiedKey={copiedKey}
        onCopy={onCopy}
      />
      <ListingField
        label="Product tags"
        value={tagText}
        copyKey={`${listing.id}:tags`}
        copiedKey={copiedKey}
        onCopy={onCopy}
      />
    </div>
  );
}

interface ListingFieldProps {
  label: string;
  value: string;
  copyKey: string;
  copiedKey: string | null;
  onCopy: (key: string, value: string) => Promise<void>;
}

function ListingField({ label, value, copyKey, copiedKey, onCopy }: ListingFieldProps) {
  return (
    <section className="grid gap-2">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-medium">{label}</h3>
        <Button
          className="h-8 px-3"
          type="button"
          variant="secondary"
          onClick={() => onCopy(copyKey, value)}
        >
          <Clipboard className="mr-2 size-4" aria-hidden="true" />
          {copiedKey === copyKey ? 'Copied' : 'Copy'}
        </Button>
      </div>
      <p className="break-words rounded-md border border-white/10 bg-background/45 p-3 text-muted-foreground">
        {value}
      </p>
    </section>
  );
}
