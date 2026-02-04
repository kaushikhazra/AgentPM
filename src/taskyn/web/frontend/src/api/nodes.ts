import { api } from './client';
import type { Node, NodeCreate, NodeRollup, NodeUpdate } from '@/types';

export const nodesApi = {
  list: (filters?: {
    project_id?: string;
    node_type?: string;
    status?: string;
    assignee?: string;
  }) => {
    const params = new URLSearchParams();
    if (filters?.project_id) params.set('project_id', filters.project_id);
    if (filters?.node_type) params.set('node_type', filters.node_type);
    if (filters?.status) params.set('status', filters.status);
    if (filters?.assignee) params.set('assignee', filters.assignee);
    return api.get<Node[]>(`/nodes?${params}`);
  },

  get: (id: string) =>
    api.get<Node>(`/nodes/${id}`),

  create: (data: NodeCreate) =>
    api.post<Node>('/nodes', data),

  update: (id: string, data: NodeUpdate) =>
    api.patch<Node>(`/nodes/${id}`, data),

  start: (id: string) =>
    api.post<Node>(`/nodes/${id}/start`),

  complete: (id: string) =>
    api.post<Node>(`/nodes/${id}/complete`),

  block: (id: string, reason: string) =>
    api.post<Node>(`/nodes/${id}/block`, { reason }),

  getAncestors: (id: string, edgeType?: string) => {
    const params = edgeType ? `?edge_type=${edgeType}` : '';
    return api.get<Node[]>(`/nodes/${id}/ancestors${params}`);
  },

  getDescendants: (id: string, edgeType?: string) => {
    const params = edgeType ? `?edge_type=${edgeType}` : '';
    return api.get<Node[]>(`/nodes/${id}/descendants${params}`);
  },

  getRollup: (id: string) =>
    api.get<NodeRollup>(`/nodes/${id}/rollup`),

  tag: (id: string, tagName: string) =>
    api.post(`/nodes/${id}/tags`, { tag_name: tagName }),

  untag: (id: string, tagName: string) =>
    api.delete(`/nodes/${id}/tags/${tagName}`),
};
