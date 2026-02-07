import { useQuery } from '@tanstack/react-query';
import { activityApi } from '@/api/activity';
import { queryKeys } from '@/api/queryKeys';

export function useActivity(filters?: {
  limit?: number;
  entity_type?: string;
  entity_id?: string;
}) {
  return useQuery({
    queryKey: queryKeys.activity.list(filters),
    queryFn: () => activityApi.list(filters),
    refetchInterval: 30_000,
  });
}
