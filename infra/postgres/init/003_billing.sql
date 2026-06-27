-- Billing, wallet & subscriptions schema.
-- Applied after 002_product_uploads.sql. IDs are VARCHAR(36) UUIDs generated in Python,
-- matching the existing convention. The wallet_transactions ledger is the source of truth
-- for credit balances; wallets.available_credits is a maintained cache.

-- Admin-defined subscription plans and one-time top-up packs (mirrored to payment providers).
CREATE TABLE IF NOT EXISTS subscription_plans (
  id                VARCHAR(36) PRIMARY KEY,
  code              VARCHAR(50) NOT NULL UNIQUE,
  name              VARCHAR(255) NOT NULL,
  description       TEXT,
  plan_type         VARCHAR(20) NOT NULL DEFAULT 'subscription', -- 'subscription' | 'topup'
  credit_allowance  BIGINT NOT NULL,
  price_cents       INTEGER NOT NULL,
  currency          VARCHAR(10) NOT NULL DEFAULT 'usd',
  interval          VARCHAR(20) NOT NULL DEFAULT 'month',        -- 'month' | 'year' | 'one_time'
  rollover          BOOLEAN NOT NULL DEFAULT FALSE,              -- capped rollover when TRUE
  stripe_product_id VARCHAR(255),
  stripe_price_id   VARCHAR(255),
  paddle_product_id VARCHAR(255),
  paddle_price_id   VARCHAR(255),
  is_active         BOOLEAN NOT NULL DEFAULT TRUE,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (credit_allowance >= 0),
  CHECK (price_cents >= 0)
);

CREATE INDEX IF NOT EXISTS ix_subscription_plans_active ON subscription_plans (is_active);

-- Catalog of enabled payment providers (the "payment methods from DB").
CREATE TABLE IF NOT EXISTS payment_providers (
  code         VARCHAR(50) PRIMARY KEY,            -- 'stripe' | 'paddle'
  display_name VARCHAR(255) NOT NULL,
  is_active    BOOLEAN NOT NULL DEFAULT TRUE,
  config       JSONB NOT NULL DEFAULT '{}',        -- non-secret config only
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- One wallet per user. available_credits is a cache of the ledger sum.
CREATE TABLE IF NOT EXISTS wallets (
  id                VARCHAR(36) PRIMARY KEY,
  user_id           VARCHAR(36) NOT NULL UNIQUE REFERENCES users(id),
  total_credits     BIGINT NOT NULL DEFAULT 0,     -- lifetime granted
  available_credits BIGINT NOT NULL DEFAULT 0,     -- spendable now
  version           BIGINT NOT NULL DEFAULT 0,     -- optimistic lock
  created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (available_credits >= 0)
);

CREATE INDEX IF NOT EXISTS ix_wallets_user_id ON wallets (user_id);

-- Append-only ledger: the single source of truth for every balance change.
CREATE TABLE IF NOT EXISTS wallet_transactions (
  id             VARCHAR(36) PRIMARY KEY,
  wallet_id      VARCHAR(36) NOT NULL REFERENCES wallets(id),
  user_id        VARCHAR(36) NOT NULL REFERENCES users(id),
  entry_type     VARCHAR(40) NOT NULL,  -- signup_bonus|subscription_grant|topup|ai_debit|refund|adjustment
  amount         BIGINT NOT NULL,       -- signed: + credit, - debit
  balance_after  BIGINT NOT NULL,
  reference_type VARCHAR(50),           -- 'ai_request_log'|'stripe_invoice'|'user'|...
  reference_id   VARCHAR(255),
  description    TEXT,
  entry_metadata JSONB NOT NULL DEFAULT '{}',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  -- Idempotency: a given external event posts a given entry type at most once.
  UNIQUE (reference_type, reference_id, entry_type)
);

CREATE INDEX IF NOT EXISTS ix_wallet_transactions_wallet_id
  ON wallet_transactions (wallet_id);
CREATE INDEX IF NOT EXISTS ix_wallet_transactions_user_created_at
  ON wallet_transactions (user_id, created_at DESC);

-- Links a user to their payment provider customers.
CREATE TABLE IF NOT EXISTS billing_customers (
  user_id            VARCHAR(36) PRIMARY KEY REFERENCES users(id),
  stripe_customer_id VARCHAR(255) UNIQUE,
  paddle_customer_id VARCHAR(255) UNIQUE,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- A user's subscription, synced from the active payment provider.
CREATE TABLE IF NOT EXISTS user_subscriptions (
  id                     VARCHAR(36) PRIMARY KEY,
  user_id                VARCHAR(36) NOT NULL REFERENCES users(id),
  plan_id                VARCHAR(36) NOT NULL REFERENCES subscription_plans(id),
  stripe_customer_id     VARCHAR(255),
  stripe_subscription_id VARCHAR(255) UNIQUE,
  paddle_customer_id     VARCHAR(255),
  paddle_subscription_id VARCHAR(255) UNIQUE,
  status                 VARCHAR(40) NOT NULL,  -- active|past_due|canceled|incomplete|...
  current_period_start   TIMESTAMPTZ,
  current_period_end     TIMESTAMPTZ,
  cancel_at_period_end   BOOLEAN NOT NULL DEFAULT FALSE,
  created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_user_subscriptions_user_id ON user_subscriptions (user_id);

-- Display-only saved payment method references (no card data).
CREATE TABLE IF NOT EXISTS user_payment_methods (
  id                       VARCHAR(36) PRIMARY KEY,
  user_id                  VARCHAR(36) NOT NULL REFERENCES users(id),
  provider_code            VARCHAR(50) NOT NULL REFERENCES payment_providers(code),
  stripe_payment_method_id VARCHAR(255),
  paddle_payment_method_id VARCHAR(255),
  brand                    VARCHAR(50),
  last4                    VARCHAR(4),
  exp_month                INTEGER,
  exp_year                 INTEGER,
  is_default               BOOLEAN NOT NULL DEFAULT FALSE,
  created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_user_payment_methods_user_id ON user_payment_methods (user_id);

-- Webhook idempotency / out-of-order protection.
CREATE TABLE IF NOT EXISTS processed_webhook_events (
  id           VARCHAR(255) PRIMARY KEY,   -- provider event id, e.g. 'evt_...'
  provider     VARCHAR(50) NOT NULL,
  event_type   VARCHAR(100) NOT NULL,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Link an AI request to the ledger debit it produced (ledger stays authoritative).
ALTER TABLE ai_request_logs
  ADD COLUMN IF NOT EXISTS credits_charged BIGINT;
ALTER TABLE ai_request_logs
  ADD COLUMN IF NOT EXISTS wallet_transaction_id VARCHAR(36) REFERENCES wallet_transactions(id);

-- Compatibility upgrades for existing local databases.
ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS paddle_product_id VARCHAR(255);
ALTER TABLE subscription_plans
  ADD COLUMN IF NOT EXISTS paddle_price_id VARCHAR(255);

ALTER TABLE billing_customers
  ALTER COLUMN stripe_customer_id DROP NOT NULL;
ALTER TABLE billing_customers
  ADD COLUMN IF NOT EXISTS paddle_customer_id VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS ux_billing_customers_paddle_customer_id
  ON billing_customers (paddle_customer_id)
  WHERE paddle_customer_id IS NOT NULL;

ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS paddle_customer_id VARCHAR(255);
ALTER TABLE user_subscriptions
  ADD COLUMN IF NOT EXISTS paddle_subscription_id VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS ux_user_subscriptions_paddle_subscription_id
  ON user_subscriptions (paddle_subscription_id)
  WHERE paddle_subscription_id IS NOT NULL;

ALTER TABLE user_payment_methods
  ADD COLUMN IF NOT EXISTS paddle_payment_method_id VARCHAR(255);

-- Seed the default payment providers and example plans. Provider product/price ids are
-- filled in once products are created in Stripe/Paddle. Safe to re-run.
INSERT INTO payment_providers (code, display_name, is_active)
VALUES ('stripe', 'Stripe', TRUE)
ON CONFLICT (code) DO NOTHING;

INSERT INTO payment_providers (code, display_name, is_active)
VALUES ('paddle', 'Paddle', TRUE)
ON CONFLICT (code) DO NOTHING;

INSERT INTO subscription_plans
  (id, code, name, description, plan_type, credit_allowance, price_cents, currency, interval, rollover)
VALUES
  ('00000000-0000-0000-0000-0000000000a1', 'starter', 'Starter',
   '1,000 credits per month.', 'subscription', 1000, 999, 'usd', 'month', FALSE),
  ('00000000-0000-0000-0000-0000000000a2', 'pro', 'Pro',
   '5,000 credits per month with capped rollover.', 'subscription', 5000, 2999, 'usd', 'month', TRUE),
  ('00000000-0000-0000-0000-0000000000b1', 'topup_small', 'Top-up 500',
   'One-time 500 credit top-up.', 'topup', 500, 499, 'usd', 'one_time', FALSE)
ON CONFLICT (code) DO NOTHING;
