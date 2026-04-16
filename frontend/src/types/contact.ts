export interface Contact {
  id: number;
  campaign_id: number;
  email: string;
  is_valid: boolean | null;
  validation_error: string | null;
  validation_error_label: string | null;
  status: string;
  created_at: string;
}

export interface ContactUploadResponse {
  total: number;
  parsed: number;
  duplicates: number;
}

export interface ValidationProgress {
  total: number;
  checked: number;
  valid: number;
  invalid: number;
  progress_percent: number;
}
