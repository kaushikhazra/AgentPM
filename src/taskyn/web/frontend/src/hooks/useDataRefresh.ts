import { useContext } from 'react';
import { DataRefreshContext, type DataRefreshContextValue } from '@/providers/DataRefreshProvider';

export function useDataRefresh(): DataRefreshContextValue {
  const ctx = useContext(DataRefreshContext);
  if (!ctx) throw new Error('useDataRefresh must be used within DataRefreshProvider');
  return ctx;
}
