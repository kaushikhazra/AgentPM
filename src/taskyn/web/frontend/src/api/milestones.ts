import { api } from './client';
import type { Milestone, MilestoneCreate, MilestoneUpdate } from '@/types';

export const milestonesApi = {
  list: (projectId: string, status?: string) => {
    const params = new URLSearchParams({ project_id: projectId });
    if (status) params.set('status', status);
    return api.get<Milestone[]>(`/milestones?${params}`);
  },

  get: (id: string) =>
    api.get<Milestone>(`/milestones/${id}`),

  create: (data: MilestoneCreate) =>
    api.post<Milestone>('/milestones', data),

  update: (id: string, data: MilestoneUpdate) =>
    api.patch<Milestone>(`/milestones/${id}`, data),

  complete: (id: string) =>
    api.post<Milestone>(`/milestones/${id}/complete`),

  delete: (id: string) =>
    api.delete(`/milestones/${id}`),
};
