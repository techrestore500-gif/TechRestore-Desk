import type { CSSProperties, ReactNode } from "react";
import { Link } from "react-router-dom";

import * as t from "../styles/theme";

export function PageHeader({
    kicker,
    title,
    description,
    actions,
}: {
    kicker?: string;
    title: string;
    description?: ReactNode;
    actions?: ReactNode;
}) {
    return (
        <div style={t.pageHeader}>
            {kicker ? <p style={t.pageKicker}>{kicker}</p> : null}
            <div style={headerRowStyle}>
                <div style={{ minWidth: 0 }}>
                    <h2 style={t.pageTitle}>{title}</h2>
                    {description ? <div style={t.pageDescription}>{description}</div> : null}
                </div>
                {actions ? <div style={actionsWrapStyle}>{actions}</div> : null}
            </div>
        </div>
    );
}

export function SectionCard({
    title,
    description,
    action,
    children,
    compact = false,
    tone = "default",
}: {
    title?: ReactNode;
    description?: ReactNode;
    action?: ReactNode;
    children: ReactNode;
    compact?: boolean;
    tone?: "default" | "soft" | "accent";
}) {
    return (
        <section style={{ ...baseSectionStyle, ...(compact ? compactStyle : null), ...(toneStyles[tone] ?? null) }}>
            {title || description || action ? (
                <div style={t.sectionHeader}>
                    <div>
                        {title ? <h3 style={t.sectionTitle}>{title}</h3> : null}
                        {description ? <div style={t.sectionMeta}>{description}</div> : null}
                    </div>
                    {action ? <div>{action}</div> : null}
                </div>
            ) : null}
            {children}
        </section>
    );
}

export function MetricTile({ label, value, hint }: { label: string; value: ReactNode; hint?: ReactNode }) {
    return (
        <div style={metricTileStyle}>
            <div style={metricLabelStyle}>{label}</div>
            <div style={metricValueStyle}>{value}</div>
            {hint ? <div style={metricHintStyle}>{hint}</div> : null}
        </div>
    );
}

export function InlineState({ tone = "info", children }: { tone?: "info" | "success" | "warning" | "error"; children: ReactNode }) {
    return <div style={{ ...stateStyles[tone] }}>{children}</div>;
}

export function BackLink({ to, children }: { to: string; children: ReactNode }) {
    return (
        <Link to={to} style={backLinkStyle}>
            {children}
        </Link>
    );
}

const headerRowStyle: CSSProperties = {
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: "12px",
    flexWrap: "wrap",
};

const actionsWrapStyle: CSSProperties = {
    display: "flex",
    gap: "8px",
    flexWrap: "wrap",
    alignItems: "center",
};

const baseSectionStyle: CSSProperties = {
    ...t.panel,
    display: "grid",
    gap: "12px",
};

const compactStyle: CSSProperties = {
    padding: "14px",
    borderRadius: "16px",
};

const toneStyles: Record<"default" | "soft" | "accent", CSSProperties> = {
    default: {},
    soft: {
        background: "linear-gradient(145deg, rgba(255,255,255,0.96) 0%, rgba(247,250,248,0.95) 100%)",
    },
    accent: {
        background: "linear-gradient(145deg, rgba(236,251,245,0.98) 0%, rgba(219,243,236,0.96) 100%)",
    },
};

const metricTileStyle: CSSProperties = {
    ...t.subCard,
    background: "rgba(255,255,255,0.86)",
    border: "1px solid rgba(29, 43, 40, 0.1)",
    display: "grid",
    gap: "4px",
};

const metricLabelStyle: CSSProperties = {
    color: "#5a7268",
    fontSize: "0.74rem",
    fontWeight: 800,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
};

const metricValueStyle: CSSProperties = {
    color: "#173f37",
    fontSize: "1.65rem",
    fontWeight: 800,
    lineHeight: 1.05,
};

const metricHintStyle: CSSProperties = {
    color: "#5d716b",
    fontSize: "0.84rem",
};

const stateStyles: Record<string, CSSProperties> = {
    info: {
        ...t.stateBanner,
    },
    success: {
        ...t.stateBanner,
        borderColor: "#a7f3d0",
        background: "#ecfdf5",
        color: "#065f46",
    },
    warning: {
        ...t.stateBanner,
        borderColor: "#f3c481",
        background: "#fff1dd",
        color: "#8a4b00",
    },
    error: {
        ...t.stateBanner,
        borderColor: "#f8b4b4",
        background: "#fde8e8",
        color: "#9b2c2c",
    },
};

const backLinkStyle: CSSProperties = {
    ...t.secondaryBtn,
    textDecoration: "none",
    display: "inline-flex",
    alignItems: "center",
};