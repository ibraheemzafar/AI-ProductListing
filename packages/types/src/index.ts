export interface ApiError {
  code: string;
  message: string;
}

export interface ApiResponse<TData> {
  data: TData;
  error: ApiError | null;
}

export interface GeneratedListingDraft {
  title: string;
  shortDescription: string;
  seoKeywords: string[];
}

