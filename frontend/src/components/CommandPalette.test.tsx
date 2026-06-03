import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { useUiStore } from "../store/uiStore";
import { CommandPalette } from "./CommandPalette";

vi.mock("../hooks/queries/useGlobalSearchQuery", () => ({
    useGlobalSearchQuery: () => ({
        data: [
            { id: 1, type: "ticket", label: "TR-001", subtitle: "Customer · New Intake", path: "/tickets/1" },
        ],
        isLoading: false,
    }),
}));

describe("CommandPalette", () => {
    it("renders search results when opened", () => {
        const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
        useUiStore.setState({ commandPaletteOpen: true, commandPaletteQuery: "TR" });

        render(
            <QueryClientProvider client={client}>
                <MemoryRouter>
                    <CommandPalette />
                </MemoryRouter>
            </QueryClientProvider>
        );

        expect(screen.getByPlaceholderText("Search tickets and parts...")).toBeInTheDocument();
        expect(screen.getByText("TR-001")).toBeInTheDocument();

        fireEvent.keyDown(window, { key: "Escape" });
    });
});
