import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
          <div className="max-w-md text-center">
            <div className="mb-4 text-4xl font-bold text-sev-critical">500</div>
            <h1 className="mb-2 text-lg font-semibold text-ink-900">Something went wrong</h1>
            <p className="mb-4 text-sm text-ink-500">
              An unexpected error occurred. Try refreshing the page.
            </p>
            <button
              className="btn-primary"
              onClick={() => window.location.reload()}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
