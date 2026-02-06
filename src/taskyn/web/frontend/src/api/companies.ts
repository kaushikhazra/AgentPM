import { api } from './client';
import type { Company, CompanyCreate, CompanyStats } from '@/types';

export const companiesApi = {
  list: (includeStats = false) =>
    api.get<Company[]>(`/companies?include_stats=${includeStats}`),

  get: (id: string) =>
    api.get<Company>(`/companies/${id}`),

  create: (data: CompanyCreate) =>
    api.post<Company>('/companies', data),

  update: (id: string, data: Partial<CompanyCreate>) =>
    api.patch<Company>(`/companies/${id}`, data),

  delete: (id: string) =>
    api.delete(`/companies/${id}`),

  getStats: (id: string) =>
    api.get<CompanyStats>(`/companies/${id}/stats`),
};
