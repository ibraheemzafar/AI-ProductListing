'use client';

import { useRouter } from 'next/navigation';

import type { UploadedProductImage } from '@ai-product-listing/types';
import { UploadForm } from './upload-form';

interface UploadWorkspaceProps {
  initialImages: UploadedProductImage[];
}

export function UploadWorkspace({ initialImages }: UploadWorkspaceProps) {
  const router = useRouter();

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
      <section className="rounded-md border border-border p-5">
        <h2 className="text-lg font-medium">Upload product images</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Preview images before uploading them to your product workspace.
        </p>
        <div className="mt-5">
          <UploadForm onUploadComplete={() => router.refresh()} />
        </div>
      </section>

      <section className="rounded-md border border-border p-5">
        <h2 className="text-lg font-medium">Uploaded images</h2>
        <div className="mt-5 grid gap-3">
          {initialImages.length > 0 ? (
            initialImages.map((image) => (
              <div key={image.id} className="flex gap-3 rounded-md border border-border p-2">
                <img
                  alt={image.originalFilename}
                  className="size-20 rounded object-cover"
                  src={image.imageUrl}
                />
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{image.originalFilename}</p>
                  <p className="text-xs text-muted-foreground">
                    {(image.sizeBytes / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-muted-foreground">No uploaded images yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}

