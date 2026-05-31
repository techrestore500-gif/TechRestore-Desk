/**
 * Shared visual tokens for Tech Restore Desk.
 * Import named exports and use directly as inline style objects.
 * Page-specific layout, grid, and structural styles stay local.
 */
import type { CSSProperties } from "react";

/** Standard content panel — soft gradient card with shadow. */
export const panel: CSSProperties = {
    background: "linear-gradient(145deg, rgba(255, 255, 255, 0.92) 0%, rgba(243, 249, 247, 0.88) 100%)",
    border: "1px solid rgba(29, 43, 40, 0.12)",
    borderRadius: "20px",
    padding: "16px 18px",
    boxShadow: "0 10px 20px rgba(22, 49, 42, 0.08)",
};

/** Primary action button — deep green gradient pill. */
export const primaryBtn: CSSProperties = {
    borderRadius: "999px",
    border: "none",
    background: "linear-gradient(145deg, #1f6657 0%, #184e42 100%)",
    color: "#f5efe3",
    padding: "9px 18px",
    cursor: "pointer",
    fontWeight: 700,
    boxShadow: "0 6px 12px rgba(23, 70, 60, 0.18)",
    transition: "all 180ms ease",
};

/** Secondary / utility button — white pill with thin border. */
export const secondaryBtn: CSSProperties = {
    borderRadius: "999px",
    border: "1px solid rgba(29, 43, 40, 0.18)",
    background: "#ffffff",
    color: "#1d2b28",
    padding: "9px 18px",
    cursor: "pointer",
    transition: "all 180ms ease",
};

/** Mini utility button — compact pill for quick-action rows. */
export const miniBtn: CSSProperties = {
    borderRadius: "999px",
    border: "1px solid rgba(29, 43, 40, 0.12)",
    background: "#ffffff",
    color: "#1d2b28",
    padding: "6px 11px",
    fontSize: "0.83rem",
    cursor: "pointer",
    transition: "background-color 160ms ease, border-color 160ms ease, transform 160ms ease",
};

/** Standard text input / select / textarea. */
export const input: CSSProperties = {
    width: "100%",
    maxWidth: "100%",
    minWidth: 0,
    padding: "9px 12px",
    borderRadius: "12px",
    border: "1px solid rgba(29, 43, 40, 0.18)",
    background: "#ffffff",
    fontSize: "1rem",
    fontFamily: '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
    transition: "border-color 160ms ease, box-shadow 160ms ease",
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
    lineHeight: 1.6,
    color: "#425751",
};

/** Page intro copy — consistent spacing for page-level helper text. */
export const pageIntro: CSSProperties = {
    ...copy,
    marginTop: "4px",
    marginBottom: 0,
    fontSize: "0.9rem",
};

/** Small metadata line — muted color and slightly reduced size. */
export const meta: CSSProperties = {
    marginTop: "6px",
    color: "#576963",
    fontSize: "0.92rem",
};

/** Error banner for inline page-level failures. */
export const errorBanner: CSSProperties = {
    padding: "9px 14px",
    background: "#fde8e8",
    color: "#9b2c2c",
    border: "1px solid #f8b4b4",
    borderRadius: "12px",
};

/** Success banner for confirmations and saved states. */
export const successBanner: CSSProperties = {
    padding: "9px 14px",
    background: "#e8f6ee",
    color: "#1f6a3f",
    border: "1px solid #b3dfc4",
    borderRadius: "12px",
};

/** Inline muted notice — for tips, explanations, non-critical info. */
export const notice: CSSProperties = {
    padding: "9px 14px",
    background: "rgba(240,242,239,0.8)",
    color: "#465954",
    border: "1px solid rgba(29,43,40,0.1)",
    borderRadius: "12px",
    fontSize: "0.88rem",
};

/** Section divider line within a panel. */
export const sectionDivider: CSSProperties = {
    border: "none",
    borderTop: "1px solid rgba(29,43,40,0.08)",
    margin: "16px 0",
};

/** Table shell for pages that still render dense record tables. */
export const tableShell: CSSProperties = {
    width: "100%",
    borderCollapse: "collapse",
    backgroundColor: "white",
    border: "1px solid #d7e0df",
    borderRadius: "12px",
    overflow: "hidden",
    boxShadow: "0 10px 24px rgba(26, 46, 41, 0.08)",
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
    borderRadius: "14px",
    background: "#f6f1e8",
    padding: "10px 14px",
};

/** Policy or constraint warning notice. */
export const warning: CSSProperties = {
    padding: "12px 14px",
    borderRadius: "12px",
    background: "#fff1dd",
    color: "#8a4b00",
    border: "1px solid #f3c481",
};

/** Section heading — removes top margin. */
export const heading: CSSProperties = {
    marginTop: 0,
    marginBottom: "14px",
};

/** Status badge pill — used on ticket header and other prominent status displays. */
export const statusBadge: CSSProperties = {
    alignSelf: "start",
    borderRadius: "999px",
    padding: "7px 14px",
    background: "linear-gradient(145deg, #1f6657 0%, #184e42 100%)",
    color: "#f5efe3",
    fontWeight: 700,
    boxShadow: "0 4px 10px rgba(23, 70, 60, 0.16)",
};

/** Responsive auto-fit grid for detail panels. */
export const detailGrid: CSSProperties = {
    display: "grid",
    gap: "18px 20px",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    alignItems: "start",
};

/** Responsive auto-fit grid for form fields. */
export const fieldGrid: CSSProperties = {
    display: "grid",
    gap: "16px 18px",
    gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
    alignItems: "start",
};

/** Two-column form grid with desktop pairing and mobile-safe stacking. */
export const fieldGridTwo: CSSProperties = {
    display: "grid",
    gap: "14px 18px",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    alignItems: "start",
};

/** Compact two-column grid for settings rows with short controls. */
export const fieldGridTwoCompact: CSSProperties = {
    display: "grid",
    gap: "12px 16px",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
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
    gap: "16px",
    width: "100%",
    maxWidth: "1280px",
    margin: "0 auto",
    minWidth: 0,
};

// ─── Interactive state helpers (for onMouseEnter/onMouseLeave/onFocus) ───

/** Apply to input onFocus for visual feedback. */
export function applyInputFocus(element: HTMLElement | null) {
    if (!element) return;
    element.style.borderColor = "rgba(31, 102, 87, 0.4)";
    element.style.boxShadow = "0 0 0 3px rgba(31, 102, 87, 0.08)";
}

/** Reset input focus state. */
export function resetInputFocus(element: HTMLElement | null) {
    if (!element) return;
    element.style.borderColor = "rgba(29, 43, 40, 0.18)";
    element.style.boxShadow = "none";
}
