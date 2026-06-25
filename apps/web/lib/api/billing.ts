import { getPublicEnv } from '@/lib/env';

export interface Wallet {
  id: string;
  userId: string;
  totalCredits: number;
  availableCredits: number;
}

export interface Plan {
  id: string;
  code: string;
  name: string;
  description: string | null;
  planType: string;
  creditAllowance: number;
  priceCents: number;
  currency: string;
  interval: string;
  rollover: boolean;
}

export interface Subscription {
  id: string;
  status: string;
  plan: Plan;
  currentPeriodEnd: string | null;
  cancelAtPeriodEnd: boolean;
}

export interface WalletTransaction {
  id: string;
  entryType: string;
  amount: number;
  balanceAfter: number;
  referenceType: string | null;
  referenceId: string | null;
  description: string | null;
  createdAt: string;
}

export interface WalletTransactionList {
  transactions: WalletTransaction[];
  total: number;
  limit: number;
  offset: number;
}

interface ApiWallet {
  id: string;
  user_id: string;
  total_credits: number;
  available_credits: number;
}

interface ApiPlan {
  id: string;
  code: string;
  name: string;
  description: string | null;
  plan_type: string;
  credit_allowance: number;
  price_cents: number;
  currency: string;
  interval: string;
  rollover: boolean;
}

interface ApiSubscription {
  id: string;
  status: string;
  plan: ApiPlan;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

interface ApiTransaction {
  id: string;
  entry_type: string;
  amount: number;
  balance_after: number;
  reference_type: string | null;
  reference_id: string | null;
  description: string | null;
  created_at: string;
}

interface ApiErrorPayload {
  error?: { message?: string };
  detail?: string;
}

function mapPlan(plan: ApiPlan): Plan {
  return {
    id: plan.id,
    code: plan.code,
    name: plan.name,
    description: plan.description,
    planType: plan.plan_type,
    creditAllowance: plan.credit_allowance,
    priceCents: plan.price_cents,
    currency: plan.currency,
    interval: plan.interval,
    rollover: plan.rollover,
  };
}

export async function getWallet(): Promise<Wallet | null> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/billing/wallet`, {
    credentials: 'include',
    cache: 'no-store',
  });
  if (!response.ok) {
    return null;
  }
  const payload = (await response.json()) as ApiWallet;
  return {
    id: payload.id,
    userId: payload.user_id,
    totalCredits: payload.total_credits,
    availableCredits: payload.available_credits,
  };
}

export async function getPlans(): Promise<Plan[]> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/billing/plans`, {
    credentials: 'include',
    cache: 'no-store',
  });
  if (!response.ok) {
    return [];
  }
  const payload = (await response.json()) as { plans: ApiPlan[] };
  return payload.plans.map(mapPlan);
}

export async function getSubscription(): Promise<Subscription | null> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/billing/subscription`, {
    credentials: 'include',
    cache: 'no-store',
  });
  if (!response.ok) {
    return null;
  }
  const payload = (await response.json()) as ApiSubscription | null;
  if (!payload) {
    return null;
  }
  return {
    id: payload.id,
    status: payload.status,
    plan: mapPlan(payload.plan),
    currentPeriodEnd: payload.current_period_end,
    cancelAtPeriodEnd: payload.cancel_at_period_end,
  };
}

export async function getTransactions(limit = 20, offset = 0): Promise<WalletTransactionList> {
  const url = new URL(`${getPublicEnv().apiBaseUrl}/billing/transactions`);
  url.searchParams.set('limit', String(limit));
  url.searchParams.set('offset', String(offset));
  const response = await fetch(url, { credentials: 'include', cache: 'no-store' });
  if (!response.ok) {
    return { transactions: [], total: 0, limit, offset };
  }
  const payload = (await response.json()) as {
    transactions: ApiTransaction[];
    total: number;
    limit: number;
    offset: number;
  };
  return {
    transactions: payload.transactions.map((item) => ({
      id: item.id,
      entryType: item.entry_type,
      amount: item.amount,
      balanceAfter: item.balance_after,
      referenceType: item.reference_type,
      referenceId: item.reference_id,
      description: item.description,
      createdAt: item.created_at,
    })),
    total: payload.total,
    limit: payload.limit,
    offset: payload.offset,
  };
}

async function readError(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}

export async function createCheckoutSession(planCode: string): Promise<string> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/billing/checkout-sessions`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ plan_code: planCode }),
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Could not start checkout. Please try again.'));
  }
  const payload = (await response.json()) as { url: string };
  return payload.url;
}

export async function createPortalSession(): Promise<string> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/billing/portal-sessions`, {
    method: 'POST',
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error(await readError(response, 'Could not open the billing portal.'));
  }
  const payload = (await response.json()) as { url: string };
  return payload.url;
}

/** Dispatched after credit-spending or purchase actions so the header chip refreshes. */
export const WALLET_REFRESH_EVENT = 'wallet:refresh';

export function notifyWalletChanged(): void {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event(WALLET_REFRESH_EVENT));
  }
}
