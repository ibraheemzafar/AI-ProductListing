import { getPublicEnv } from '@/lib/env';

interface ApiErrorPayload {
  error?: {
    message?: string;
  };
  detail?: string;
}

export async function deleteListing(listingId: string): Promise<void> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/listings/${listingId}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, 'Could not delete listing. Please try again.'));
  }
}

export async function deleteUploadedImage(imageId: string): Promise<void> {
  const response = await fetch(`${getPublicEnv().apiBaseUrl}/product-images/${imageId}`, {
    method: 'DELETE',
    credentials: 'include',
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, 'Could not delete image. Please try again.'));
  }
}

async function readErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const payload = (await response.json()) as ApiErrorPayload;
    return payload.error?.message ?? payload.detail ?? fallback;
  } catch {
    return fallback;
  }
}
