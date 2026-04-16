export type CampaignStatus =
  | "draft"
  | "validating"
  | "generating"
  | "ready"
  | "running"
  | "paused"
  | "completed"
  | "failed";

export interface Campaign {
  id: number;
  name: string;
  original_subject: string;
  original_body: string;
  total_contacts: number;
  valid_contacts: number;
  sent_count: number;
  failed_count: number;
  status: CampaignStatus;
  rotate_every_n: number;
  delay_min_sec: number;
  delay_max_sec: number;
  skip_validation: boolean;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface CampaignCreate {
  name: string;
  original_subject: string;
  original_body: string;
  rotate_every_n?: number;
  delay_min_sec?: number;
  delay_max_sec?: number;
  skip_validation?: boolean;
}

export interface CampaignStats {
  total_contacts: number;
  valid_contacts: number;
  sent_count: number;
  failed_count: number;
  invalid_count: number;
  remaining: number;
  progress_percent: number;
  elapsed_seconds: number | null;
  eta_seconds: number | null;
}

export interface ValidationBreakdown {
  syntax_errors: number;
  no_mx: number;
  smtp_rejected: number;
  disposable: number;
  other: number;
}

export interface CampaignReport {
  total_contacts: number;
  valid_contacts: number;
  invalid_contacts: number;
  sent_count: number;
  failed_count: number;
  pending_count: number;
  validation_breakdown: ValidationBreakdown;
}
