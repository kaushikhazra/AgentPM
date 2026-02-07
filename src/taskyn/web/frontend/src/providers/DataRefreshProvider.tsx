import { createContext, useCallback, type ReactNode } from 'react';
import { useQueryClient, useIsFetching } from '@tanstack/react-query';

export interface DataRefreshContextValue {
  refreshAll: () => void;
  isRefreshing: boolean;
}

export const DataRefreshContext = createContext<DataRefreshContextValue | null>(null);

export function DataRefreshProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const fetchingCount = useIsFetching();

  const refreshAll = useCallback(() => {
    queryClient.invalidateQueries();
  }, [queryClient]);

  return (
    <DataRefreshContext.Provider
      value={{ refreshAll, isRefreshing: fetchingCount > 0 }}
    >
      {children}
    </DataRefreshContext.Provider>
  );
}
