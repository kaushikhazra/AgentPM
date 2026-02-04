import { createContext, useCallback, useState, type ReactNode } from 'react';

export interface ModalState {
  type: string;
  props?: Record<string, unknown>;
}

export interface ModalContextValue {
  modal: ModalState | null;
  open: (type: string, props?: Record<string, unknown>) => void;
  close: () => void;
}

export const ModalContext = createContext<ModalContextValue | null>(null);

export function ModalProvider({ children }: { children: ReactNode }) {
  const [modal, setModal] = useState<ModalState | null>(null);

  const open = useCallback(
    (type: string, props?: Record<string, unknown>) => setModal({ type, props }),
    [],
  );

  const close = useCallback(() => setModal(null), []);

  return (
    <ModalContext.Provider value={{ modal, open, close }}>
      {children}
    </ModalContext.Provider>
  );
}
