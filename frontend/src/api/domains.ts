import api from "./client";
import type { Domain, DomainCreate } from "@/types/domain";

export const getDomains = () =>
  api.get<Domain[]>("/domains").then((r) => r.data);

export const createDomain = (data: DomainCreate) =>
  api.post<Domain>("/domains", data).then((r) => r.data);

export const updateDomain = (id: number, data: Partial<DomainCreate & { is_active: boolean }>) =>
  api.put<Domain>(`/domains/${id}`, data).then((r) => r.data);

export const deleteDomain = (id: number) =>
  api.delete(`/domains/${id}`);
