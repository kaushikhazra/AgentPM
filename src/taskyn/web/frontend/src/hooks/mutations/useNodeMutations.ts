import { useMutation, useQueryClient } from '@tanstack/react-query';
import { nodesApi } from '@/api/nodes';
import { queryKeys } from '@/api/queryKeys';
import { useToast } from '@/hooks/useToast';
import type { Node, NodeCreate, NodeUpdate } from '@/types';

function useNodeInvalidation() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
    qc.invalidateQueries({ queryKey: queryKeys.dashboard.all() });
  };
}

function useNodeAndProjectInvalidation() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
    qc.invalidateQueries({ queryKey: queryKeys.dashboard.all() });
    qc.invalidateQueries({ queryKey: queryKeys.projects.all() });
  };
}

export function useCreateNode() {
  const invalidate = useNodeAndProjectInvalidation();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (data: NodeCreate) => nodesApi.create(data),
    onSuccess: () => {
      invalidate();
      addToast('success', 'Node created');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useUpdateNode() {
  const invalidate = useNodeInvalidation();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NodeUpdate }) =>
      nodesApi.update(id, data),
    onSuccess: () => invalidate(),
    onError: (err: Error) => addToast('error', err.message),
  });
}

/** Optimistic variant of useUpdateNode for drag-and-drop scenarios. */
export function useOptimisticUpdateNode(projectId: string) {
  const qc = useQueryClient();
  const { addToast } = useToast();
  const listKey = queryKeys.nodes.list({ project_id: projectId });

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NodeUpdate }) =>
      nodesApi.update(id, data),
    onMutate: async ({ id, data }) => {
      await qc.cancelQueries({ queryKey: listKey });
      const previous = qc.getQueryData<Node[]>(listKey);
      qc.setQueryData<Node[]>(listKey, (old) =>
        old?.map((n) => (n.id === id ? { ...n, ...data } : n)),
      );
      return { previous };
    },
    onError: (_err, _vars, context) => {
      if (context?.previous) qc.setQueryData(listKey, context.previous);
      addToast('error', 'Failed to update status');
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: queryKeys.nodes.all() });
      qc.invalidateQueries({ queryKey: queryKeys.dashboard.all() });
    },
  });
}

export function useDeleteNode() {
  const invalidate = useNodeAndProjectInvalidation();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => nodesApi.delete(id),
    onSuccess: () => {
      invalidate();
      addToast('success', 'Node deleted');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useStartNode() {
  const invalidate = useNodeInvalidation();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => nodesApi.start(id),
    onSuccess: () => {
      invalidate();
      addToast('success', 'Started');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useCompleteNode() {
  const invalidate = useNodeAndProjectInvalidation();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => nodesApi.complete(id),
    onSuccess: () => {
      invalidate();
      addToast('success', 'Marked as complete');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useBlockNode() {
  const invalidate = useNodeInvalidation();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      nodesApi.block(id, reason),
    onSuccess: () => {
      invalidate();
      addToast('success', 'Node blocked');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}
