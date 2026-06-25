'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { FormEvent, useState } from 'react';

import { Button } from '@/components/ui/button';
import { getPublicEnv } from '@/lib/env';

type AuthMode = 'login' | 'register';

interface ApiValidationError {
  detail?: Array<{
    msg?: string;
  }>;
}

function validateRegistrationPassword(password: string, confirmPassword: string): string | null {
  if (password.length < 8) {
    return 'Password must be at least 8 characters.';
  }
  if (!/[a-zA-Z]/.test(password) || !/[0-9]/.test(password)) {
    return 'Password must contain at least one letter and one number.';
  }
  if (password !== confirmPassword) {
    return 'Passwords do not match.';
  }
  return null;
}

export function AuthForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [mode, setMode] = useState<AuthMode>('login');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    const formData = new FormData(event.currentTarget);
    const email = String(formData.get('email') ?? '').trim();
    const password = String(formData.get('password') ?? '');
    const confirmPassword = String(formData.get('confirm_password') ?? '');
    const name = String(formData.get('name') ?? '').trim();

    if (mode === 'register') {
      const passwordError = validateRegistrationPassword(password, confirmPassword);
      if (passwordError) {
        setIsSubmitting(false);
        setErrorMessage(passwordError);
        return;
      }
    }

    const response = await fetch(`${getPublicEnv().apiBaseUrl}/auth/${mode}`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        ...(mode === 'register'
          ? { name: name || null, confirm_password: confirmPassword }
          : {}),
      }),
    });

    setIsSubmitting(false);

    if (!response.ok) {
      if (response.status === 422) {
        const validationError = (await response.json()) as ApiValidationError;
        const validationMessage = validationError.detail?.[0]?.msg;
        setErrorMessage(validationMessage ?? 'Check your email and password, then try again.');
        return;
      }

      setErrorMessage(
        mode === 'login'
          ? 'Invalid email or password.'
          : 'Could not create an account with these details.',
      );
      return;
    }

    const destination = searchParams.get('next') || '/dashboard';
    if (mode === 'register') {
      const data = (await response.json().catch(() => null)) as {
        granted_bonus_credits?: number | null;
      } | null;
      const bonus = data?.granted_bonus_credits;
      if (bonus) {
        const url = new URL(destination, window.location.origin);
        url.searchParams.set('welcome_credits', String(bonus));
        router.replace(url.pathname + url.search);
        router.refresh();
        return;
      }
    }

    router.replace(destination);
    router.refresh();
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
      <div className="grid grid-cols-2 rounded-md border border-white/10 bg-background/55 p-1">
        <button
          className={`rounded px-3 py-2 text-sm font-semibold transition ${
            mode === 'login'
              ? 'bg-primary text-primary-foreground shadow-[0_12px_36px_-18px_hsl(var(--primary))]'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          type="button"
          onClick={() => setMode('login')}
        >
          Sign in
        </button>
        <button
          className={`rounded px-3 py-2 text-sm font-semibold transition ${
            mode === 'register'
              ? 'bg-primary text-primary-foreground shadow-[0_12px_36px_-18px_hsl(var(--primary))]'
              : 'text-muted-foreground hover:text-foreground'
          }`}
          type="button"
          onClick={() => setMode('register')}
        >
          Register
        </button>
      </div>

      {mode === 'register' ? (
        <label className="flex flex-col gap-2 text-sm font-medium text-white">
          Name
          <input
            className="field-surface h-11 font-normal"
            name="name"
            placeholder="Your name"
            type="text"
          />
        </label>
      ) : null}

      <label className="flex flex-col gap-2 text-sm font-medium text-white">
        Email
        <input
          className="field-surface h-11 font-normal"
          name="email"
          placeholder="you@example.com"
          required
          type="email"
        />
      </label>

      <label className="flex flex-col gap-2 text-sm font-medium text-white">
        Password
        <input
          className="field-surface h-11 font-normal"
          minLength={mode === 'register' ? 8 : 1}
          name="password"
          placeholder={mode === 'register' ? 'At least 8 characters' : 'Your password'}
          required
          type="password"
        />
      </label>

      {mode === 'register' ? (
        <label className="flex flex-col gap-2 text-sm font-medium text-white">
          Confirm password
          <input
            className="field-surface h-11 font-normal"
            minLength={8}
            name="confirm_password"
            placeholder="Re-enter your password"
            required
            type="password"
          />
        </label>
      ) : null}

      {errorMessage ? (
        <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
          {errorMessage}
        </p>
      ) : null}

      <Button className="mt-2 h-11" type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Please wait' : mode === 'login' ? 'Sign in' : 'Create account'}
      </Button>
    </form>
  );
}
