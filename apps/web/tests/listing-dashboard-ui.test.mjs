import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { URL } from 'node:url';

function readSource(path) {
  return readFileSync(new URL(path, import.meta.url), 'utf8');
}

test('dashboard page includes listing history success and empty states', () => {
  const source = readSource('../app/dashboard/page.tsx');

  assert.match(source, /Listing history/);
  assert.match(source, /history\.listings\.map/);
  assert.match(source, /No generated listings yet/);
  assert.match(source, /Upload images/);
});

test('dashboard route includes loading and error states', () => {
  const loadingSource = readSource('../app/dashboard/loading.tsx');
  const errorSource = readSource('../app/dashboard/error.tsx');
  const rootErrorSource = readSource('../app/error.tsx');
  const globalErrorSource = readSource('../app/global-error.tsx');

  assert.match(loadingSource, /DashboardLoading/);
  assert.match(errorSource, /Listing history could not load/);
  assert.match(errorSource, /Try again/);
  assert.match(rootErrorSource, /Something went wrong/);
  assert.match(globalErrorSource, /Application error/);
});

test('listing detail view includes generated listing fields and copy actions', () => {
  const source = readSource('../app/dashboard/listings/[listingId]/listing-detail-view.tsx');

  assert.match(source, /Product analysis/);
  assert.match(source, /Copy All/);
  assert.match(source, /JSON/);
  assert.match(source, /Shopify CSV/);
  assert.match(source, /Analyze SEO/);
  assert.match(source, /Improve with AI/);
  assert.match(source, /Regenerate/);
  assert.match(source, /Optimize/);
  assert.match(source, /Image studio/);
  assert.match(source, /Background removal/);
  assert.match(source, /Image cleanup/);
  assert.match(source, /Image optimization/);
  assert.match(source, /ImageProcessingProgress/);
  assert.match(source, /ImageEnhancementPanel/);
  assert.match(source, /Before/);
  assert.match(source, /After/);
  assert.match(source, /Download enhanced image/);
  assert.match(source, /Shopify/);
  assert.match(source, /Amazon/);
  assert.match(source, /Etsy/);
  assert.match(source, /Daraz/);
  assert.match(source, /MarketplaceOptimizationPanel/);
  assert.match(source, /Optimized title/);
  assert.match(source, /Bullet points/);
  assert.match(source, /Keywords \/ tags/);
  assert.match(source, /SEO quality/);
  assert.match(source, /Before \/ after comparison/);
  assert.match(source, /Accept improved version/);
  assert.match(source, /Version history/);
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
  assert.match(source, /enhanceListingImage/);
  assert.match(source, /acceptListingVersion/);
  assert.match(source, /getListingVersions/);
  assert.match(source, /regenerateListing/);
  assert.match(source, /JSON export downloaded/);
  assert.match(source, /Shopify CSV downloaded/);
  assert.match(source, /SEO analysis completed/);
  assert.match(source, /Improved version created/);
  assert.match(source, /Improved version accepted/);
  assert.match(source, /Marketplace optimization ready/);
  assert.match(source, /Image enhancement completed/);
  assert.match(source, /Copy failed/);
});

test('listing detail route includes loading, error, and not found states', () => {
  const loadingSource = readSource('../app/dashboard/listings/[listingId]/loading.tsx');
  const errorSource = readSource('../app/dashboard/listings/[listingId]/error.tsx');
  const notFoundSource = readSource('../app/dashboard/listings/[listingId]/not-found.tsx');

  assert.match(loadingSource, /ListingDetailLoading/);
  assert.match(errorSource, /Listing detail could not load/);
  assert.match(notFoundSource, /Listing not found/);
});
