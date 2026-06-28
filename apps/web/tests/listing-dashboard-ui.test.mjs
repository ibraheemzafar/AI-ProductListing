import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { URL } from 'node:url';

function readSource(path) {
  return readFileSync(new URL(path, import.meta.url), 'utf8');
}

test('dashboard page includes listing history success and empty states', () => {
  const source = readSource('../app/dashboard/page.tsx');
  const listingHistorySource = readSource('../app/dashboard/listing-history-view.tsx');

  assert.match(source, /Workspace History/);
  assert.match(source, /ListingHistoryView/);
  assert.match(source, /enrichListingsWithCategory/);
  assert.match(listingHistorySource, /filteredListings\.map/);
  assert.match(listingHistorySource, /No product workflows yet/);
  assert.match(listingHistorySource, /No workflows match your filters/);
  assert.match(listingHistorySource, /StatusBadge/);
  assert.match(source, /Upload images/);
});

test('dashboard route includes loading and error states', () => {
  const loadingSource = readSource('../app/dashboard/loading.tsx');
  const errorSource = readSource('../app/dashboard/error.tsx');
  const rootErrorSource = readSource('../app/error.tsx');
  const globalErrorSource = readSource('../app/global-error.tsx');

  assert.match(loadingSource, /DashboardLoading/);
  assert.match(errorSource, /Workspace History could not load/);
  assert.match(errorSource, /Try again/);
  assert.match(rootErrorSource, /Something went wrong/);
  assert.match(globalErrorSource, /Application error/);
});

test('upload workspace displays invalid product image validation state', () => {
  const source = readSource('../app/dashboard/upload/upload-workspace.tsx');

  assert.match(source, /No clear product was detected/);
  assert.match(source, /No recognizable product was found/);
  assert.match(source, /Upload a clear image with one primary product/);
  assert.match(source, /listing: 'skipped'/);
  assert.match(source, /seo: 'skipped'/);
  assert.match(source, /marketplace: 'skipped'/);
});

test('listing detail view includes generated listing fields and copy actions', () => {
  const source = readSource('../app/dashboard/listings/[listingId]/listing-detail-view.tsx');

  assert.match(source, /ResultTabs/);
  assert.match(source, /OverviewPanel/);
  assert.match(source, /ListingPanel/);
  assert.match(source, /ImageGallery/);
  assert.match(source, /MarketplacePanel/);
  assert.match(source, /MarketingPanel/);
  assert.match(source, /HistoryPanel/);
  assert.match(source, /Product Intelligence/);
  assert.match(source, /Copy full copy/);
  assert.match(source, /Shopify CSV/);
  assert.match(source, /Analyze in SEO Studio/);
  assert.match(source, /Improve/);
  assert.match(source, /Regenerate/);
  assert.match(source, /Create channel content/);
  assert.match(source, /Creative Studio/);
  assert.match(source, /Generate creative/);
  assert.match(source, /Before/);
  assert.match(source, /After/);
  assert.match(source, /Shopify/);
  assert.match(source, /Amazon/);
  assert.match(source, /Etsy/);
  assert.match(source, /Daraz/);
  assert.match(source, /Optimized title/);
  assert.match(source, /Bullet points/);
  assert.match(source, /Keywords \/ tags/);
  assert.match(source, /SEO Studio quality/);
  assert.match(source, /Workspace History/);
  assert.match(source, /Open Marketing Studio/);
  assert.match(source, /ScoreMeter/);
  assert.match(source, /Short description/);
  assert.match(source, /Long description/);
  assert.match(source, /SEO keywords/);
  assert.match(source, /Product tags/);
  assert.match(source, /navigator\.clipboard\.writeText/);
  assert.match(source, /getListingJsonExport/);
  assert.match(source, /getListingShopifyCsvExport/);
  assert.match(source, /analyzeListingSeo/);
  assert.match(source, /improveListing/);
  assert.match(source, /optimizeListingForMarketplace/);
  assert.match(source, /getMarketplaceOptimizations/);
  assert.match(source, /generateLifestyleScene/);
  assert.match(source, /deleteGeneratedLifestyleScene/);
  assert.match(source, /acceptListingVersion/);
  assert.match(source, /getListingVersions/);
  assert.match(source, /regenerateListing/);
  assert.match(source, /JSON export downloaded/);
  assert.match(source, /Shopify CSV downloaded/);
  assert.match(source, /SEO Studio analysis completed/);
  assert.match(source, /Improved version created/);
  assert.match(source, /Version accepted/);
  assert.match(source, /Marketplace Studio content ready/);
  assert.match(source, /Generated image saved/);
  assert.match(source, /Copy failed/);
});

test('listing detail route includes loading, error, and not found states', () => {
  const loadingSource = readSource('../app/dashboard/listings/[listingId]/loading.tsx');
  const errorSource = readSource('../app/dashboard/listings/[listingId]/error.tsx');
  const notFoundSource = readSource('../app/dashboard/listings/[listingId]/not-found.tsx');

  assert.match(loadingSource, /ListingDetailLoading/);
  assert.match(errorSource, /Product workspace could not load/);
  assert.match(notFoundSource, /Workspace not found/);
});
