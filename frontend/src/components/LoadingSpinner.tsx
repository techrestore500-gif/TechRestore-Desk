import type { CSSProperties } from "react";

interface LoadingSpinnerProps {
    size?: "sm" | "md" | "lg";
    message?: string;
}

export function LoadingSpinner({ size = "md", message }: LoadingSpinnerProps) {
    const sizeMap = { sm: 24, md: 40, lg: 56 };
    const dimension = sizeMap[size];

    return (
        <div
            style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                gap: "12px",
                padding: "24px",
            }}
        >
            <div
                style={{
                    width: dimension,
                    height: dimension,
                    border: "3px solid rgba(31, 102, 87, 0.15)",
                    borderTopColor: "#1f6657",
                    borderRadius: "50%",
                    animation: "spin 0.8s linear infinite",
                }}
            />
            {message && (
                <p
                    style={{
                        margin: 0,
                        fontSize: "0.9rem",
                        color: "#425751",
                        fontWeight: 500,
                    }}
                >
                    {message}
                </p>
            )}
            <style>{`
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}
