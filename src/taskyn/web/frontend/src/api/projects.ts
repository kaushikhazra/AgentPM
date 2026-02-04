import { api } from './client';
import type {
  MethodologyInfo,
  Project,
  ProjectCreate,
  ProjectStats,
  ProjectUpdate,
} from '@/types';

export const projectsApi = {
  list: (filters?: { company_id?: string; status?: string; include_stats?: boolean }) => {
    const params = new URLSearchParams();
    if (filters?.company_id) params.set('company_id', filters.company_id);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.include_stats) params.set('include_stats', 'true');
    return api.get<Project[]>(`/projects/?${params}`);
  },

  get: (id: string) =>
    api.get<Project>(`/projects/${id}`),

  create: (data: ProjectCreate) =>
    api.post<Project>('/projects/', data),

  update: (id: string, data: ProjectUpdate) =>
    api.patch<Project>(`/projects/${id}`, data),

  delete: (id: string) =>
    api.delete(`/projects/${id}`),

  getMethodology: (id: string) =>
    api.get<MethodologyInfo>(`/projects/${id}/methodology`),

  getStats: (id: string) =>
    api.get<ProjectStats>(`/projects/${id}/stats`),
};
