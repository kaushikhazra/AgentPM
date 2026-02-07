import { useQuery } from '@tanstack/react-query';
import { projectsApi } from '@/api/projects';
import { queryKeys } from '@/api/queryKeys';

export function useProjects(filters?: {
  company_id?: string;
  status?: string;
  include_stats?: boolean;
}) {
  return useQuery({
    queryKey: queryKeys.projects.list(filters),
    queryFn: () => projectsApi.list(filters),
    refetchInterval: 30_000,
  });
}

export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.detail(id!),
    queryFn: () => projectsApi.get(id!),
    enabled: !!id,
    refetchInterval: 30_000,
  });
}

export function useProjectMethodology(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.methodology(id!),
    queryFn: () => projectsApi.getMethodology(id!),
    enabled: !!id,
  });
}

export function useProjectStats(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.projects.stats(id!),
    queryFn: () => projectsApi.getStats(id!),
    enabled: !!id,
  });
}
