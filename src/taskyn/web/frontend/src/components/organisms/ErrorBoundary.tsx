import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from '@/components/atoms';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info.componentStack);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="content-wrapper" style={{ textAlign: 'center', paddingTop: 80 }}>
          <h1 className="page-title">Something went wrong</h1>
          <p className="text-secondary" style={{ marginBottom: 24 }}>
            {this.state.error?.message ?? 'An unexpected error occurred.'}
          </p>
          <Button variant="primary" onClick={this.handleReset}>
            Try again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
