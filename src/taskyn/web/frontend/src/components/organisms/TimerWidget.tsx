import { useTimer } from '@/hooks/useTimer';
import { Icon } from '@/components/atoms';
import type { ActiveTimer } from '@/types';

function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

export function TimerWidget() {
  const { activeTimers, elapsedMap, loading, stop } = useTimer();

  if (activeTimers.length === 0) {
    return (
      <div className="timer-widget">
        <div className="timer-label">No Active Timer</div>
        <div className="timer-display">00:00:00</div>
      </div>
    );
  }

  // Single timer — compact layout
  if (activeTimers.length === 1) {
    const timer = activeTimers[0]!;
    return (
      <div className="timer-widget">
        <div className="timer-label">Timer Running</div>
        <div className="timer-display">
          {formatElapsed(elapsedMap[timer.id] ?? 0)}
        </div>
        <div className="timer-task">{timer.node_title ?? timer.node_id.slice(0, 8)}</div>
        {timer.actor && (
          <span className="timer-actor">{timer.actor}</span>
        )}
        <div className="timer-controls">
          <button
            className="timer-btn timer-btn-stop"
            onClick={() => void stop(timer.id)}
            disabled={loading}
          >
            <Icon name="stop" size={14} />
            Stop
          </button>
        </div>
      </div>
    );
  }

  // Multiple timers — list with per-timer stop buttons
  return (
    <div className="timer-widget">
      <div className="timer-label">
        {activeTimers.length} Active Timers
      </div>
      {activeTimers.map((timer: ActiveTimer) => (
        <div key={timer.id} className="timer-entry">
          <div className="timer-display">
            {formatElapsed(elapsedMap[timer.id] ?? 0)}
          </div>
          <div className="timer-task">
            {timer.node_title ?? timer.node_id.slice(0, 8)}
          </div>
          {timer.actor && (
            <span className="timer-actor">{timer.actor}</span>
          )}
          <button
            className="timer-btn timer-btn-stop"
            onClick={() => void stop(timer.id)}
            disabled={loading}
          >
            <Icon name="stop" size={14} />
            Stop
          </button>
        </div>
      ))}
    </div>
  );
}
