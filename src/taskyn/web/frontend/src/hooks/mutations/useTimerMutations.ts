import { useMutation, useQueryClient } from '@tanstack/react-query';
import { timerApi } from '@/api/timer';
import { queryKeys } from '@/api/queryKeys';
import { useToast } from '@/hooks/useToast';
import type { TimeEntryCreate } from '@/types';

export function useStartTimer() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ nodeId, notes }: { nodeId: string; notes?: string }) =>
      timerApi.start(nodeId, notes),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.timer.all() });
      addToast('success', 'Timer started');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useStopTimer() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (entryId?: string) => timerApi.stop(entryId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.timer.all() });
      qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
      addToast('success', 'Timer stopped');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useLogTime() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (data: TimeEntryCreate) => timerApi.logTime(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
      qc.invalidateQueries({ queryKey: queryKeys.timer.all() });
      addToast('success', 'Time logged');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useDeleteTimeEntry() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => timerApi.deleteTimeEntry(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
      qc.invalidateQueries({ queryKey: queryKeys.timer.all() });
      addToast('success', 'Time entry deleted');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}
