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
            <div style={{ padding: "10px 14px", background: "#fde8e8", color: "#9b2c2c", border: "1px solid #f8b4b4", borderRadius: "12px" }}>
                {error}
            </div>
        );
    }

    return <>{children}</>;
}
