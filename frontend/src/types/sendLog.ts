export interface SendLog {
  id: number;
  campaign_id: number;
  contact_id: number;
  mailbox_id: number | null;
  subject_used: string;
  body_preview: string | null;
  status: string;
  error_message: string | null;
  sent_at: string;
}
