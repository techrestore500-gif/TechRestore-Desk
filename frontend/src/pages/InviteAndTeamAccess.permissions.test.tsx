import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import InviteCreatePage from "./InviteCreatePage";
import AccessRequestsPage from "./AccessRequestsPage";
import { RequireRole } from "../components/RequireRole";

vi.mock("../auth/AuthProvider", () => ({
    useAuth: vi.fn(),
}));

vi.mock("../api/auth", () => ({
    createInvite: vi.fn(),
    fetchUsers: vi.fn(),
    fetchInvites: vi.fn(),
    resendInvite: vi.fn(),
    revokeInvite: vi.fn(),
}));

import { useAuth } from "../auth/AuthProvider";
import { fetchInvites, fetchUsers } from "../api/auth";

function makeUser(role: "owner" | "admin" | "manager" | "technician" | "front_desk" | "viewer") {
    return {
        id: 1,
        name: `${role} user`,
        email: `${role}@example.com`,
        username: role,
        role,
        status: "active" as const,
        is_active: true,
        approved_at: new Date().toISOString(),
        approved_by: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
    };
}

function renderRoutes(path: "/invite-create" | "/users-invites") {
    render(
        <MemoryRouter initialEntries={[path]}>
            <Routes>
                <Route
                    path="/invite-create"
                    element={
                        <RequireRole
                            allowedRoles={["owner", "admin"]}
                            deniedTitle="Invite access is restricted"
                            deniedDescription="Only owner/admin roles can create staff invites."
                        >
                            <InviteCreatePage />
                        </RequireRole>
                    }
                />
                <Route
                    path="/users-invites"
                    element={
                        <RequireRole
                            allowedRoles={["owner"]}
                            deniedTitle="Team access is owner-only"
                            deniedDescription="Only the owner can manage invites and roles."
                        >
                            <AccessRequestsPage />
                        </RequireRole>
                    }
                />
            </Routes>
        </MemoryRouter>
    );
}

describe("Invite and Team Access permissions", () => {
    beforeEach(() => {
        vi.resetAllMocks();
        vi.mocked(fetchInvites).mockResolvedValue([]);
        vi.mocked(fetchUsers).mockResolvedValue([]);
    });

    it("owner can access full Team Access management", async () => {
        vi.mocked(useAuth).mockReturnValue({ user: makeUser("owner") } as never);

        renderRoutes("/users-invites");

        expect(await screen.findByText("Team Access")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Current users" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Pending invites" })).toBeInTheDocument();
    });

    it("admin can reach invite interface and only sees allowed invite role options", async () => {
        vi.mocked(useAuth).mockReturnValue({ user: makeUser("admin") } as never);

        renderRoutes("/invite-create");

        expect(await screen.findByText("Create Invite")).toBeInTheDocument();
        const options = screen.getAllByRole("option").map((option) => option.textContent);
        expect(options).toEqual(["viewer", "front_desk", "technician"]);
    });

    it("admin cannot access owner-only Team Access controls through direct navigation", async () => {
        vi.mocked(useAuth).mockReturnValue({ user: makeUser("admin") } as never);

        renderRoutes("/users-invites");

        expect(await screen.findByText("Team access is owner-only")).toBeInTheDocument();
        expect(screen.queryByText("Team Access")).not.toBeInTheDocument();
        expect(screen.queryByRole("button", { name: "Current users" })).not.toBeInTheDocument();
    });

    it("non-owner and non-admin roles cannot access invite management", async () => {
        vi.mocked(useAuth).mockReturnValue({ user: makeUser("viewer") } as never);

        renderRoutes("/invite-create");

        expect(await screen.findByText("Invite access is restricted")).toBeInTheDocument();
        expect(screen.queryByText("Create Invite")).not.toBeInTheDocument();
    });
});
