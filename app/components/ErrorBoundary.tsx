"use client";

import React from "react";

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    console.error("[ErrorBoundary] Caught error:", error);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("[ErrorBoundary] Error caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen flex-col items-center justify-center bg-[--bg-base] p-6">
          <div className="max-w-md text-center space-y-4">
            <h1 className="text-2xl font-semibold text-[--text-primary]">Something went wrong</h1>
            <p className="text-sm text-[--text-secondary]">
              {this.state.error?.message || "An unexpected error occurred"}
            </p>
            <details className="text-xs text-[--text-muted] text-left p-3 bg-[--bg-surface] rounded border border-[--border] overflow-auto max-h-32">
              <summary className="cursor-pointer font-semibold mb-2">Error details</summary>
              <pre className="whitespace-pre-wrap break-words font-mono">
                {this.state.error?.stack}
              </pre>
            </details>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 rounded-lg bg-[--accent] px-4 py-2 font-semibold text-white hover:opacity-90 transition-opacity"
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
