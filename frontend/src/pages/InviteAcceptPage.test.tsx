import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import InviteAcceptPage from "./InviteAcceptPage";

vi.mock("../api/auth", () => ({
    resolveInvite: vi.fn(),
    acceptInvite: vi.fn(),
}));

import { acceptInvite, resolveInvite } from "../api/auth";

function renderPage(path: string) {
    return render(
        <MemoryRouter initialEntries={[path]}>
            <Routes>
                <Route path="/invite/:token" element={<InviteAcceptPage />} />
            </Routes>
        </MemoryRouter>
    );
}

describe("InviteAcceptPage", () => {
    it("shows invited email as locked field", async () => {
        vi.mocked(resolveInvite).mockResolvedValue({
            email: "invited@example.com",
            name: "Invited User",
            role: "owner",
            expires_at: new Date(Date.now() + 86_400_000).toISOString(),
        });

        renderPage("/invite/token-abc");

        const emailField = await screen.findByLabelText("Invited Email");
        expect(emailField).toHaveValue("invited@example.com");
        expect(emailField).toBeDisabled();
    });

    it("submits password and accepts invite", async () => {
        vi.mocked(resolveInvite).mockResolvedValue({
            email: "invited@example.com",
            name: "Invited User",
            role: "owner",
            expires_at: new Date(Date.now() + 86_400_000).toISOString(),
        });
        vi.mocked(acceptInvite).mockResolvedValue({
            message: "Invite accepted. Your account is active.",
            user: {
                id: 5,
                name: "Invited User",
                email: "invited@example.com",
                username: "invited",
                role: "owner",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: 1,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        });

        renderPage("/invite/token-abc");

        await screen.findByLabelText("Invited Email");
        fireEvent.change(screen.getByLabelText("Password"), { target: { value: "invited-pass-123" } });
        fireEvent.change(screen.getByLabelText("Confirm Password"), { target: { value: "invited-pass-123" } });
        fireEvent.click(screen.getByRole("button", { name: "Activate account" }));

        await waitFor(() => {
            expect(acceptInvite).toHaveBeenCalledWith("token-abc", "invited-pass-123");
        });
    });
});
