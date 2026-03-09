import { useQuery } from '@tanstack/react-query';
import { nodesApi } from '@/api/nodes';
import { queryKeys } from '@/api/queryKeys';

interface QueryOptions {
  refetchInterval?: number | false;
}

export function useNodes(filters?: {
  project_id?: string;
  node_type?: string;
  status?: string;
  assignee?: string;
}, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.nodes.list(filters),
    queryFn: () => nodesApi.list(filters),
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}

export function useNode(id: string | undefined, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.nodes.detail(id!),
    queryFn: () => nodesApi.get(id!),
    enabled: !!id,
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}

export function useNodeAncestors(id: string | undefined, edgeType?: string, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.nodes.ancestors(id!, edgeType),
    queryFn: () => nodesApi.getAncestors(id!, edgeType),
    enabled: !!id,
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}

export function useNodeDescendants(id: string | undefined, edgeType?: string, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.nodes.descendants(id!, edgeType),
    queryFn: () => nodesApi.getDescendants(id!, edgeType),
    enabled: !!id,
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}

export function useNodeRollup(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.nodes.rollup(id!),
    queryFn: () => nodesApi.getRollup(id!),
    enabled: !!id,
  });
}
