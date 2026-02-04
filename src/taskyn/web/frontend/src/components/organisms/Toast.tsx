import { Icon, type IconName } from '@/components/atoms';
import type { Toast as ToastType } from '@/providers/ToastProvider';

interface ToastProps {
  toast: ToastType;
  onDismiss: (id: string) => void;
}

const iconMap: Record<string, IconName> = {
  success: 'check',
  error: 'x',
  info: 'help',
};

export function Toast({ toast, onDismiss }: ToastProps) {
  return (
    <div
      className={`toast toast--${toast.type}`}
      onClick={() => onDismiss(toast.id)}
      role="alert"
    >
      <Icon name={iconMap[toast.type] ?? 'help'} size={16} />
      {toast.message}
    </div>
  );
}
