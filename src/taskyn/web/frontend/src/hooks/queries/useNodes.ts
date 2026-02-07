import { useQuery } from '@tanstack/react-query';
import { nodesApi } from '@/api/nodes';
import { queryKeys } from '@/api/queryKeys';

export function useNodes(filters?: {
  project_id?: string;
  node_type?: string;
  status?: string;
  assignee?: string;
}) {
  return useQuery({
    queryKey: queryKeys.nodes.list(filters),
    queryFn: () => nodesApi.list(filters),
  });
}

export function useNode(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.nodes.detail(id!),
    queryFn: () => nodesApi.get(id!),
    enabled: !!id,
  });
}

export function useNodeAncestors(id: string | undefined, edgeType?: string) {
  return useQuery({
    queryKey: queryKeys.nodes.ancestors(id!, edgeType),
    queryFn: () => nodesApi.getAncestors(id!, edgeType),
    enabled: !!id,
  });
}

export function useNodeDescendants(id: string | undefined, edgeType?: string) {
  return useQuery({
    queryKey: queryKeys.nodes.descendants(id!, edgeType),
    queryFn: () => nodesApi.getDescendants(id!, edgeType),
    enabled: !!id,
  });
}

export function useNodeRollup(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.nodes.rollup(id!),
    queryFn: () => nodesApi.getRollup(id!),
    enabled: !!id,
  });
}
