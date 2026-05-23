'use client';

import { ImagePlus, Upload } from 'lucide-react';
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
        className="flex min-h-48 cursor-pointer flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border px-6 py-8 text-center transition-colors hover:bg-muted"
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        <ImagePlus className="size-8 text-primary" aria-hidden="true" />
        <span className="text-sm font-medium">Drop images here or browse</span>
        <span className="text-xs text-muted-foreground">JPG, PNG, WEBP up to 10MB each</span>
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
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>{previews.length} selected</span>
            <span>{totalSizeLabel}</span>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {previews.map((preview) => (
              <div key={preview.id} className="overflow-hidden rounded-md border border-border">
                <img
                  alt={preview.file.name}
                  className="aspect-square w-full object-cover"
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
        <div className="h-2 overflow-hidden rounded bg-muted">
          <div className="h-full bg-primary transition-all" style={{ width: `${progress}%` }} />
        </div>
      ) : null}

      {errorMessage ? <p className="text-sm text-red-600">{errorMessage}</p> : null}

      <div className="flex flex-wrap gap-3">
        <Button type="button" onClick={uploadFiles} disabled={isUploading || !hasFiles}>
          <Upload className="mr-2 size-4" aria-hidden="true" />
          {isUploading ? `Uploading ${progress}%` : 'Upload images'}
        </Button>
        <Button type="button" variant="secondary" onClick={clearFiles} disabled={isUploading}>
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

