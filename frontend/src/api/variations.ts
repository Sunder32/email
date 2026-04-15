import api from "./client";
import type { TextVariation } from "@/types/variation";

export const generateVariations = (campaignId: number, count: number = 30) =>
  api.post(`/campaigns/${campaignId}/variations/generate`, { count }).then((r) => r.data);

export const getVariations = (campaignId: number) =>
  api.get<TextVariation[]>(`/campaigns/${campaignId}/variations`).then((r) => r.data);

export const updateVariation = (id: number, data: { subject_variant?: string; iceberg_variant?: string }) =>
  api.put<TextVariation>(`/variations/${id}`, data).then((r) => r.data);

export const deleteVariation = (id: number) =>
  api.delete(`/variations/${id}`);
