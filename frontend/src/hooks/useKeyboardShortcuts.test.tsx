import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import { useUiStore } from "../store/uiStore";
import { useKeyboardShortcuts } from "./useKeyboardShortcuts";

function Harness() {
    useKeyboardShortcuts();
    return null;
}

describe("useKeyboardShortcuts", () => {
    it("opens command palette on Ctrl+K", () => {
        useUiStore.setState({ commandPaletteOpen: false, commandPaletteQuery: "" });

        render(
            <MemoryRouter>
                <Harness />
            </MemoryRouter>
        );
        window.dispatchEvent(new KeyboardEvent("keydown", { key: "k", ctrlKey: true }));

        expect(useUiStore.getState().commandPaletteOpen).toBe(true);
    });
});
