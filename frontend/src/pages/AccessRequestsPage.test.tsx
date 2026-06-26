import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AccessRequestsPage from "./AccessRequestsPage";

vi.mock("../api/auth", () => ({
    fetchUsers: vi.fn(),
    fetchInvites: vi.fn(),
    createInvite: vi.fn(),
    resendInvite: vi.fn(),
    revokeInvite: vi.fn(),
}));

import { createInvite, fetchInvites, fetchUsers, resendInvite, revokeInvite } from "../api/auth";

describe("AccessRequestsPage", () => {
    it("shows current users from users endpoint", async () => {
        vi.mocked(fetchUsers).mockResolvedValue([
            {
                id: 21,
                name: "Current User",
                email: "current@example.com",
                username: "current",
                role: "technician",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: 1,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(fetchInvites).mockResolvedValue([]);

        render(<AccessRequestsPage />);

        expect(await screen.findByText("current@example.com")).toBeInTheDocument();
        expect(screen.queryByText("No records for this filter.")).not.toBeInTheDocument();
    });

    it("shows pending invites and allows revocation", async () => {
        vi.spyOn(window, "confirm").mockReturnValue(true);
        vi.mocked(fetchUsers).mockResolvedValue([]);
        vi.mocked(fetchInvites).mockResolvedValue([
            {
                id: 10,
                name: "Pending User",
                email: "pending@example.com",
                role: "technician",
                status: "pending",
                expires_at: new Date(Date.now() + 86_400_000).toISOString(),
                created_at: new Date().toISOString(),
                created_by: 1,
                accepted_at: null,
                accepted_user_id: null,
                revoked_at: null,
            },
        ]);
        vi.mocked(revokeInvite).mockResolvedValue({
            id: 10,
            name: "Pending User",
            email: "pending@example.com",
            role: "technician",
            status: "revoked",
            expires_at: new Date(Date.now() + 86_400_000).toISOString(),
            created_at: new Date().toISOString(),
            created_by: 1,
            accepted_at: null,
            accepted_user_id: null,
            revoked_at: new Date().toISOString(),
        });

        render(<AccessRequestsPage />);

    fireEvent.click(screen.getByRole("button", { name: "Pending invites" }));
        expect(await screen.findByText("pending@example.com")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Revoke" }));

        await waitFor(() => {
            expect(revokeInvite).toHaveBeenCalledWith(10);
        });
    });

    it("re-sends pending invites", async () => {
        vi.mocked(fetchUsers).mockResolvedValue([]);
        vi.mocked(fetchInvites).mockResolvedValue([
            {
                id: 12,
                name: "Pending User",
                email: "pending@example.com",
                role: "admin",
                status: "pending",
                expires_at: new Date(Date.now() + 86_400_000).toISOString(),
                created_at: new Date().toISOString(),
                created_by: 1,
                accepted_at: null,
                accepted_user_id: null,
                revoked_at: null,
            },
        ]);
        vi.mocked(resendInvite).mockResolvedValue({
            id: 13,
            name: "Pending User",
            email: "pending@example.com",
            role: "admin",
            status: "pending",
            expires_at: new Date(Date.now() + 86_400_000).toISOString(),
            created_at: new Date().toISOString(),
            created_by: 1,
            accepted_at: null,
            accepted_user_id: null,
            revoked_at: null,
        });

        render(<AccessRequestsPage />);

    fireEvent.click(screen.getByRole("button", { name: "Pending invites" }));
        expect(await screen.findByText("pending@example.com")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Resend" }));

        await waitFor(() => {
            expect(resendInvite).toHaveBeenCalledWith(12);
        });
    });

    it("creates invite from form", async () => {
        vi.mocked(fetchUsers).mockResolvedValue([]);
        vi.mocked(fetchInvites).mockResolvedValue([]);
        vi.mocked(createInvite).mockResolvedValue({
            id: 11,
            name: "New User",
            email: "new@example.com",
            role: "viewer",
            status: "pending",
            expires_at: new Date(Date.now() + 86_400_000).toISOString(),
            created_at: new Date().toISOString(),
            created_by: 1,
            accepted_at: null,
            accepted_user_id: null,
            revoked_at: null,
        });

        render(<AccessRequestsPage />);

        fireEvent.change(await screen.findByLabelText("Name (optional)"), { target: { value: "New User" } });
        fireEvent.change(screen.getByLabelText("Email"), { target: { value: "new@example.com" } });
        fireEvent.change(screen.getByLabelText("Role"), { target: { value: "viewer" } });
        fireEvent.click(screen.getByRole("button", { name: "Send invite" }));

        await waitFor(() => {
            expect(createInvite).toHaveBeenCalledWith("new@example.com", "viewer", "New User");
        });
    });
});
