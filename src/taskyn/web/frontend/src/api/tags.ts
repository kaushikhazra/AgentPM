import { api } from './client';
import type { Tag, TagCreate, TagUsage, TagDeleteResult } from '@/types';

export const tagsApi = {
  list: () =>
    api.get<Tag[]>('/tags'),

  create: (data: TagCreate) =>
    api.post<Tag>('/tags', data),

  getUsage: (tagName: string) =>
    api.get<TagUsage>(`/tags/${encodeURIComponent(tagName)}/usage`),

  delete: (tagName: string) =>
    api.delete<TagDeleteResult>(`/tags/${encodeURIComponent(tagName)}`),
};
