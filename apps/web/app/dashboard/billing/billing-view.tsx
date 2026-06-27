'use client';

import { Coins, ExternalLink, RefreshCw } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  createCheckoutSession,
  createPortalSession,
  getPlans,
  getSubscription,
  getTransactions,
  getWallet,
  type Plan,
  type Subscription,
  type Wallet,
  type WalletTransaction,
} from '@/lib/api/billing';

function formatPrice(cents: number, currency: string): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase(),
  }).format(cents / 100);
}

export function BillingView() {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [pendingCode, setPendingCode] = useState<string | null>(null);
  const [portalPending, setPortalPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [walletData, planData, subscriptionData, transactionData] = await Promise.all([
      getWallet(),
      getPlans(),
      getSubscription(),
      getTransactions(10, 0),
    ]);
    setWallet(walletData);
    setPlans(planData);
    setSubscription(subscriptionData);
    setTransactions(transactionData.transactions);
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handlePurchase(code: string) {
    setPendingCode(code);
    setError(null);
    try {
      const url = await createCheckoutSession(code);
      window.location.href = url;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not start checkout.');
      setPendingCode(null);
    }
  }

  async function handleManage() {
    if (!subscription) {
      setError('Choose a subscription plan before opening the billing portal.');
      return;
    }

    setPortalPending(true);
    setError(null);
    try {
      const url = await createPortalSession();
      window.location.href = url;
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Could not open the billing portal.');
      setPortalPending(false);
    }
  }

  const subscriptionPlans = plans.filter((plan) => plan.planType === 'subscription');
  const topupPlans = plans.filter((plan) => plan.planType === 'topup');

  if (loading) {
    return (
      <div className="glass-panel flex items-center gap-3 p-6 text-sm text-muted-foreground">
        <RefreshCw className="size-4 animate-spin" aria-hidden="true" />
        Loading billing details…
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {error ? (
        <p className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
          {error}
        </p>
      ) : null}

      <section className="glass-panel flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <span className="flex size-12 items-center justify-center rounded-md bg-primary/15 text-primary">
            <Coins className="size-6" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm text-muted-foreground">Available credits</p>
            <p className="text-3xl font-semibold tabular-nums text-white">
              {(wallet?.availableCredits ?? 0).toLocaleString()}
            </p>
            {subscription ? (
              <p className="mt-1 text-xs text-muted-foreground">
                {subscription.plan.name} · {subscription.status}
                {subscription.cancelAtPeriodEnd ? ' · cancels at period end' : ''}
              </p>
            ) : (
              <p className="mt-1 text-xs text-muted-foreground">No active subscription</p>
            )}
          </div>
        </div>
        <Button
          type="button"
          variant="secondary"
          onClick={handleManage}
          disabled={portalPending || !subscription}
        >
          <ExternalLink className="mr-2 size-4" aria-hidden="true" />
          {portalPending ? 'Opening…' : 'Manage billing'}
        </Button>
      </section>

      <section>
        <h2 className="text-lg font-semibold text-white">Subscription plans</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Recurring credits each billing cycle.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {subscriptionPlans.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              cta={subscription?.plan.code === plan.code ? 'Current plan' : 'Subscribe'}
              disabled={pendingCode !== null || subscription?.plan.code === plan.code}
              pending={pendingCode === plan.code}
              onSelect={() => handlePurchase(plan.code)}
            />
          ))}
        </div>
      </section>

      {topupPlans.length > 0 ? (
        <section>
          <h2 className="text-lg font-semibold text-white">One-time top-ups</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Add credits without changing your subscription.
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {topupPlans.map((plan) => (
              <PlanCard
                key={plan.id}
                plan={plan}
                cta="Buy credits"
                disabled={pendingCode !== null}
                pending={pendingCode === plan.code}
                onSelect={() => handlePurchase(plan.code)}
              />
            ))}
          </div>
        </section>
      ) : null}

      <section className="glass-panel p-6">
        <h2 className="text-lg font-semibold text-white">Recent credit activity</h2>
        {transactions.length === 0 ? (
          <p className="mt-3 text-sm text-muted-foreground">No credit activity yet.</p>
        ) : (
          <div className="mt-4 grid gap-2">
            {transactions.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-background/45 px-3 py-2 text-sm"
              >
                <div className="min-w-0">
                  <p className="truncate font-medium text-white">
                    {item.description ?? item.entryType}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(item.createdAt).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`shrink-0 tabular-nums font-semibold ${
                    item.amount >= 0 ? 'text-emerald-300' : 'text-red-200'
                  }`}
                >
                  {item.amount >= 0 ? '+' : ''}
                  {item.amount.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

interface PlanCardProps {
  plan: Plan;
  cta: string;
  disabled: boolean;
  pending: boolean;
  onSelect: () => void;
}

function PlanCard({ plan, cta, disabled, pending, onSelect }: PlanCardProps) {
  return (
    <div className="premium-card flex flex-col gap-4 p-5">
      <div>
        <p className="text-sm font-semibold text-white">{plan.name}</p>
        <p className="mt-1 text-2xl font-semibold text-white">
          {formatPrice(plan.priceCents, plan.currency)}
          {plan.planType === 'subscription' ? (
            <span className="text-sm font-normal text-muted-foreground">/{plan.interval}</span>
          ) : null}
        </p>
      </div>
      <p className="text-sm text-muted-foreground">
        {plan.creditAllowance.toLocaleString()} credits
        {plan.planType === 'subscription'
          ? plan.rollover
            ? ' · capped rollover'
            : ' · resets each cycle'
          : ''}
      </p>
      {plan.description ? (
        <p className="text-xs leading-5 text-muted-foreground">{plan.description}</p>
      ) : null}
      <Button className="mt-auto" type="button" onClick={onSelect} disabled={disabled}>
        {pending ? 'Redirecting…' : cta}
      </Button>
    </div>
  );
}
