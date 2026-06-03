import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { RequireRole } from "./RequireRole";

vi.mock("../auth/AuthProvider", () => ({
    useAuth: vi.fn(),
}));

import { useAuth } from "../auth/AuthProvider";

describe("RequireRole", () => {
    it("renders access denied for forbidden role", () => {
        vi.mocked(useAuth).mockReturnValue({
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

        render(
            <MemoryRouter>
                <RequireRole allowedRoles={["owner"]}>
                    <div>Owner area</div>
                </RequireRole>
            </MemoryRouter>
        );

        expect(screen.queryByText("Owner area")).not.toBeInTheDocument();
        expect(screen.getByText("You do not have access")).toBeInTheDocument();
    });

    it("renders children for allowed role", () => {
        vi.mocked(useAuth).mockReturnValue({
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

        render(
            <MemoryRouter>
                <RequireRole allowedRoles={["owner"]}>
                    <div>Owner area</div>
                </RequireRole>
            </MemoryRouter>
        );

        expect(screen.getByText("Owner area")).toBeInTheDocument();
    });
});
