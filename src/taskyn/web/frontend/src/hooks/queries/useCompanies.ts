import { useQuery } from '@tanstack/react-query';
import { companiesApi } from '@/api/companies';
import { queryKeys } from '@/api/queryKeys';

export function useCompanies(includeStats?: boolean) {
  return useQuery({
    queryKey: queryKeys.companies.list({ includeStats }),
    queryFn: () => companiesApi.list(includeStats),
    refetchInterval: 30_000,
  });
}

export function useCompany(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.companies.detail(id!),
    queryFn: () => companiesApi.get(id!),
    enabled: !!id,
    refetchInterval: 30_000,
  });
}

export function useCompanyStats(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.companies.stats(id!),
    queryFn: () => companiesApi.getStats(id!),
    enabled: !!id,
  });
}
