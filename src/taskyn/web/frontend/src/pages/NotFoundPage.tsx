import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/atoms';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="auth-layout">
      <div style={{ textAlign: 'center' }}>
        <h1 className="page-title" style={{ fontSize: '4rem', marginBottom: 8 }}>404</h1>
        <p className="text-secondary" style={{ marginBottom: 24 }}>
          The page you're looking for doesn't exist.
        </p>
        <Button variant="primary" onClick={() => navigate('/dashboard')}>
          Go to Dashboard
        </Button>
      </div>
    </div>
  );
}
