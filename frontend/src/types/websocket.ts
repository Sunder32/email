export interface WsProgressMessage {
  type: "progress";
  data: {
    sent: number;
    failed: number;
    total: number;
    current_mailbox: string;
    current_domain: string;
    last_contact: string;
    last_subject: string;
    last_status: string;
  };
}

export interface WsStatusMessage {
  type: "status";
  data: {
    status: string;
    reason?: string;
  };
}

export type WsMessage = WsProgressMessage | WsStatusMessage;
