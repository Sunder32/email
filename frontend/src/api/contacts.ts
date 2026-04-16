import api from "./client";
import type { Contact, ContactUploadResponse } from "@/types/contact";
import type { CampaignReport } from "@/types/campaign";

export const uploadContacts = (campaignId: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post<ContactUploadResponse>(`/campaigns/${campaignId}/contacts/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const getContacts = (
  campaignId: number,
  params?: { status?: string; validation?: string; search?: string; page?: number; size?: number }
) => api.get<Contact[]>(`/campaigns/${campaignId}/contacts`, { params }).then((r) => r.data);

export const validateContacts = (campaignId: number) =>
  api.post(`/campaigns/${campaignId}/contacts/validate`).then((r) => r.data);

export const markAllValid = (campaignId: number) =>
  api.post<{ marked_valid: number }>(`/campaigns/${campaignId}/contacts/mark-all-valid`).then((r) => r.data);

export const getCampaignReport = (campaignId: number) =>
  api.get<CampaignReport>(`/campaigns/${campaignId}/contacts/report`).then((r) => r.data);

export const exportReportUrl = (campaignId: number) =>
  `/api/campaigns/${campaignId}/contacts/export`;
