import { ReactNode } from "react";

import { LoadingSpinner } from "./LoadingSpinner";

export function LoadingBoundary({
    loading,
    error,
    children,
    loadingMessage,
}: {
    loading: boolean;
    error?: string | null;
    children: ReactNode;
    loadingMessage?: string;
}) {
    if (loading) {
        return <LoadingSpinner message={loadingMessage ?? "Loading..."} />;
    }

    if (error) {
        return (
            <div style={{ padding: "10px 14px", background: "var(--danger-soft)", color: "var(--danger-ink)", border: "1px solid var(--danger-line)", borderRadius: "12px" }}>
                {error}
            </div>
        );
    }

    return <>{children}</>;
}
