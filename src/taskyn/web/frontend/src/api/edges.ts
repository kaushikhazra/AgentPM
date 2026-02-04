import { api } from './client';
import type { Edge, EdgeCreate } from '@/types';

export const edgesApi = {
  list: (filters?: {
    project_id?: string;
    source_id?: string;
    target_id?: string;
    edge_type?: string;
  }) => {
    const params = new URLSearchParams();
    if (filters?.project_id) params.set('project_id', filters.project_id);
    if (filters?.source_id) params.set('source_id', filters.source_id);
    if (filters?.target_id) params.set('target_id', filters.target_id);
    if (filters?.edge_type) params.set('edge_type', filters.edge_type);
    return api.get<Edge[]>(`/edges/?${params}`);
  },

  create: (data: EdgeCreate) =>
    api.post<Edge>('/edges/', data),

  delete: (id: string) =>
    api.delete(`/edges/${id}`),
};
