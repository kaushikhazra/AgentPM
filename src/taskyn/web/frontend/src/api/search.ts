import { api } from './client';
import type { SearchResult } from '@/types';

export const searchApi = {
  search: (query: string, filters?: {
    entity_type?: string;
    project_id?: string;
    limit?: number;
  }) => {
    const params = new URLSearchParams({ query });
    if (filters?.entity_type) params.set('entity_type', filters.entity_type);
    if (filters?.project_id) params.set('project_id', filters.project_id);
    if (filters?.limit) params.set('limit', String(filters.limit));
    return api.get<SearchResult[]>(`/search?${params}`);
  },
};
