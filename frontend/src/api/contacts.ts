import api from "./client";
import type { Contact, ContactUploadResponse } from "@/types/contact";

export const uploadContacts = (campaignId: number, file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post<ContactUploadResponse>(`/campaigns/${campaignId}/contacts/upload`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    })
    .then((r) => r.data);
};

export const getContacts = (campaignId: number, params?: { status?: string; page?: number; size?: number }) =>
  api.get<Contact[]>(`/campaigns/${campaignId}/contacts`, { params }).then((r) => r.data);

export const validateContacts = (campaignId: number) =>
  api.post(`/campaigns/${campaignId}/contacts/validate`).then((r) => r.data);
