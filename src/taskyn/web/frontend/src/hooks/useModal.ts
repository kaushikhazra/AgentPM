import { useContext } from 'react';
import { ModalContext, type ModalContextValue } from '@/providers/ModalProvider';

export function useModal(): ModalContextValue {
  const ctx = useContext(ModalContext);
  if (!ctx) throw new Error('useModal must be used within ModalProvider');
  return ctx;
}
