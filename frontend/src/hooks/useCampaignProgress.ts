import { useEffect, useState } from "react";
import { useWebSocket } from "./useWebSocket";
import type { WsProgressMessage } from "@/types/websocket";

interface ProgressState {
  sent: number;
  failed: number;
  total: number;
  currentMailbox: string;
  currentDomain: string;
  lastContact: string;
  lastSubject: string;
  lastStatus: string;
  campaignStatus: string | null;
  log: Array<{
    contact: string;
    mailbox: string;
    subject: string;
    status: string;
    time: string;
  }>;
}

export function useCampaignProgress(campaignId: number | null) {
  const { lastMessage, isConnected } = useWebSocket(campaignId);
  const [progress, setProgress] = useState<ProgressState>({
    sent: 0,
    failed: 0,
    total: 0,
    currentMailbox: "",
    currentDomain: "",
    lastContact: "",
    lastSubject: "",
    lastStatus: "",
    campaignStatus: null,
    log: [],
  });

  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === "progress") {
      const d = (lastMessage as WsProgressMessage).data;
      setProgress((prev) => ({
        sent: d.sent,
        failed: d.failed,
        total: d.total,
        currentMailbox: d.current_mailbox,
        currentDomain: d.current_domain,
        lastContact: d.last_contact,
        lastSubject: d.last_subject,
        lastStatus: d.last_status,
        campaignStatus: prev.campaignStatus,
        log: [
          {
            contact: d.last_contact,
            mailbox: d.current_mailbox,
            subject: d.last_subject,
            status: d.last_status,
            time: new Date().toLocaleTimeString(),
          },
          ...prev.log.slice(0, 19),
        ],
      }));
    }

    if (lastMessage.type === "status") {
      setProgress((prev) => ({
        ...prev,
        campaignStatus: lastMessage.data.status,
      }));
    }
  }, [lastMessage]);

  return { progress, isConnected };
}
