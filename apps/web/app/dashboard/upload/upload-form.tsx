'use client';

import { ImagePlus, Upload, X } from 'lucide-react';
import { ChangeEvent, DragEvent, useEffect, useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import { getPublicEnv } from '@/lib/env';

const maxFileSizeBytes = 10 * 1024 * 1024;
const allowedTypes = new Set(['image/jpeg', 'image/png', 'image/webp']);

interface UploadPreview {
  id: string;
  file: File;
  previewUrl: string;
}

interface UploadFormProps {
  onUploadComplete: () => void;
}

export function UploadForm({ onUploadComplete }: UploadFormProps) {
  const [previews, setPreviews] = useState<UploadPreview[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const hasFiles = previews.length > 0;

  useEffect(() => {
    return () => {
      previews.forEach((preview) => URL.revokeObjectURL(preview.previewUrl));
    };
  }, [previews]);

  const totalSizeLabel = useMemo(() => {
    const totalSize = previews.reduce((sum, preview) => sum + preview.file.size, 0);
    return `${(totalSize / 1024 / 1024).toFixed(2)} MB`;
  }, [previews]);

  function handleFileInputChange(event: ChangeEvent<HTMLInputElement>) {
    addFiles(Array.from(event.target.files ?? []));
    event.target.value = '';
  }

  function handleDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    event.currentTarget.dataset.dragging = 'false';
    addFiles(Array.from(event.dataTransfer.files));
  }

  function addFiles(files: File[]) {
    setErrorMessage(null);
    const invalidFile = files.find(
      (file) => !allowedTypes.has(file.type) || file.size > maxFileSizeBytes,
    );

    if (invalidFile) {
      setErrorMessage('Only JPG, PNG, and WEBP images up to 10MB are supported.');
      return;
    }

    setPreviews((currentPreviews) => [
      ...currentPreviews,
      ...files.map((file) => ({
        id: `${file.name}-${file.lastModified}-${crypto.randomUUID()}`,
        file,
        previewUrl: URL.createObjectURL(file),
      })),
    ]);
  }

  function clearFiles() {
    previews.forEach((preview) => URL.revokeObjectURL(preview.previewUrl));
    setPreviews([]);
    setProgress(0);
  }

  async function uploadFiles() {
    if (!hasFiles) {
      setErrorMessage('Choose at least one image to upload.');
      return;
    }

    setIsUploading(true);
    setErrorMessage(null);
    setProgress(0);

    const formData = new FormData();
    previews.forEach((preview) => formData.append('files', preview.file));

    const request = new XMLHttpRequest();
    request.open('POST', `${getPublicEnv().apiBaseUrl}/products/images`);
    request.withCredentials = true;
    request.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        setProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    request.onload = () => {
      setIsUploading(false);
      if (request.status >= 200 && request.status < 300) {
        clearFiles();
        onUploadComplete();
        return;
      }
      setErrorMessage(readUploadError(request.responseText));
    };
    request.onerror = () => {
      setIsUploading(false);
      setErrorMessage('Upload failed. Check that the API server is running.');
    };
    request.send(formData);
  }

  return (
    <div className="flex flex-col gap-5">
      <label
        className="group flex min-h-60 cursor-pointer flex-col items-center justify-center gap-4 rounded-lg border border-dashed border-primary/35 bg-primary/[0.06] px-6 py-10 text-center transition hover:-translate-y-0.5 hover:border-primary/70 hover:bg-primary/[0.09] data-[dragging=true]:scale-[1.01] data-[dragging=true]:border-accent data-[dragging=true]:bg-accent/10"
        onDragEnter={(event) => {
          event.currentTarget.dataset.dragging = 'true';
        }}
        onDragLeave={(event) => {
          event.currentTarget.dataset.dragging = 'false';
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        <span className="flex size-14 items-center justify-center rounded-lg bg-primary/15 text-primary transition group-hover:scale-105">
          <ImagePlus className="size-7" aria-hidden="true" />
        </span>
        <span className="text-base font-semibold text-white">Drop images here or browse</span>
        <span className="max-w-sm text-sm leading-6 text-muted-foreground">
          JPG, PNG, and WEBP images up to 10MB each. Select multiple product angles for better AI
          context.
        </span>
        <input
          className="sr-only"
          multiple
          accept="image/jpeg,image/png,image/webp"
          type="file"
          onChange={handleFileInputChange}
        />
      </label>

      {hasFiles ? (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between rounded-md border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-muted-foreground">
            <span>{previews.length} selected</span>
            <span>{totalSizeLabel}</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {previews.map((preview) => (
              <div
                key={preview.id}
                className="group overflow-hidden rounded-lg border border-white/10 bg-secondary/70"
              >
                <img
                  alt={preview.file.name}
                  className="aspect-square w-full object-cover transition duration-500 group-hover:scale-105"
                  src={preview.previewUrl}
                />
                <div className="truncate px-3 py-2 text-xs text-muted-foreground">
                  {preview.file.name}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {isUploading ? (
        <div className="rounded-md border border-white/10 bg-white/[0.04] p-3">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Uploading assets</span>
            <span>{progress}%</span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded bg-muted">
            <div
              className="h-full bg-gradient-to-r from-primary to-accent transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      ) : null}

      {errorMessage ? (
        <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-100">
          {errorMessage}
        </p>
      ) : null}

      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={uploadFiles} disabled={isUploading || !hasFiles}>
          <Upload className="mr-2 size-4" aria-hidden="true" />
          {isUploading ? `Uploading ${progress}%` : 'Upload images'}
        </Button>
        <Button type="button" variant="secondary" onClick={clearFiles} disabled={isUploading}>
          <X className="size-4" aria-hidden="true" />
          Clear
        </Button>
      </div>
    </div>
  );
}

function readUploadError(responseText: string) {
  try {
    const payload = JSON.parse(responseText) as { error?: { message?: string }; detail?: string };
    return payload.error?.message ?? payload.detail ?? 'Upload failed. Please try again.';
  } catch {
    return 'Upload failed. Please try again.';
  }
}
