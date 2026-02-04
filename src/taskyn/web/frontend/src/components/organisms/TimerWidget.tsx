import { useTimer } from '@/hooks/useTimer';
import { Icon } from '@/components/atoms';

function formatElapsed(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${pad(h)}:${pad(m)}:${pad(s)}`;
}

export function TimerWidget() {
  const { activeTimer, elapsed, loading, stop } = useTimer();

  return (
    <div className="timer-widget">
      <div className="timer-label">
        {activeTimer ? 'Timer Running' : 'No Active Timer'}
      </div>
      <div className="timer-display">
        {formatElapsed(elapsed)}
      </div>
      {activeTimer && (
        <>
          <div className="timer-task">{activeTimer.node_id}</div>
          <div className="timer-controls">
            <button
              className="timer-btn timer-btn-stop"
              onClick={() => void stop()}
              disabled={loading}
            >
              <Icon name="stop" size={14} />
              Stop
            </button>
          </div>
        </>
      )}
    </div>
  );
}
