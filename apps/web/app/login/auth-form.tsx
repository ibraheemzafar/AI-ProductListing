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
    const name = String(formData.get('name') ?? '').trim();

    if (mode === 'register' && password.length < 8) {
      setIsSubmitting(false);
      setErrorMessage('Password must be at least 8 characters.');
      return;
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
        ...(mode === 'register' ? { name: name || null } : {}),
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

    router.replace(searchParams.get('next') || '/dashboard');
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
