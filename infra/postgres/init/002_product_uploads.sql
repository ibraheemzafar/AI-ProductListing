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

