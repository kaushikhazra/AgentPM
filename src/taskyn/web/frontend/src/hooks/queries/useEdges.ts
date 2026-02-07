import { useQuery } from '@tanstack/react-query';
import { edgesApi } from '@/api/edges';
import { queryKeys } from '@/api/queryKeys';

export function useEdges(filters?: {
  project_id?: string;
  source_id?: string;
  target_id?: string;
  edge_type?: string;
}) {
  return useQuery({
    queryKey: queryKeys.edges.list(filters),
    queryFn: () => edgesApi.list(filters),
    refetchInterval: 10_000,
  });
}
