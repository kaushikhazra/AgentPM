import { useQuery } from '@tanstack/react-query';
import { timerApi } from '@/api/timer';
import { queryKeys } from '@/api/queryKeys';

interface QueryOptions {
  enabled?: boolean;
  refetchInterval?: number | false;
}

export function useTimerCurrent(options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.timer.current(),
    queryFn: () => timerApi.getCurrent(),
    enabled: options?.enabled ?? true,
    refetchInterval: options?.refetchInterval ?? 1_000,
  });
}

export function useActiveTimers(options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.timer.active(),
    queryFn: () => timerApi.getActive(),
    enabled: options?.enabled ?? true,
    refetchInterval: options?.refetchInterval ?? 1_000,
  });
}

export function useTimeEntries(projectId?: string, options?: QueryOptions) {
  return useQuery({
    queryKey: queryKeys.timer.list(projectId),
    queryFn: () => timerApi.listTimeEntries(projectId),
    refetchInterval: options?.refetchInterval ?? 10_000,
  });
}

export function useTimeEntry(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.timer.entry(id!),
    queryFn: () => timerApi.getTimeEntry(id!),
    enabled: !!id,
  });
}
