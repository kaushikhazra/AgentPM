import { useQuery } from '@tanstack/react-query';
import { edgesApi } from '@/api/edges';
import { queryKeys } from '@/api/queryKeys';

interface QueryOptions {
  refetchInterval?: number | false;
}

export function useEdges(filters?: {
  project_id?: string;
  source_id?: string;
  target_id?: string;
  edge_type?: string;
}, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.edges.list(filters),
    queryFn: () => edgesApi.list(filters),
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}
