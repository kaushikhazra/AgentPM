import { useQuery } from '@tanstack/react-query';
import { timerApi } from '@/api/timer';
import { queryKeys } from '@/api/queryKeys';

export function useTimerCurrent(options?: { enabled?: boolean; refetchInterval?: number }) {
  return useQuery({
    queryKey: queryKeys.timer.current(),
    queryFn: () => timerApi.getCurrent(),
    enabled: options?.enabled ?? true,
    refetchInterval: options?.refetchInterval ?? 1_000,
  });
}

export function useTimeEntries(projectId?: string) {
  return useQuery({
    queryKey: queryKeys.timer.list(projectId),
    queryFn: () => timerApi.listTimeEntries(projectId),
    refetchInterval: 10_000,
  });
}

export function useTimeEntry(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.timer.entry(id!),
    queryFn: () => timerApi.getTimeEntry(id!),
    enabled: !!id,
  });
}
