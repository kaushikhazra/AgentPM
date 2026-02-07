import { useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';
import { queryKeys } from '@/api/queryKeys';
import { useToast } from '@/hooks/useToast';
import type { ProjectCreate, ProjectUpdate } from '@/types';

export function useCreateProject() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (data: ProjectCreate) => projectsApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projects.all() });
      qc.invalidateQueries({ queryKey: queryKeys.companies.all() });
      addToast('success', 'Project created');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useUpdateProject() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProjectUpdate }) =>
      projectsApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projects.all() });
      addToast('success', 'Project updated');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useDeleteProject() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => projectsApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.projects.all() });
      qc.invalidateQueries({ queryKey: queryKeys.companies.all() });
      addToast('success', 'Project deleted');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}
