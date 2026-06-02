/**
 * Shared visual tokens for Tech Restore Desk.
 * Import named exports and use directly as inline style objects.
 * Page-specific layout, grid, and structural styles stay local.
 */
import type { CSSProperties } from "react";

/** Standard content panel — frosted surface with angular geometry. */
export const panel: CSSProperties = {
    background: "linear-gradient(150deg, rgba(255,255,255,0.92) 0%, rgba(240,245,255,0.86) 100%)",
    border: "1px solid rgba(28, 52, 94, 0.15)",
    borderRadius: "22px",
    padding: "18px 19px",
    boxShadow: "0 16px 38px rgba(21, 42, 82, 0.13)",
    backdropFilter: "blur(8px)",
};

/** Primary action button — saturated cyan gradient with darker edge. */
export const primaryBtn: CSSProperties = {
    borderRadius: "12px",
    border: "1px solid rgba(29, 66, 138, 0.2)",
    background: "linear-gradient(145deg, var(--brand-600) 0%, #285ed0 55%, var(--brand-700) 100%)",
    color: "#f4f8ff",
    padding: "11px 15px",
    cursor: "pointer",
    fontWeight: 750,
    letterSpacing: "0.01em",
    boxShadow: "0 11px 24px rgba(33, 75, 184, 0.28)",
    transition: "all 180ms ease",
};

/** Secondary / utility button — crisp neutral chip with quiet depth. */
export const secondaryBtn: CSSProperties = {
    borderRadius: "12px",
    border: "1px solid rgba(38, 66, 118, 0.2)",
    background: "rgba(255,255,255,0.78)",
    color: "#1b2f54",
    padding: "11px 15px",
    cursor: "pointer",
    transition: "all 180ms ease",
};

/** Mini utility button — compact capsule for row actions. */
export const miniBtn: CSSProperties = {
    borderRadius: "10px",
    border: "1px solid rgba(35, 62, 111, 0.16)",
    background: "rgba(255,255,255,0.85)",
    color: "#1d335e",
    padding: "7px 10px",
    cursor: "pointer",
    fontWeight: 650,
    transition: "background-color 160ms ease, border-color 160ms ease, transform 160ms ease",
};

/** Standard text input / select / textarea. */
export const input: CSSProperties = {
    width: "100%",
    maxWidth: "100%",
    minWidth: 0,
    padding: "11px 13px",
    borderRadius: "11px",
    border: "1px solid rgba(37, 65, 117, 0.2)",
    background: "rgba(255,255,255,0.95)",
    fontSize: "1rem",
    fontFamily: '"Sora", "Plus Jakarta Sans", "Avenir Next", "Segoe UI", sans-serif',
    transition: "border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease",
};

/** Form field label wrapper — stacked grid with bold label text. */
export const label: CSSProperties = {
    display: "grid",
    gap: "8px",
    fontWeight: 600,
    minWidth: 0,
};

/** Body copy — readable line-height and muted green tone. */
export const copy: CSSProperties = {
    lineHeight: 1.58,
    color: "#30466d",
};

/** Page intro copy — consistent spacing for page-level helper text. */
export const pageIntro: CSSProperties = {
    ...copy,
    marginTop: "4px",
    marginBottom: 0,
    fontSize: "0.93rem",
};

/** Small metadata line — muted color and slightly reduced size. */
export const meta: CSSProperties = {
    marginTop: "6px",
    color: "#4f6793",
    fontSize: "0.9rem",
};

/** Error banner for inline page-level failures. */
export const errorBanner: CSSProperties = {
    padding: "10px 13px",
    background: "var(--danger-soft)",
    color: "var(--danger-ink)",
    border: "1px solid var(--danger-line)",
    borderRadius: "12px",
};

/** Table shell for pages that still render dense record tables. */
export const tableShell: CSSProperties = {
    width: "100%",
    borderCollapse: "collapse",
    backgroundColor: "rgba(255,255,255,0.95)",
    border: "1px solid rgba(29, 56, 104, 0.16)",
    borderRadius: "14px",
    overflow: "hidden",
    boxShadow: "0 14px 30px rgba(31, 56, 107, 0.12)",
};

export const tableHeaderCell: CSSProperties = {
    padding: "0.75rem",
    textAlign: "left",
    borderBottom: "1px solid rgba(255,255,255,0.22)",
};

export const tableCell: CSSProperties = {
    padding: "0.75rem",
};

/** Inline sub-card for history items, notes, and usage rows. */
export const subCard: CSSProperties = {
    borderRadius: "16px",
    background: "linear-gradient(155deg, rgba(255,255,255,0.93) 0%, rgba(233,241,255,0.84) 100%)",
    padding: "12px 14px",
    border: "1px solid rgba(30, 58, 104, 0.1)",
};

/** Policy or constraint warning notice. */
export const warning: CSSProperties = {
    padding: "11px 13px",
    borderRadius: "12px",
    background: "#fff2ea",
    color: "#8b4221",
    border: "1px solid #f1b494",
};

/** Section heading — removes top margin. */
export const heading: CSSProperties = {
    marginTop: 0,
    marginBottom: "14px",
};

/** Status badge pill — used on ticket header and other prominent status displays. */
export const statusBadge: CSSProperties = {
    alignSelf: "start",
    borderRadius: "11px",
    padding: "8px 12px",
    background: "linear-gradient(145deg, var(--brand-600) 0%, var(--brand-700) 100%)",
    color: "#eef4ff",
    fontWeight: 700,
    boxShadow: "0 10px 18px rgba(33, 75, 184, 0.22)",
};

/** Responsive auto-fit grid for detail panels. */
export const detailGrid: CSSProperties = {
    display: "grid",
    gap: "16px 18px",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    alignItems: "start",
};

/** Responsive auto-fit grid for form fields. */
export const fieldGrid: CSSProperties = {
    display: "grid",
    gap: "14px 16px",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    alignItems: "start",
};

/** Two-column form grid with desktop pairing and mobile-safe stacking. */
export const fieldGridTwo: CSSProperties = {
    display: "grid",
    gap: "13px 16px",
    gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
    alignItems: "start",
};

/** Compact two-column grid for settings rows with short controls. */
export const fieldGridTwoCompact: CSSProperties = {
    display: "grid",
    gap: "10px 14px",
    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
    alignItems: "start",
};

/** Vertical stack for form sections and card content. */
export const formStack: CSSProperties = {
    display: "grid",
    gap: "12px",
    minWidth: 0,
};

/** Inline action row that wraps cleanly and avoids overflow clipping. */
export const formActionsRow: CSSProperties = {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
    alignItems: "center",
    minWidth: 0,
};

/** Page-level wrapper — fills the main content column with a vertical grid. */
export const pageWrap: CSSProperties = {
    display: "grid",
    gap: "18px",
    width: "100%",
    maxWidth: "1240px",
    margin: "0 auto",
    minWidth: 0,
    animation: "riseIn 280ms ease",
};

export const pageHeader: CSSProperties = {
    display: "grid",
    gap: "6px",
};

export const pageKicker: CSSProperties = {
    margin: 0,
    color: "#2f64c5",
    fontSize: "0.72rem",
    fontWeight: 800,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
};

export const pageTitle: CSSProperties = {
    margin: 0,
    color: "#11264a",
    lineHeight: 1.03,
    fontSize: "1.9rem",
    fontWeight: 800,
};

export const pageDescription: CSSProperties = {
    ...copy,
    margin: 0,
    fontSize: "0.96rem",
};

export const sectionHeader: CSSProperties = {
    display: "flex",
    alignItems: "baseline",
    justifyContent: "space-between",
    gap: "10px",
    flexWrap: "wrap",
    marginBottom: "12px",
};

export const sectionTitle: CSSProperties = {
    margin: 0,
    fontSize: "1.06rem",
    color: "#1b315a",
};

export const sectionMeta: CSSProperties = {
    margin: 0,
    color: "#4b6693",
    fontSize: "0.85rem",
};

export const compactSurface: CSSProperties = {
    ...panel,
    padding: "14px",
    borderRadius: "18px",
};

export const stateBanner: CSSProperties = {
    padding: "10px 13px",
    borderRadius: "11px",
    border: "1px solid rgba(29, 58, 112, 0.16)",
    background: "#ffffff",
    color: "#2c4a76",
};

// ─── Interactive state helpers (for onMouseEnter/onMouseLeave/onFocus) ───

/** Apply to input onFocus for visual feedback. */
export function applyInputFocus(element: HTMLElement | null) {
    if (!element) return;
    element.style.borderColor = "rgba(47, 111, 237, 0.45)";
    element.style.boxShadow = "0 0 0 3px rgba(47, 111, 237, 0.12)";
}

/** Reset input focus state. */
export function resetInputFocus(element: HTMLElement | null) {
    if (!element) return;
    element.style.borderColor = "rgba(37, 65, 117, 0.2)";
    element.style.boxShadow = "none";
}
