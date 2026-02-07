import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { queryKeys } from '@/api/queryKeys';

export function useDashboard(options?: { refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.dashboard.all(),
    queryFn: () => dashboardApi.get(),
    refetchInterval: options?.refetchInterval,
  });
}
