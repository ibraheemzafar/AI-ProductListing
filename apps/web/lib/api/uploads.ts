import { cookies } from 'next/headers';

import type { ProductImageList, UploadedProductImage } from '@ai-product-listing/types';
import { getServerEnv } from '@/lib/env';

interface ApiUploadedImage {
  id: string;
  product_id: string;
  original_filename: string;
  image_url: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

interface ApiProductImageList {
  images: ApiUploadedImage[];
}

export async function getUploadedImages(): Promise<ProductImageList> {
  const cookieStore = await cookies();
  const response = await fetch(`${getServerEnv().apiBaseUrl}/products/images`, {
    cache: 'no-store',
    headers: {
      Cookie: cookieStore.toString(),
    },
  });

  if (!response.ok) {
    return { images: [] };
  }

  const payload = (await response.json()) as ApiProductImageList;
  return {
    images: payload.images.map(mapUploadedImage),
  };
}

function mapUploadedImage(image: ApiUploadedImage): UploadedProductImage {
  return {
    id: image.id,
    productId: image.product_id,
    originalFilename: image.original_filename,
    imageUrl: image.image_url,
    contentType: image.content_type,
    sizeBytes: image.size_bytes,
    createdAt: image.created_at,
  };
}

