/**
 * Shared UI copy for the product workspace.
 *
 * The "already done" warnings are surfaced when a user tries to re-run an AI
 * workflow (analysis or listing generation) that has already completed for a
 * product, since re-running spends AI tokens and can incur additional cost.
 */
export const ANALYSIS_ALREADY_DONE_MESSAGE =
  'Product Intelligence is already complete for this image. Re-running will call the AI again and cost you tokens. Continue only if you want to redo it.';

export const LISTING_ALREADY_DONE_MESSAGE =
  'Listing Studio content has already been generated for this product. Re-running will call the AI again and cost you tokens. Continue only if you want to redo it.';
