import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error caught by OPTIV ErrorBoundary:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: 40,
            maxWidth: 600,
            margin: '60px auto',
            backgroundColor: 'var(--tprm-surface)',
            border: '1px solid var(--tprm-rose)',
            borderRadius: 12,
            boxShadow: 'var(--tprm-shadow-md)',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: 50,
              height: 50,
              borderRadius: '50%',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 16px',
            }}
          >
            <AlertOctagon size={28} color="#ef4444" />
          </div>

          <h2 style={{ margin: '0 0 8px', fontSize: '1.25rem', color: 'var(--tprm-text-primary)' }}>
            Workspace Rendering Notice
          </h2>

          <p style={{ fontSize: '0.85rem', color: 'var(--tprm-text-muted)', margin: '0 0 16px', lineHeight: 1.5 }}>
            A client-side state issue was intercepted. You can reset the active workspace session below.
          </p>

          {this.state.error && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: 6,
                backgroundColor: 'var(--tprm-surface-subtle)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
                color: 'var(--tprm-rose)',
                textAlign: 'left',
                marginBottom: 20,
                overflowX: 'auto',
              }}
            >
              {this.state.error.message}
            </div>
          )}

          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="btn-primary"
            style={{ padding: '8px 18px', fontSize: '0.85rem', margin: '0 auto', display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <RefreshCw size={15} />
            <span>Reload Workspace</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
