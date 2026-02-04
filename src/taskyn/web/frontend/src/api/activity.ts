import { api } from './client';
import type { ActivityEntry } from '@/types';

export const activityApi = {
  list: (filters?: {
    limit?: number;
    entity_type?: string;
    entity_id?: string;
  }) => {
    const params = new URLSearchParams();
    if (filters?.limit) params.set('limit', String(filters.limit));
    if (filters?.entity_type) params.set('entity_type', filters.entity_type);
    if (filters?.entity_id) params.set('entity_id', filters.entity_id);
    return api.get<ActivityEntry[]>(`/activity?${params}`);
  },
};
