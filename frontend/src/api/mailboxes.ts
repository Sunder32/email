import api from "./client";
import type { Mailbox, MailboxCreate, MailboxTestResult } from "@/types/domain";

export const createMailbox = (domainId: number, data: MailboxCreate) =>
  api.post<Mailbox>(`/mailboxes/domain/${domainId}`, data).then((r) => r.data);

export const updateMailbox = (id: number, data: Partial<MailboxCreate & { is_active: boolean }>) =>
  api.put<Mailbox>(`/mailboxes/${id}`, data).then((r) => r.data);

export const deleteMailbox = (id: number) =>
  api.delete(`/mailboxes/${id}`);

export const testMailbox = (id: number) =>
  api.post<MailboxTestResult>(`/mailboxes/${id}/test`).then((r) => r.data);
