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
        <div style={headerShellStyle}>
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
    gap: "14px",
    flexWrap: "wrap",
};

const headerShellStyle: CSSProperties = {
    ...t.panel,
    padding: "18px 20px 16px",
    display: "grid",
    gap: "10px",
    background: "linear-gradient(150deg, rgba(255,255,255,0.9) 0%, rgba(233,246,245,0.82) 62%, rgba(241,232,216,0.86) 100%)",
    borderLeft: "5px solid #238f8a",
    position: "relative",
    overflow: "hidden",
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
    borderTop: "4px solid rgba(35, 143, 138, 0.72)",
};

const compactStyle: CSSProperties = {
    padding: "14px",
    borderRadius: "16px",
};

const toneStyles: Record<"default" | "soft" | "accent", CSSProperties> = {
    default: {},
    soft: {
        background: "linear-gradient(145deg, rgba(255,255,255,0.92) 0%, rgba(236,244,245,0.86) 100%)",
    },
    accent: {
        background: "linear-gradient(145deg, rgba(255,235,196,0.98) 0%, rgba(243,188,126,0.92) 100%)",
        borderTopColor: "rgba(228, 141, 55, 0.88)",
    },
};

const metricTileStyle: CSSProperties = {
    ...t.subCard,
    background: "linear-gradient(175deg, rgba(255,255,255,0.92) 0%, rgba(235,246,246,0.9) 100%)",
    border: "1px solid rgba(22, 48, 54, 0.13)",
    display: "grid",
    gap: "4px",
    boxShadow: "0 11px 20px rgba(18, 43, 49, 0.08)",
};

const metricLabelStyle: CSSProperties = {
    color: "#2b6d75",
    fontSize: "0.74rem",
    fontWeight: 800,
    letterSpacing: "0.1em",
    textTransform: "uppercase",
};

const metricValueStyle: CSSProperties = {
    color: "#113641",
    fontSize: "1.65rem",
    fontWeight: 800,
    lineHeight: 1.05,
};

const metricHintStyle: CSSProperties = {
    color: "#4f6670",
    fontSize: "0.84rem",
};

const stateStyles: Record<string, CSSProperties> = {
    info: {
        ...t.stateBanner,
    },
    success: {
        ...t.stateBanner,
        borderColor: "#8ce4cf",
        background: "#e6fbf3",
        color: "#0a6553",
    },
    warning: {
        ...t.stateBanner,
        borderColor: "#eeb877",
        background: "#fff0da",
        color: "#8a4a09",
    },
    error: {
        ...t.stateBanner,
        borderColor: "#f3a9a9",
        background: "#ffeaea",
        color: "#9d2929",
    },
};

const backLinkStyle: CSSProperties = {
    ...t.secondaryBtn,
    textDecoration: "none",
    display: "inline-flex",
    alignItems: "center",
};