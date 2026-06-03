import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { AppShell } from "./AppShell";

vi.mock("../auth/AuthProvider", () => ({
    useAuth: vi.fn(),
}));

vi.mock("../hooks/useKeyboardShortcuts", () => ({
    useKeyboardShortcuts: vi.fn(),
}));

vi.mock("./CommandPalette", () => ({
    CommandPalette: () => null,
}));

import { useAuth } from "../auth/AuthProvider";

function renderShell(path = "/") {
    const client = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
    });

    return render(
        <QueryClientProvider client={client}>
            <MemoryRouter initialEntries={[path]}>
                <Routes>
                    <Route path="/" element={<AppShell />}>
                        <Route index element={<div>Dashboard body</div>} />
                        <Route path="settings" element={<div>Settings body</div>} />
                        <Route path="users-invites" element={<div>Invites body</div>} />
                    </Route>
                </Routes>
            </MemoryRouter>
        </QueryClientProvider>
    );
}

describe("AppShell role navigation", () => {
    it("shows Team Access only for owner", async () => {
        vi.mocked(useAuth).mockReturnValue({
            authEnabled: true,
            isAuthenticated: true,
            logout: vi.fn(),
            user: {
                id: 1,
                name: "Owner User",
                email: "owner@example.com",
                username: "owner",
                role: "owner",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        } as never);

        renderShell();

        expect(await screen.findByText("Team Access")).toBeInTheDocument();
        expect(screen.getByText("Settings")).toBeInTheDocument();
    });

    it("hides Team Access for admin", async () => {
        vi.mocked(useAuth).mockReturnValue({
            authEnabled: true,
            isAuthenticated: true,
            logout: vi.fn(),
            user: {
                id: 2,
                name: "Admin User",
                email: "admin@example.com",
                username: "admin",
                role: "admin",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: 1,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        } as never);

        renderShell();

        expect(await screen.findByText("Dashboard body")).toBeInTheDocument();
        expect(screen.queryByText("Team Access")).not.toBeInTheDocument();
        expect(screen.getByText("Settings")).toBeInTheDocument();
    });

    it("hides Settings and Team Access for technician", async () => {
        vi.mocked(useAuth).mockReturnValue({
            authEnabled: true,
            isAuthenticated: true,
            logout: vi.fn(),
            user: {
                id: 3,
                name: "Tech User",
                email: "tech@example.com",
                username: "tech",
                role: "technician",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: 1,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        } as never);

        renderShell();

        expect(await screen.findByText("Dashboard body")).toBeInTheDocument();
        expect(screen.queryByText("Team Access")).not.toBeInTheDocument();
        expect(screen.queryByText("Settings")).not.toBeInTheDocument();
    });
});
