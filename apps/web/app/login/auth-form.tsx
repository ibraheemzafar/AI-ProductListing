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
      <div className="grid grid-cols-2 rounded-md border border-border p-1">
        <button
          className={`rounded px-3 py-2 text-sm font-medium ${
            mode === 'login' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
          }`}
          type="button"
          onClick={() => setMode('login')}
        >
          Sign in
        </button>
        <button
          className={`rounded px-3 py-2 text-sm font-medium ${
            mode === 'register' ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'
          }`}
          type="button"
          onClick={() => setMode('register')}
        >
          Register
        </button>
      </div>

      {mode === 'register' ? (
        <label className="flex flex-col gap-2 text-sm font-medium">
          Name
          <input
            className="h-10 rounded-md border border-border px-3 text-sm font-normal outline-none focus:ring-2 focus:ring-primary"
            name="name"
            placeholder="Your name"
            type="text"
          />
        </label>
      ) : null}

      <label className="flex flex-col gap-2 text-sm font-medium">
        Email
        <input
          className="h-10 rounded-md border border-border px-3 text-sm font-normal outline-none focus:ring-2 focus:ring-primary"
          name="email"
          placeholder="you@example.com"
          required
          type="email"
        />
      </label>

      <label className="flex flex-col gap-2 text-sm font-medium">
        Password
        <input
          className="h-10 rounded-md border border-border px-3 text-sm font-normal outline-none focus:ring-2 focus:ring-primary"
          minLength={mode === 'register' ? 8 : 1}
          name="password"
          placeholder={mode === 'register' ? 'At least 8 characters' : 'Your password'}
          required
          type="password"
        />
      </label>

      {errorMessage ? <p className="text-sm text-red-600">{errorMessage}</p> : null}

      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Please wait' : mode === 'login' ? 'Sign in' : 'Create account'}
      </Button>
    </form>
  );
}
