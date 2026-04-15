import api from "./client";
import type { SendLog } from "@/types/sendLog";

export const getSendLogs = (
  campaignId: number,
  params?: { mailbox_id?: number; status?: string; page?: number; size?: number }
) =>
  api.get<SendLog[]>(`/campaigns/${campaignId}/logs`, { params }).then((r) => r.data);
