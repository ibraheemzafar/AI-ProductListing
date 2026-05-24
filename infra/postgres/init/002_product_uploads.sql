CREATE TABLE IF NOT EXISTS products (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL REFERENCES users(id),
  title VARCHAR(255),
  category VARCHAR(255),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_products_user_id ON products (user_id);

CREATE TABLE IF NOT EXISTS product_images (
  id VARCHAR(36) PRIMARY KEY,
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  original_filename VARCHAR(255) NOT NULL,
  storage_filename VARCHAR(255) NOT NULL UNIQUE,
  image_url VARCHAR(2048) NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  size_bytes INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_product_images_product_id ON product_images (product_id);

CREATE TABLE IF NOT EXISTS product_analysis_results (
  id VARCHAR(36) PRIMARY KEY,
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  image_id VARCHAR(36) NOT NULL REFERENCES product_images(id),
  category VARCHAR(255) NOT NULL,
  product_type VARCHAR(255) NOT NULL,
  color VARCHAR(255) NOT NULL,
  material VARCHAR(255) NOT NULL,
  style VARCHAR(255) NOT NULL,
  visible_text_brand VARCHAR(255) NOT NULL,
  target_audience VARCHAR(255) NOT NULL,
  raw_attributes JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_product_analysis_results_product_id
  ON product_analysis_results (product_id);
CREATE INDEX IF NOT EXISTS ix_product_analysis_results_image_id
  ON product_analysis_results (image_id);

CREATE TABLE IF NOT EXISTS ai_request_logs (
  id VARCHAR(36) PRIMARY KEY,
  user_id VARCHAR(36) NOT NULL REFERENCES users(id),
  product_id VARCHAR(36) REFERENCES products(id),
  image_id VARCHAR(36) REFERENCES product_images(id),
  workflow_name VARCHAR(100) NOT NULL,
  model_name VARCHAR(100) NOT NULL,
  prompt_version VARCHAR(50) NOT NULL,
  input_tokens INTEGER,
  output_tokens INTEGER,
  total_tokens INTEGER,
  latency_ms INTEGER NOT NULL,
  success BOOLEAN NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'success',
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ai_request_logs_user_id ON ai_request_logs (user_id);
CREATE INDEX IF NOT EXISTS ix_ai_request_logs_user_workflow_created_at
  ON ai_request_logs (user_id, workflow_name, created_at DESC);
ALTER TABLE ai_request_logs
  ADD COLUMN IF NOT EXISTS status VARCHAR(50) NOT NULL DEFAULT 'success';

CREATE TABLE IF NOT EXISTS generated_listings (
  id VARCHAR(36) PRIMARY KEY,
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  analysis_id VARCHAR(36) NOT NULL REFERENCES product_analysis_results(id),
  title VARCHAR(255) NOT NULL,
  short_description TEXT NOT NULL,
  long_description TEXT NOT NULL,
  seo_keywords JSONB NOT NULL,
  product_tags JSONB NOT NULL,
  raw_output JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_generated_listings_product_id
  ON generated_listings (product_id);
CREATE INDEX IF NOT EXISTS ix_generated_listings_analysis_id
  ON generated_listings (analysis_id);
CREATE INDEX IF NOT EXISTS ix_generated_listings_product_created_at
  ON generated_listings (product_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_product_images_product_created_at
  ON product_images (product_id, created_at DESC);

CREATE TABLE IF NOT EXISTS seo_analysis (
  id VARCHAR(36) PRIMARY KEY,
  listing_id VARCHAR(36) NOT NULL REFERENCES generated_listings(id),
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  seo_score INTEGER NOT NULL,
  readability_score INTEGER NOT NULL,
  keyword_optimization_feedback TEXT NOT NULL,
  title_quality_feedback TEXT NOT NULL,
  description_quality_feedback TEXT NOT NULL,
  strengths JSONB NOT NULL,
  weaknesses JSONB NOT NULL,
  improvement_suggestions JSONB NOT NULL,
  raw_output JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_seo_analysis_listing_id ON seo_analysis (listing_id);
CREATE INDEX IF NOT EXISTS ix_seo_analysis_product_id ON seo_analysis (product_id);
CREATE INDEX IF NOT EXISTS ix_seo_analysis_listing_created_at
  ON seo_analysis (listing_id, created_at DESC);

CREATE TABLE IF NOT EXISTS listing_versions (
  id VARCHAR(36) PRIMARY KEY,
  listing_id VARCHAR(36) NOT NULL REFERENCES generated_listings(id),
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  version_number INTEGER NOT NULL,
  title VARCHAR(255) NOT NULL,
  short_description TEXT NOT NULL,
  long_description TEXT NOT NULL,
  seo_keywords JSONB NOT NULL,
  product_tags JSONB NOT NULL,
  source VARCHAR(50) NOT NULL DEFAULT 'ai_improvement',
  is_accepted BOOLEAN NOT NULL DEFAULT FALSE,
  raw_output JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  accepted_at TIMESTAMPTZ,
  UNIQUE (listing_id, version_number)
);

CREATE INDEX IF NOT EXISTS ix_listing_versions_listing_id ON listing_versions (listing_id);
CREATE INDEX IF NOT EXISTS ix_listing_versions_product_id ON listing_versions (product_id);
CREATE INDEX IF NOT EXISTS ix_listing_versions_listing_version
  ON listing_versions (listing_id, version_number DESC);

CREATE TABLE IF NOT EXISTS marketplace_optimizations (
  id VARCHAR(36) PRIMARY KEY,
  listing_id VARCHAR(36) NOT NULL REFERENCES generated_listings(id),
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  marketplace VARCHAR(50) NOT NULL,
  optimized_title VARCHAR(255) NOT NULL,
  optimized_description TEXT NOT NULL,
  bullet_points JSONB NOT NULL,
  keywords_tags JSONB NOT NULL,
  platform_notes TEXT NOT NULL,
  raw_output JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_marketplace_optimizations_listing_id
  ON marketplace_optimizations (listing_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_optimizations_product_id
  ON marketplace_optimizations (product_id);
CREATE INDEX IF NOT EXISTS ix_marketplace_optimizations_listing_marketplace_created_at
  ON marketplace_optimizations (listing_id, marketplace, created_at DESC);

CREATE TABLE IF NOT EXISTS enhanced_images (
  id VARCHAR(36) PRIMARY KEY,
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  original_image_id VARCHAR(36) NOT NULL REFERENCES product_images(id),
  operation VARCHAR(50) NOT NULL,
  provider_name VARCHAR(100) NOT NULL,
  storage_filename VARCHAR(255) NOT NULL UNIQUE,
  enhanced_image_url VARCHAR(2048) NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  size_bytes INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_enhanced_images_product_id
  ON enhanced_images (product_id);
CREATE INDEX IF NOT EXISTS ix_enhanced_images_original_image_id
  ON enhanced_images (original_image_id);
CREATE INDEX IF NOT EXISTS ix_enhanced_images_original_operation_created_at
  ON enhanced_images (original_image_id, operation, created_at DESC);

CREATE TABLE IF NOT EXISTS generated_images (
  id VARCHAR(36) PRIMARY KEY,
  product_id VARCHAR(36) NOT NULL REFERENCES products(id),
  listing_id VARCHAR(36) NOT NULL REFERENCES generated_listings(id),
  source_image_id VARCHAR(36) NOT NULL REFERENCES product_images(id),
  source_enhanced_image_id VARCHAR(36) REFERENCES enhanced_images(id),
  scene_preset VARCHAR(100) NOT NULL,
  custom_prompt TEXT,
  prompt TEXT NOT NULL,
  provider_name VARCHAR(100) NOT NULL,
  storage_filename VARCHAR(255) NOT NULL UNIQUE,
  generated_image_url VARCHAR(2048) NOT NULL,
  content_type VARCHAR(100) NOT NULL,
  size_bytes INTEGER NOT NULL,
  generation_time_ms INTEGER NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'success',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_generated_images_product_id
  ON generated_images (product_id);
CREATE INDEX IF NOT EXISTS ix_generated_images_listing_id
  ON generated_images (listing_id);
CREATE INDEX IF NOT EXISTS ix_generated_images_listing_created_at
  ON generated_images (listing_id, created_at DESC);
