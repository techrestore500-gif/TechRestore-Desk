/**
 * Shared visual tokens for Tech Restore Desk.
 * Import named exports and use directly as inline style objects.
 * Page-specific layout, grid, and structural styles stay local.
 */
import type { CSSProperties } from "react";

/** Standard content panel — frosted surface with angular geometry. */
export const panel: CSSProperties = {
    background: "linear-gradient(150deg, rgba(255,255,255,0.9) 0%, rgba(246,241,234,0.84) 100%)",
    border: "1px solid rgba(24, 42, 48, 0.15)",
    borderRadius: "22px",
    padding: "18px 19px",
    boxShadow: "0 16px 38px rgba(22, 41, 46, 0.12)",
    backdropFilter: "blur(8px)",
};

/** Primary action button — saturated cyan gradient with darker edge. */
export const primaryBtn: CSSProperties = {
    borderRadius: "12px",
    border: "1px solid rgba(9, 64, 67, 0.16)",
    background: "linear-gradient(145deg, #19a58f 0%, #13746f 55%, #0f4f53 100%)",
    color: "#f2fffc",
    padding: "11px 15px",
    cursor: "pointer",
    fontWeight: 750,
    letterSpacing: "0.01em",
    boxShadow: "0 11px 24px rgba(17, 83, 86, 0.26)",
    transition: "all 180ms ease",
};

/** Secondary / utility button — crisp neutral chip with quiet depth. */
export const secondaryBtn: CSSProperties = {
    borderRadius: "12px",
    border: "1px solid rgba(26, 51, 58, 0.2)",
    background: "rgba(255,255,255,0.78)",
    color: "#163740",
    padding: "11px 15px",
    cursor: "pointer",
    transition: "all 180ms ease",
};

/** Mini utility button — compact capsule for row actions. */
export const miniBtn: CSSProperties = {
    borderRadius: "10px",
    border: "1px solid rgba(20, 49, 56, 0.16)",
    background: "rgba(255,255,255,0.85)",
    color: "#173b44",
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
    border: "1px solid rgba(20, 52, 60, 0.17)",
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
    color: "#2e454c",
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
    color: "#55707a",
    fontSize: "0.9rem",
};

/** Error banner for inline page-level failures. */
export const errorBanner: CSSProperties = {
    padding: "10px 13px",
    background: "#ffefee",
    color: "#9a2929",
    border: "1px solid #f2b1ad",
    borderRadius: "12px",
};

/** Table shell for pages that still render dense record tables. */
export const tableShell: CSSProperties = {
    width: "100%",
    borderCollapse: "collapse",
    backgroundColor: "rgba(255,255,255,0.95)",
    border: "1px solid rgba(19,45,51,0.15)",
    borderRadius: "14px",
    overflow: "hidden",
    boxShadow: "0 14px 30px rgba(24, 45, 51, 0.11)",
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
    background: "linear-gradient(155deg, rgba(255,255,255,0.9) 0%, rgba(236,242,244,0.82) 100%)",
    padding: "12px 14px",
    border: "1px solid rgba(22, 49, 56, 0.1)",
};

/** Policy or constraint warning notice. */
export const warning: CSSProperties = {
    padding: "11px 13px",
    borderRadius: "12px",
    background: "#fff4df",
    color: "#81510f",
    border: "1px solid #eec57b",
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
    background: "linear-gradient(145deg, #195c67 0%, #123f4a 100%)",
    color: "#e8fbff",
    fontWeight: 700,
    boxShadow: "0 10px 18px rgba(14, 59, 67, 0.2)",
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
    color: "#245f67",
    fontSize: "0.72rem",
    fontWeight: 800,
    letterSpacing: "0.14em",
    textTransform: "uppercase",
};

export const pageTitle: CSSProperties = {
    margin: 0,
    color: "#102b33",
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
    color: "#143842",
};

export const sectionMeta: CSSProperties = {
    margin: 0,
    color: "#56707b",
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
    border: "1px solid rgba(29, 58, 67, 0.15)",
    background: "#ffffff",
    color: "#25434a",
};

// ─── Interactive state helpers (for onMouseEnter/onMouseLeave/onFocus) ───

/** Apply to input onFocus for visual feedback. */
export function applyInputFocus(element: HTMLElement | null) {
    if (!element) return;
    element.style.borderColor = "rgba(25, 135, 132, 0.44)";
    element.style.boxShadow = "0 0 0 3px rgba(25, 135, 132, 0.11)";
}

/** Reset input focus state. */
export function resetInputFocus(element: HTMLElement | null) {
    if (!element) return;
    element.style.borderColor = "rgba(29, 58, 67, 0.17)";
    element.style.boxShadow = "none";
}
