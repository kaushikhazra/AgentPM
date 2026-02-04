interface ShortcutHint {
  key: string;
  label: string;
}

interface ShortcutBarProps {
  shortcuts: ShortcutHint[];
}

export function ShortcutBar({ shortcuts }: ShortcutBarProps) {
  if (shortcuts.length === 0) return null;

  return (
    <footer className="shortcut-bar">
      {shortcuts.map((s) => (
        <div key={s.key} className="shortcut-item">
          <kbd className="shortcut-key">{s.key}</kbd>
          <span className="shortcut-label">{s.label}</span>
        </div>
      ))}
    </footer>
  );
}
