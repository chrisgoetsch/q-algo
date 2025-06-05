import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props { children: ReactNode }
interface State { hasError: boolean }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', error, info);
    // TODO: send to Sentry/LogRocket
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center bg-gray-100 dark:bg-gray-900">
          <div className="text-center space-y-4">
            <h1 className="text-2xl font-semibold text-red-600">Something went wrong.</h1>
            <p className="text-gray-600 dark:text-gray-400">The dashboard crashed — please refresh.</p>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
