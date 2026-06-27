'use client';

import {
  ArrowRight,
  Check,
  Circle,
  FileText,
  ImageIcon,
  Loader2,
  PackageCheck,
  Search,
  Sparkles,
  WandSparkles,
} from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import type {
  GeneratedListingResult,
  Marketplace,
  ProductAnalysisResult,
  ScenePreset,
  UploadedProductImage,
} from '@ai-product-listing/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { analyzeProductImage, getAnalysisVersions } from '@/lib/api/analysis';
import { notifyWalletChanged } from '@/lib/api/billing';
import { generateLifestyleScene } from '@/lib/api/lifestyle-scenes';
import { generateListing, getListingVersions } from '@/lib/api/listings';
import { optimizeListingForMarketplace } from '@/lib/api/marketplace-optimizations';
import { analyzeListingSeo } from '@/lib/api/seo-analysis';
import { UploadForm } from './upload-form';

interface UploadWorkspaceProps {
  initialImages: UploadedProductImage[];
}

type WorkflowStepKey =
  | 'upload'
  | 'analysis'
  | 'listing'
  | 'seo'
  | 'marketplace'
  | 'image'
  | 'finalizing';

type WorkflowStepStatus = 'pending' | 'running' | 'completed' | 'skipped' | 'error';

type WorkflowStatusByStep = Record<WorkflowStepKey, WorkflowStepStatus>;

interface WorkflowRunState {
  statusByStep: WorkflowStatusByStep;
  message?: string;
  listingId?: string;
}

const defaultWorkflowStatus: WorkflowStatusByStep = {
  upload: 'completed',
  analysis: 'pending',
  listing: 'pending',
  seo: 'pending',
  marketplace: 'pending',
  image: 'pending',
  finalizing: 'pending',
};

const workflowSteps: Array<{
  key: WorkflowStepKey;
  label: string;
  description: string;
  icon: typeof Sparkles;
}> = [
  {
    key: 'upload',
    label: 'Upload complete',
    description: 'Product image is available in the workspace.',
    icon: Check,
  },
  {
    key: 'analysis',
    label: 'Analyzing product',
    description: 'Extracting product category, attributes, and audience.',
    icon: Search,
  },
  {
    key: 'listing',
    label: 'Generating listing',
    description: 'Creating title, description, tags, and keywords.',
    icon: FileText,
  },
  {
    key: 'seo',
    label: 'Optimizing SEO',
    description: 'Checking listing quality and keyword opportunities.',
    icon: Sparkles,
  },
  {
    key: 'marketplace',
    label: 'Creating marketplace content',
    description: 'Preparing reusable ecommerce platform content.',
    icon: PackageCheck,
  },
  {
    key: 'image',
    label: 'Generating lifestyle images',
    description: 'Creating an optional product lifestyle scene.',
    icon: ImageIcon,
  },
  {
    key: 'finalizing',
    label: 'Finalizing assets',
    description: 'Saving generated results and opening the listing workspace.',
    icon: WandSparkles,
  },
];

const defaultMarketplace: Marketplace = 'shopify';
const defaultScenePreset: ScenePreset = 'lifestyle_home_setup';
const invalidProductImageMessage =
  'No clear product was detected. Please upload a clear product image.';

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
  const [errorByImageId, setErrorByImageId] = useState<Record<string, string>>({});
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [workflowByImageId, setWorkflowByImageId] = useState<Record<string, WorkflowRunState>>({});
  const [activeImageId, setActiveImageId] = useState<string | null>(null);
  const [includeSeo, setIncludeSeo] = useState(true);
  const [includeMarketplace, setIncludeMarketplace] = useState(true);
  const [includeLifestyleImage, setIncludeLifestyleImage] = useState(false);

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

  async function handleGenerateAssets(image: UploadedProductImage) {
    if (activeImageId) {
      return;
    }

    setActiveImageId(image.id);
    clearError(image.id);
    setWorkflow(image.id, {
      statusByStep: {
        ...defaultWorkflowStatus,
        seo: includeSeo ? 'pending' : 'skipped',
        marketplace: includeMarketplace ? 'pending' : 'skipped',
        image: includeLifestyleImage ? 'pending' : 'skipped',
      },
      message: 'Starting asset generation.',
    });

    try {
      setStepStatus(image.id, 'analysis', 'running', 'Analyzing product image.');
      const analysis = analysisByImageId[image.id] ?? (await analyzeProductImage(image.id));
      setAnalysisByImageId((current) => ({ ...current, [image.id]: analysis }));
      notifyWalletChanged();
      setStepStatus(image.id, 'analysis', 'completed', 'Product analysis completed.');

      setStepStatus(image.id, 'listing', 'running', 'Generating listing copy.');
      const listing =
        listingByImageId[image.id] ?? (await generateListing(analysis.id));
      setListingByImageId((current) => ({ ...current, [image.id]: listing }));
      notifyWalletChanged();
      setWorkflowListingId(image.id, listing.id);
      setStepStatus(image.id, 'listing', 'completed', 'Listing generated.');

      if (includeSeo) {
        await runOptionalStep(image.id, 'seo', 'SEO analysis completed.', () =>
          analyzeListingSeo(listing.id),
        );
      } else {
        setStepStatus(image.id, 'seo', 'skipped', 'SEO optimization skipped.');
      }

      if (includeMarketplace) {
        await runOptionalStep(
          image.id,
          'marketplace',
          'Marketplace content created.',
          () => optimizeListingForMarketplace(listing.id, defaultMarketplace),
        );
      } else {
        setStepStatus(image.id, 'marketplace', 'skipped', 'Marketplace content skipped.');
      }

      if (includeLifestyleImage) {
        await runOptionalStep(
          image.id,
          'image',
          'Lifestyle image generated.',
          () => generateLifestyleScene(listing.id, defaultScenePreset, ''),
        );
      } else {
        setStepStatus(image.id, 'image', 'skipped', 'Lifestyle image skipped.');
      }

      setStepStatus(image.id, 'finalizing', 'running', 'Finalizing generated assets.');
      notifyWalletChanged();
      setStepStatus(image.id, 'finalizing', 'completed', 'AI assets are ready.');
      showToast('AI assets generated.');
      router.refresh();
    } catch (error) {
      const message = error instanceof Error ? error.message : 'AI asset generation failed.';
      if (isInvalidProductImageError(message)) {
        setWorkflow(image.id, {
          statusByStep: {
            upload: 'completed',
            analysis: 'error',
            listing: 'skipped',
            seo: 'skipped',
            marketplace: 'skipped',
            image: 'skipped',
            finalizing: 'skipped',
          },
          message,
        });
      }
      setErrorByImageId((current) => ({ ...current, [image.id]: message }));
      setWorkflowMessage(image.id, message);
      showToast(message);
    } finally {
      setActiveImageId(null);
    }
  }

  async function runOptionalStep(
    imageId: string,
    step: WorkflowStepKey,
    successMessage: string,
    action: () => Promise<unknown>,
  ) {
    setStepStatus(imageId, step, 'running');
    try {
      await action();
      notifyWalletChanged();
      setStepStatus(imageId, step, 'completed', successMessage);
    } catch (error) {
      const message = error instanceof Error ? error.message : `${successMessage} skipped.`;
      setStepStatus(imageId, step, 'skipped', message);
    }
  }

  function setWorkflow(imageId: string, workflow: WorkflowRunState) {
    setWorkflowByImageId((current) => ({ ...current, [imageId]: workflow }));
  }

  function setWorkflowListingId(imageId: string, listingId: string) {
    setWorkflowByImageId((current) => ({
      ...current,
      [imageId]: {
        ...current[imageId],
        listingId,
        statusByStep: current[imageId]?.statusByStep ?? defaultWorkflowStatus,
      },
    }));
  }

  function setWorkflowMessage(imageId: string, message: string) {
    setWorkflowByImageId((current) => ({
      ...current,
      [imageId]: {
        ...current[imageId],
        message,
        statusByStep: current[imageId]?.statusByStep ?? defaultWorkflowStatus,
      },
    }));
  }

  function setStepStatus(
    imageId: string,
    step: WorkflowStepKey,
    status: WorkflowStepStatus,
    message?: string,
  ) {
    setWorkflowByImageId((current) => {
      const previous = current[imageId] ?? { statusByStep: defaultWorkflowStatus };
      return {
        ...current,
        [imageId]: {
          ...previous,
          message: message ?? previous.message,
          statusByStep: {
            ...previous.statusByStep,
            [step]: status,
          },
        },
      };
    });
  }

  function clearError(imageId: string) {
    setErrorByImageId((current) => {
      const next = { ...current };
      delete next[imageId];
      return next;
    });
  }

  function showToast(message: string) {
    setToastMessage(message);
    window.setTimeout(() => setToastMessage(null), 2500);
  }

  function isInvalidProductImageError(message: string) {
    return message === invalidProductImageMessage;
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
        <div className="mt-1 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
            Generate the full asset workflow from each uploaded image with one primary action.
          </p>
          <div className="grid gap-2 rounded-lg border border-white/10 bg-background/45 p-3 text-sm sm:grid-cols-3">
            <WorkflowOption
              checked={includeSeo}
              disabled={Boolean(activeImageId)}
              label="SEO Optimization"
              onChange={setIncludeSeo}
            />
            <WorkflowOption
              checked={includeMarketplace}
              disabled={Boolean(activeImageId)}
              label="Marketplace Copy"
              onChange={setIncludeMarketplace}
            />
            <WorkflowOption
              checked={includeLifestyleImage}
              disabled={Boolean(activeImageId)}
              label="Lifestyle Images"
              onChange={setIncludeLifestyleImage}
            />
          </div>
        </div>
        <div className="mt-5 grid gap-3">
          {initialImages.length > 0 ? (
            initialImages.map((image) => {
              const analysis = analysisByImageId[image.id];
              const listing = listingByImageId[image.id];
              const workflow = workflowByImageId[image.id];
              const errorMessage = errorByImageId[image.id];
              const isGeneratingAssets = activeImageId === image.id;

              return (
                <div
                  key={image.id}
                  className="rounded-lg border border-white/10 bg-secondary/60 p-4 transition hover:border-primary/35"
                >
                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_360px]">
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
                      <p className="mt-3 text-sm leading-6 text-muted-foreground">
                        {listing
                          ? 'Listing assets are ready to review.'
                          : analysis
                            ? 'Product analysis is ready. Generate listing assets next.'
                            : 'Ready to generate AI assets.'}
                      </p>
                      {workflow?.message ? (
                        <p className="mt-2 text-xs text-muted-foreground">{workflow.message}</p>
                      ) : null}
                    </div>
                  </div>

                    <WorkflowProgress
                      statusByStep={
                        workflow?.statusByStep ?? {
                          ...defaultWorkflowStatus,
                          analysis: analysis ? 'completed' : 'pending',
                          listing: listing ? 'completed' : 'pending',
                          seo: 'pending',
                          marketplace: 'pending',
                          image: includeLifestyleImage ? 'pending' : 'skipped',
                          finalizing: listing ? 'completed' : 'pending',
                        }
                      }
                    />
                  </div>

                  {errorMessage ? (
                    isInvalidProductImageError(errorMessage) ? (
                      <InvalidProductImagePanel />
                    ) : (
                      <p className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
                        {errorMessage}
                      </p>
                    )
                  ) : null}

                  {analysis ? (
                    <div className="mt-4 border-t border-white/10 pt-4">
                      <AnalysisAttributes analysis={analysis} />
                    </div>
                  ) : null}

                  <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-white/10 pt-4">
                    <Button
                      type="button"
                      onClick={() => void handleGenerateAssets(image)}
                      disabled={Boolean(activeImageId)}
                      className="min-w-48"
                    >
                      {isGeneratingAssets ? (
                        <Loader2 className="mr-2 size-4 animate-spin" aria-hidden="true" />
                      ) : (
                        <Sparkles className="mr-2 size-4" aria-hidden="true" />
                      )}
                      {isGeneratingAssets ? 'Generating assets' : 'Generate AI Assets'}
                    </Button>
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

function WorkflowOption({
  checked,
  disabled,
  label,
  onChange,
}: {
  checked: boolean;
  disabled: boolean;
  label: string;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-muted-foreground transition hover:bg-white/[0.05] hover:text-white">
      <input
        checked={checked}
        className="size-4 accent-primary"
        disabled={disabled}
        type="checkbox"
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>{label}</span>
    </label>
  );
}

function InvalidProductImagePanel() {
  return (
    <div className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-3 text-sm text-red-100">
      <p className="font-semibold">No recognizable product was found.</p>
      <p className="mt-1 leading-5 text-red-100/85">
        Upload a clear image with one primary product. Placeholder graphics, blank images,
        screenshots, logo-only images, or text-only images cannot be used for listing generation.
      </p>
    </div>
  );
}

function WorkflowProgress({ statusByStep }: { statusByStep: WorkflowStatusByStep }) {
  return (
    <ol className="grid gap-2 rounded-lg border border-white/10 bg-background/45 p-3">
      {workflowSteps.map((step) => {
        const status = statusByStep[step.key];
        const Icon = step.icon;
        return (
          <li key={step.key} className="flex items-start gap-3">
            <span
              className={cn(
                'mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full border',
                status === 'completed' && 'border-primary/50 bg-primary/20 text-white',
                status === 'running' && 'border-accent/60 bg-accent/10 text-accent',
                status === 'skipped' && 'border-white/10 bg-white/[0.03] text-muted-foreground',
                status === 'error' && 'border-red-400/50 bg-red-500/10 text-red-100',
                status === 'pending' && 'border-white/10 text-muted-foreground',
              )}
            >
              {status === 'running' ? (
                <Loader2 className="size-3.5 animate-spin" aria-hidden="true" />
              ) : status === 'completed' ? (
                <Check className="size-3.5" aria-hidden="true" />
              ) : status === 'pending' ? (
                <Circle className="size-3" aria-hidden="true" />
              ) : (
                <Icon className="size-3.5" aria-hidden="true" />
              )}
            </span>
            <span className="min-w-0">
              <span
                className={cn(
                  'block text-sm font-medium',
                  status === 'completed' || status === 'running' ? 'text-white' : 'text-muted-foreground',
                )}
              >
                {step.label}
              </span>
              <span className="block text-xs leading-5 text-muted-foreground">
                {status === 'skipped' ? 'Skipped for this run.' : step.description}
              </span>
            </span>
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
