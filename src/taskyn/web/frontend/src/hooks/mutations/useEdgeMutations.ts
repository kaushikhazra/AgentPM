import { useMutation, useQueryClient } from '@tanstack/react-query';
import { edgesApi } from '@/api/edges';
import { queryKeys } from '@/api/queryKeys';
import { useToast } from '@/hooks/useToast';
import type { EdgeCreate } from '@/types';

export function useCreateEdge() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (data: EdgeCreate) => edgesApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.edges.all() });
      qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useDeleteEdge() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => edgesApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.edges.all() });
      qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}
