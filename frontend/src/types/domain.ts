export interface Domain {
  id: number;
  name: string;
  hourly_limit: number;
  daily_limit: number;
  sent_this_hour: number;
  sent_today: number;
  is_active: boolean;
  created_at: string;
  mailboxes: Mailbox[];
}

export interface Mailbox {
  id: number;
  domain_id: number;
  email: string;
  smtp_host: string;
  smtp_port: number;
  login: string;
  use_tls: boolean;
  hourly_limit: number;
  daily_limit: number;
  sent_this_hour: number;
  sent_today: number;
  is_active: boolean;
  created_at: string;
}

export interface DomainCreate {
  name: string;
  hourly_limit?: number;
  daily_limit?: number;
}

export interface MailboxCreate {
  email: string;
  smtp_host: string;
  smtp_port?: number;
  login: string;
  password: string;
  use_tls?: boolean;
  hourly_limit?: number;
  daily_limit?: number;
}

export interface MailboxTestResult {
  success: boolean;
  message: string;
}
