import { ReactNode } from "react";

interface PageHeaderProps {
    kicker?: string;
    title: string;
    description?: ReactNode;
}

export function PageHeader({ kicker, title, description }: PageHeaderProps) {
    return (
        <div style={{ marginBottom: "4px" }}>
            {kicker ? (
                <div style={{ fontSize: "0.68rem", letterSpacing: "0.14em", textTransform: "uppercase", color: "#5a7268", fontWeight: 700, marginBottom: "4px" }}>
                    {kicker}
                </div>
            ) : null}
            <h2 style={{ margin: "0 0 4px", fontSize: "1.45rem", fontWeight: 800, color: "#13312b", lineHeight: 1.2 }}>{title}</h2>
            {description ? (
                <p style={{ margin: 0, fontSize: "0.88rem", color: "#4d6760", lineHeight: 1.5 }}>{description}</p>
            ) : null}
        </div>
    );
}
