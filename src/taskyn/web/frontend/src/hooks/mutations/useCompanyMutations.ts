import { useMutation, useQueryClient } from '@tanstack/react-query';
import { companiesApi } from '@/api/companies';
import { queryKeys } from '@/api/queryKeys';
import { useToast } from '@/hooks/useToast';
import type { CompanyCreate } from '@/types';

export function useCreateCompany() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (data: CompanyCreate) => companiesApi.create(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.companies.all() });
      addToast('success', 'Company created');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useUpdateCompany() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<CompanyCreate> }) =>
      companiesApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.companies.all() });
      addToast('success', 'Company updated');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}

export function useDeleteCompany() {
  const qc = useQueryClient();
  const { addToast } = useToast();

  return useMutation({
    mutationFn: (id: string) => companiesApi.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.companies.all() });
      qc.invalidateQueries({ queryKey: queryKeys.projects.all() });
      addToast('success', 'Company deleted');
    },
    onError: (err: Error) => addToast('error', err.message),
  });
}
