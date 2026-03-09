import { useQuery } from '@tanstack/react-query';
import { activityApi } from '@/api/activity';
import { queryKeys } from '@/api/queryKeys';

interface QueryOptions {
  refetchInterval?: number | false;
}

export function useActivity(filters?: {
  limit?: number;
  entity_type?: string;
  entity_id?: string;
}, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.activity.list(filters),
    queryFn: () => activityApi.list(filters),
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}
