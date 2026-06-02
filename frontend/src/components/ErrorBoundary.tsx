import React, { ReactNode } from "react";

type ErrorBoundaryState = {
    hasError: boolean;
    message: string;
};

export class ErrorBoundary extends React.Component<{ children: ReactNode }, ErrorBoundaryState> {
    constructor(props: { children: ReactNode }) {
        super(props);
        this.state = { hasError: false, message: "" };
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return { hasError: true, message: error.message || "Unexpected UI error" };
    }

    componentDidCatch(): void {
        // Intentionally no-op for now; centralized error reporting will be added in observability gate.
    }

    render() {
        if (this.state.hasError) {
            return (
                <div style={{ padding: "14px", borderRadius: "12px", background: "var(--danger-soft)", border: "1px solid var(--danger-line)", color: "var(--danger-ink)" }}>
                    <strong>UI Error:</strong> {this.state.message}
                </div>
            );
        }
        return this.props.children;
    }
}
