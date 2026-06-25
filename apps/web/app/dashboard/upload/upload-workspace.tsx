'use client';

import { ArrowRight, Check, Sparkles, WandSparkles } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import type {
  GeneratedListingResult,
  ProductAnalysisResult,
  UploadedProductImage,
} from '@ai-product-listing/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { analyzeProductImage, getAnalysisVersions } from '@/lib/api/analysis';
import { notifyWalletChanged } from '@/lib/api/billing';
import { generateListing, getListingVersions } from '@/lib/api/listings';
import { UploadForm } from './upload-form';

interface UploadWorkspaceProps {
  initialImages: UploadedProductImage[];
}

// The upload page is a linear wizard: Analyze -> Generate -> open the listing detail page,
// where all editing, versioning, SEO, and image work lives. No inline versioning here.
export function UploadWorkspace({ initialImages }: UploadWorkspaceProps) {
  const router = useRouter();
  const [analysisByImageId, setAnalysisByImageId] = useState<
    Record<string, ProductAnalysisResult>
  >({});
  const [listingByImageId, setListingByImageId] = useState<
    Record<string, GeneratedListingResult>
  >({});
  const [analyzingImageId, setAnalyzingImageId] = useState<string | null>(null);
  const [generatingImageId, setGeneratingImageId] = useState<string | null>(null);
  const [errorByImageId, setErrorByImageId] = useState<Record<string, string>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Surface any previously generated analysis/listing without spending tokens, so the wizard
  // resumes at the right step (and links straight to an existing listing).
  useEffect(() => {
    let cancelled = false;

    async function preloadExistingResults() {
      for (const image of initialImages) {
        const [analysis] = await getAnalysisVersions(image.id);
        if (cancelled || !analysis) {
          continue;
        }
        setAnalysisByImageId((current) => ({ ...current, [image.id]: analysis }));

        const [listing] = await getListingVersions(analysis.id);
        if (cancelled || !listing) {
          continue;
        }
        setListingByImageId((current) => ({ ...current, [image.id]: listing }));
      }
    }

    void preloadExistingResults();

    return () => {
      cancelled = true;
    };
  }, [initialImages]);

  async function handleAnalyzeImage(imageId: string) {
    setAnalyzingImageId(imageId);
    clearError(imageId);
    try {
      const analysis = await analyzeProductImage(imageId);
      setAnalysisByImageId((current) => ({ ...current, [imageId]: analysis }));
      notifyWalletChanged();
      showToast('Product analysis completed.');
    } catch (error) {
      handleError(imageId, error, 'Product analysis failed.');
    } finally {
      setAnalyzingImageId(null);
    }
  }

  async function handleGenerateListing(imageId: string, analysisId: string) {
    setGeneratingImageId(imageId);
    clearError(imageId);
    try {
      const listing = await generateListing(analysisId);
      setListingByImageId((current) => ({ ...current, [imageId]: listing }));
      notifyWalletChanged();
      showToast('Listing generated.');
    } catch (error) {
      handleError(imageId, error, 'Listing generation failed.');
    } finally {
      setGeneratingImageId(null);
    }
  }

  function clearError(imageId: string) {
    setErrorByImageId((current) => {
      const next = { ...current };
      delete next[imageId];
      return next;
    });
  }

  function handleError(imageId: string, error: unknown, fallback: string) {
    const message = error instanceof Error ? error.message : fallback;
    setErrorByImageId((current) => ({ ...current, [imageId]: message }));
    showToast(message);
  }

  function showToast(message: string) {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 2500);
  }

  return (
    <div className="flex flex-col gap-8">
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
        <p className="mt-1 text-sm text-muted-foreground">
          Analyze each product, generate its listing, then open the listing to refine it.
        </p>
        <div className="mt-5 grid gap-3">
          {initialImages.length > 0 ? (
            initialImages.map((image) => {
              const analysis = analysisByImageId[image.id];
              const listing = listingByImageId[image.id];
              const step = listing ? 3 : analysis ? 2 : 1;

              return (
                <div
                  key={image.id}
                  className="rounded-lg border border-white/10 bg-secondary/60 p-4 transition hover:border-primary/35"
                >
                  <div className="flex gap-4">
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
                      <WizardSteps current={step} />
                    </div>
                  </div>

                  {errorByImageId[image.id] ? (
                    <p className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                      {errorByImageId[image.id]}
                    </p>
                  ) : null}

                  {analysis ? (
                    <div className="mt-4 border-t border-white/10 pt-4">
                      <AnalysisAttributes analysis={analysis} />
                    </div>
                  ) : null}

                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    {!analysis ? (
                      <Button
                        type="button"
                        onClick={() => handleAnalyzeImage(image.id)}
                        disabled={analyzingImageId === image.id}
                      >
                        <Sparkles className="mr-2 size-4" aria-hidden="true" />
                        {analyzingImageId === image.id ? 'Analyzing' : 'Analyze product'}
                      </Button>
                    ) : null}

                    {analysis && !listing ? (
                      <Button
                        type="button"
                        onClick={() => handleGenerateListing(image.id, analysis.id)}
                        disabled={generatingImageId === image.id}
                      >
                        <WandSparkles className="mr-2 size-4" aria-hidden="true" />
                        {generatingImageId === image.id ? 'Generating' : 'Generate listing'}
                      </Button>
                    ) : null}

                    {listing ? (
                      <>
                        <p className="min-w-0 flex-1 truncate text-sm text-muted-foreground">
                          {listing.listing.title}
                        </p>
                        <Button asChild>
                          <Link href={`/dashboard/listings/${listing.id}`}>
                            View listing
                            <ArrowRight className="ml-2 size-4" aria-hidden="true" />
                          </Link>
                        </Button>
                      </>
                    ) : null}
                  </div>
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

const WIZARD_STEPS = ['Analyze', 'Generate', 'Open listing'];

function WizardSteps({ current }: { current: number }) {
  return (
    <ol className="mt-3 flex flex-wrap items-center gap-2 text-xs">
      {WIZARD_STEPS.map((label, index) => {
        const stepNumber = index + 1;
        const isComplete = current > stepNumber;
        const isActive = current === stepNumber;
        return (
          <li key={label} className="flex items-center gap-2">
            <span
              className={cn(
                'flex size-5 items-center justify-center rounded-full border text-[11px] font-semibold',
                isComplete
                  ? 'border-primary/60 bg-primary/20 text-white'
                  : isActive
                    ? 'border-primary/60 text-white'
                    : 'border-white/15 text-muted-foreground',
              )}
            >
              {isComplete ? <Check className="size-3" aria-hidden="true" /> : stepNumber}
            </span>
            <span className={isActive || isComplete ? 'text-white' : 'text-muted-foreground'}>
              {label}
            </span>
            {stepNumber < WIZARD_STEPS.length ? (
              <span className="text-white/20" aria-hidden="true">
                /
              </span>
            ) : null}
          </li>
        );
      })}
    </ol>
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
    <dl className="grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-3">
      {attributes.map(([label, value]) => (
        <div key={label} className="rounded-md border border-white/10 bg-background/45 px-3 py-2">
          <dt className="text-xs uppercase tracking-wide text-muted-foreground">{label}</dt>
          <dd className="mt-1 min-w-0 break-words font-medium text-white">{value}</dd>
        </div>
      ))}
    </dl>
  );
}
