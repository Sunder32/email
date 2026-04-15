import api from "./client";
import type { Campaign, CampaignCreate, CampaignStats } from "@/types/campaign";

export const getCampaigns = () =>
  api.get<Campaign[]>("/campaigns").then((r) => r.data);

export const getCampaign = (id: number) =>
  api.get<Campaign>(`/campaigns/${id}`).then((r) => r.data);

export const createCampaign = (data: CampaignCreate) =>
  api.post<Campaign>("/campaigns", data).then((r) => r.data);

export const updateCampaign = (id: number, data: Partial<CampaignCreate>) =>
  api.put<Campaign>(`/campaigns/${id}`, data).then((r) => r.data);

export const deleteCampaign = (id: number) =>
  api.delete(`/campaigns/${id}`);

export const startCampaign = (id: number) =>
  api.post<Campaign>(`/campaigns/${id}/start`).then((r) => r.data);

export const pauseCampaign = (id: number) =>
  api.post<Campaign>(`/campaigns/${id}/pause`).then((r) => r.data);

export const stopCampaign = (id: number) =>
  api.post<Campaign>(`/campaigns/${id}/stop`).then((r) => r.data);

export const getCampaignStats = (id: number) =>
  api.get<CampaignStats>(`/campaigns/${id}/stats`).then((r) => r.data);
