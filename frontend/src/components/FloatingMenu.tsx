import { createPortal } from "react-dom";
import { type CSSProperties, type ReactNode, useEffect, useLayoutEffect, useRef, useState } from "react";

import * as t from "../styles/theme";

export interface FloatingMenuProps {
    open: boolean;
    anchorElement: HTMLElement | null;
    onClose: () => void;
    align?: "right" | "left";
    offset?: { x?: number; y?: number };
    style?: CSSProperties;
    children: ReactNode;
}

const TOOLTIP_MARGIN = 8;

function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
}

export function FloatingMenu({
    open,
    anchorElement,
    onClose,
    align = "right",
    offset = {},
    style,
    children,
}: FloatingMenuProps) {
    const menuRef = useRef<HTMLDivElement | null>(null);
    const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

    const updatePosition = (): void => {
        if (!anchorElement) {
            return;
        }

        const anchorRect = anchorElement.getBoundingClientRect();
        const menuEl = menuRef.current;
        const menuWidth = menuEl?.offsetWidth ?? 180;
        const menuHeight = menuEl?.offsetHeight ?? 0;
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let left = align === "right" ? anchorRect.right - menuWidth : anchorRect.left;
        left += offset.x ?? 0;
        left = clamp(left, TOOLTIP_MARGIN, viewportWidth - menuWidth - TOOLTIP_MARGIN);

        let top = anchorRect.bottom + (offset.y ?? 8);
        if (top + menuHeight > viewportHeight - TOOLTIP_MARGIN) {
            const aboveTop = anchorRect.top - menuHeight - (offset.y ?? 8);
            if (aboveTop >= TOOLTIP_MARGIN) {
                top = aboveTop;
            }
        }
        top = clamp(top, TOOLTIP_MARGIN, viewportHeight - menuHeight - TOOLTIP_MARGIN);

        setPosition({ top, left });
    };

    useLayoutEffect(() => {
        if (!open) {
            return;
        }

        updatePosition();
        // Delay a second measure in case the menu width changes after render.
        const frame = window.requestAnimationFrame(() => updatePosition());
        return () => {
            window.cancelAnimationFrame(frame);
        };
    }, [open, anchorElement, align, offset.x, offset.y]);

    useEffect(() => {
        if (!open) {
            return;
        }

        const handleDocumentMouseDown = (event: MouseEvent) => {
            const target = event.target as Node | null;
            if (!target) {
                return;
            }

            if (menuRef.current?.contains(target) || anchorElement?.contains(target)) {
                return;
            }

            onClose();
        };

        const handleDocumentKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                onClose();
            }
        };

        document.addEventListener("mousedown", handleDocumentMouseDown);
        document.addEventListener("keydown", handleDocumentKeyDown);
        window.addEventListener("resize", updatePosition);
        window.addEventListener("scroll", updatePosition, true);

        return () => {
            document.removeEventListener("mousedown", handleDocumentMouseDown);
            document.removeEventListener("keydown", handleDocumentKeyDown);
            window.removeEventListener("resize", updatePosition);
            window.removeEventListener("scroll", updatePosition, true);
        };
    }, [open, anchorElement, onClose, updatePosition]);

    if (!open || !anchorElement) {
        return null;
    }

    return createPortal(
        <div
            ref={menuRef}
            role="menu"
            style={{
                position: "fixed",
                top: position?.top ?? 0,
                left: position?.left ?? 0,
                minWidth: "180px",
                borderRadius: "10px",
                border: "1px solid rgba(29, 43, 40, 0.16)",
                background: "#ffffff",
                boxShadow: "0 16px 30px rgba(21, 40, 36, 0.16)",
                zIndex: t.zDropdown,
                display: "grid",
                padding: "6px",
                gap: "4px",
                ...style,
            }}
        >
            {children}
        </div>,
        document.body
    );
}
