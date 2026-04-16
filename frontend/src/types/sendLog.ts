export interface SendLog {
  id: number;
  campaign_id: number;
  contact_id: number;
  contact_email: string | null;
  mailbox_id: number | null;
  mailbox_email: string | null;
  subject_used: string;
  body_preview: string | null;
  status: string;
  error_message: string | null;
  error_label: string | null;
  sent_at: string;
}
