# Billing, Wallet & Subscriptions Architecture

Status: **in progress** (Phase 1 + Phase 3 landed; metering, subscriptions, Stripe, webhooks, frontend pending).

This document is the spec for the token-metered billing system: subscription plans,
a credit wallet, OpenAI request metering, Stripe payments, and a signup reward.
It follows the repo's feature-sliced clean architecture and the no-Alembic SQL convention
(`infra/postgres/init/*.sql`, applied in order).

## 1. Core mental model — two different "tokens"

| Concept | What it is | Where it lives |
| --- | --- | --- |
| **OpenAI tokens** | Real usage reported by OpenAI (`input_tokens`, `output_tokens`) | `ai_request_logs` (already exists) |
| **Credits** (internal "tokens") | The currency a user buys via a plan / top-up and spends per request | `wallets` + `wallet_transactions` |

A **pricing policy** converts an OpenAI request into a credit debit. Keeping the two separate
lets us change OpenAI models, add margin, or swap providers without touching the wallet.
The UI may still call credits "tokens".

### Confirmed product decisions
1. **Recurring subscriptions grant credits each billing cycle**, plus one-time **top-up packs**.
2. **Credits are an abstract currency** debited via a configurable pricing policy
   (default: `credits = ceil((input+output) * margin)`, floored at a per-workflow minimum).
3. **Rollover is configurable per plan.** `subscription_plans.rollover = TRUE` enables
   **capped rollover**: at renewal, unused credits roll over but the resulting balance is
   capped at `ROLLOVER_CAP_MULTIPLIER * plan.credit_allowance`. `rollover = FALSE` resets
   the balance to the plan allowance each cycle. The cap multiplier lives in **constants**.
4. **"Payment methods from DB"** = a catalog of enabled providers (`payment_providers`),
   Stripe first. Card data is **not** stored — management is offloaded to the Stripe Billing
   Portal (keeps us out of PCI scope). `user_payment_methods` stores display-only references.
5. **When the balance hits zero**, the user has two paths: **top up** with a one-time credit
   pack, or **upgrade/subscribe** to a plan. New AI requests are hard-blocked with `402`.

## 2. Feature slices (SOLID)

```
app/features/
  wallet/            # balance + append-only ledger (source of truth for credits)
  subscriptions/     # plans catalog + a user's subscription lifecycle
  payments/          # provider-agnostic checkout + webhook ingestion
  billing_meter/     # cross-cutting: converts an AI request -> credit debit
app/shared/payments/ # PaymentProvider Protocol + StripePaymentProvider impl
```

- **SRP** — wallet accounting, subscription lifecycle, and gateway mechanics change for
  different reasons; they are separate services/slices.
- **OCP** — `PaymentProvider` Protocol and `CreditPricingPolicy` strategy let us add
  providers/policies without modifying callers.
- **DIP/ISP** — AI services depend on a narrow `BillingMeter` interface, not the whole
  wallet; auth depends on a narrow `WalletGranter` interface.

## 3. Database schema — `infra/postgres/init/003_billing.sql`

Matches existing conventions: `VARCHAR(36)` UUID PKs (generated in Python), `JSONB`,
`TIMESTAMPTZ DEFAULT NOW()`, `CREATE TABLE IF NOT EXISTS`.

Tables:
- `subscription_plans` — admin-defined plans & top-up packs; mirrored to Stripe.
  Columns include `plan_type` (`subscription`|`topup`), `credit_allowance`, `rollover`,
  `interval`, `stripe_product_id`, `stripe_price_id`.
- `payment_providers` — catalog of enabled providers (`stripe`).
- `wallets` — one per user; `available_credits` (spendable) + `total_credits` (lifetime),
  `version` for optimistic locking, `CHECK (available_credits >= 0)`.
- `wallet_transactions` — **append-only ledger, the single source of truth** for all balance
  changes. `entry_type` ∈ {`signup_bonus`,`subscription_grant`,`topup`,`ai_debit`,`refund`,
  `adjustment`}, signed `amount`, `balance_after`, `(reference_type, reference_id, entry_type)`
  **UNIQUE** for idempotency.
- `user_subscriptions` — maps Stripe subscription state to a user/plan.
- `billing_customers` — links a user to a `stripe_customer_id`.
- `user_payment_methods` — display-only saved card references.
- `processed_webhook_events` — webhook idempotency / out-of-order protection.

`ai_request_logs` gains `credits_charged BIGINT` and `wallet_transaction_id VARCHAR(36)` —
a back-reference from an AI request to the ledger debit. The ledger remains authoritative
(it also records credits the request log knows nothing about: purchases, bonuses, refunds).

## 4. Metering flow (critical path)

```python
class BillingMeter(Protocol):
    async def authorize(self, user_id: str, workflow: str) -> None: ...   # 402 if below minimum
    async def charge(self, user_id, workflow, usage, request_log_id) -> WalletTransaction: ...

class CreditPricingPolicy(Protocol):
    def credits_for(self, model: str, usage: TokenUsage) -> int: ...
```

Wired into **all 7 AI workflows** (`product_analysis`, `listing_generation`, `seo_evaluation`,
`listing_improvement`, `marketplace_optimization` use the token policy; `image_enhancement`,
`lifestyle_scene_generation` use the flat policy). `authorize()` runs before the provider call
(checks balance vs the per-workflow minimum, raising `402` with no spend), `charge()` after
**success** (failed calls are never charged); each charged request stores `credits_charged` +
`wallet_transaction_id` on its `ai_request_logs` row.

Implemented formula and constants (`wallet/constants.py`):
```
weighted = input_tokens*INPUT_WEIGHT(1) + output_tokens*OUTPUT_WEIGHT(4)
credits  = max(MIN_CREDITS_PER_REQUEST(5),
               ceil(weighted / TOKENS_PER_CREDIT(100) * MARGIN_MULTIPLIER(1.5)))
flat workflows: FLAT_CREDITS_PER_IMAGE(20)
```

The AI debit is **clamped** (never fails a completed request) using a `SELECT ... FOR UPDATE`
row lock so concurrent debits serialize and the balance never goes negative. The pre-check is
what blocks; for token workflows the floor is `MIN_CREDITS_PER_REQUEST` (a small settlement
overage is possible and accepted — raise the floor or adopt reserve/settle to harden). For
credit grants the wallet uses one guarded statement:

```sql
UPDATE wallets SET available_credits = available_credits - :credits, version = version + 1
 WHERE id = :wallet_id AND available_credits >= :credits
RETURNING available_credits;     -- 0 rows => InsufficientCreditsError (402)
```

The wallet update and the `wallet_transactions` insert happen in the same DB transaction.
Upgrade path for strict guarantees: a **reserve → settle** pattern (hold an estimate, post
the delta) using paired ledger entries.

## 5. Stripe integration

Provider abstraction mirrors `StorageProvider`:

```python
class PaymentProvider(Protocol):
    async def create_checkout_session(...) -> CheckoutSession: ...
    async def create_billing_portal_session(...) -> PortalSession: ...
    def verify_and_parse_webhook(self, payload: bytes, signature: str) -> WebhookEvent: ...
```

**Purchase flow:** server creates a Stripe Customer + Checkout Session (`mode=subscription`
for plans, `mode=payment` for top-ups) with `client_reference_id=user_id` and an idempotency
key → user pays on Stripe-hosted Checkout → **credits are granted by webhook, never by the
success redirect**. Subscription/payment-method management via the Billing Portal.

**Webhook endpoint** `POST /api/v1/billing/webhooks/stripe` — public, **signature-verified**,
excluded from the AI rate limiter, idempotent via `processed_webhook_events`:

| Event | Action |
| --- | --- |
| `checkout.session.completed` | Link customer/subscription; grant credits for one-time top-ups. |
| `customer.subscription.created` / `.updated` | Upsert `user_subscriptions` (Stripe = source of truth for status). |
| `invoice.paid` | Grant the plan's credits (rollover-aware); idempotent per invoice. |
| `invoice.payment_failed` | Mark `past_due`; no grant; surface banner. |
| `customer.subscription.deleted` | Mark `canceled`; stop future grants. |
| `charge.refunded` | Negative `refund` ledger entry (clawback), floored at 0. |
| `charge.dispute.created` | Flag account / optionally freeze spending. |

Cross-cutting: signature verification, idempotency keys (in + out), out-of-order tolerance
(reconcile against the subscription object, not event order), structured logging.

## 6. Rollover-aware subscription grant

On `invoice.paid` for a subscription plan:

```python
allowance = plan.credit_allowance
if plan.rollover:
    cap = ROLLOVER_CAP_MULTIPLIER * allowance          # from constants
    new_available = min(wallet.available_credits + allowance, cap)
else:
    new_available = allowance                           # reset
```

The grant posts a `subscription_grant` ledger entry keyed on the Stripe invoice id (idempotent).

## 7. Free credits on registration (Phase 3)

- **Feature flag** in `Settings`: `signup_bonus_enabled: bool = False` (enable from backend).
- **Amount in constants**: `SIGNUP_BONUS_CREDITS` in `app/features/wallet/constants.py`.
- **Hook**: `AuthService.register` grants the bonus via a narrow `WalletGranter` interface
  after the user is created. Idempotent via the ledger's UNIQUE constraint (once per user).
- **Prompt**: the register response returns `granted_bonus_credits`; the web app shows a
  toast: "🎉 You've been rewarded N free credits."

## 8. API surface (`/api/v1`)

```
GET    /billing/plans                 # active plans + top-up packs
GET    /billing/wallet                # current balance
GET    /billing/transactions          # paginated ledger
GET    /billing/subscription          # current subscription
POST   /billing/checkout-sessions     # -> Stripe Checkout URL
POST   /billing/portal-sessions       # -> Stripe Billing Portal URL
POST   /billing/webhooks/stripe       # public, signature-verified, idempotent
POST/PUT /billing/admin/plans         # admin-managed plans & providers
```

New errors (extend `AppError`): `InsufficientCreditsError` (402), `WebhookVerificationError`
(400), `PaymentProviderError` (502).

## 9. Frontend touchpoints (`apps/web`)

- Wallet balance chip in `DashboardShell`; `lib/api/billing.ts`.
- `/dashboard/billing` — plans, subscribe (Checkout), top-up, manage (Billing Portal), ledger.
- Signup bonus toast from the register response flag.
- `402` interceptor → "Out of credits" modal offering **top up** or **upgrade**.
- AI buttons disabled when balance below the workflow minimum.

## 10. Testing

Wallet concurrency (no breach below zero), webhook & grant idempotency, pricing policy math,
metering (no debit on failure; one ledger entry on success), webhook signature verification,
signup bonus (flag on/off, granted once). Stripe faked via `stripe-mock` / a fake
`PaymentProvider`, mirroring how `StorageProvider` is faked in tests.

## 11. Phased rollout

1. **Wallet + ledger** (schema, service, atomic debit). ← done
2. **Metering** into all 7 AI workflows + `402` + `credits_charged`. ← done
3. **Signup bonus** (flag + constant + toast). ← done
4. **Plans + subscriptions** schema/services (Stripe IDs). ← done
5. **Stripe Checkout + Billing Portal** (purchase path). ← done
6. **Webhooks** (lifecycle + rollover-aware grants + idempotency). ← done
7. **Frontend billing UI**. ← done

All phases complete. Each phase is independently shippable behind flags.
