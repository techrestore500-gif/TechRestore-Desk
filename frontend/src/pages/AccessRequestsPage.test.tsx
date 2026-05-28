import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AccessRequestsPage from "./AccessRequestsPage";

vi.mock("../api/auth", () => ({
    fetchAccessRequests: vi.fn(),
    approveAccessRequest: vi.fn(),
    denyAccessRequest: vi.fn(),
}));

import { approveAccessRequest, denyAccessRequest, fetchAccessRequests } from "../api/auth";

describe("AccessRequestsPage", () => {
    it("shows pending requests and allows approval", async () => {
        vi.mocked(fetchAccessRequests).mockResolvedValue([
            {
                id: 10,
                name: "Pending User",
                email: "pending@example.com",
                username: "pendinguser",
                status: "pending",
                created_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(approveAccessRequest).mockResolvedValue({
            message: "Access request approved",
            user: {
                id: 10,
                name: "Pending User",
                email: "pending@example.com",
                username: "pendinguser",
                role: "technician",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: 1,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        });

        render(<AccessRequestsPage />);

        expect(await screen.findByText("pending@example.com")).toBeInTheDocument();
        fireEvent.change(screen.getByRole("combobox"), { target: { value: "technician" } });
        fireEvent.click(screen.getByRole("button", { name: "Approve" }));

        await waitFor(() => {
            expect(approveAccessRequest).toHaveBeenCalledWith(10, "technician");
        });
    });

    it("allows denying a pending request", async () => {
        vi.mocked(fetchAccessRequests).mockResolvedValue([
            {
                id: 11,
                name: "Denied User",
                email: "denied@example.com",
                username: "denieduser",
                status: "pending",
                created_at: new Date().toISOString(),
            },
        ]);
        vi.mocked(denyAccessRequest).mockResolvedValue({
            message: "Access request denied",
            user: {
                id: 11,
                name: "Denied User",
                email: "denied@example.com",
                username: "denieduser",
                role: null,
                status: "denied",
                is_active: false,
                approved_at: null,
                approved_by: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        });

        render(<AccessRequestsPage />);

        expect(await screen.findByText("denied@example.com")).toBeInTheDocument();
        fireEvent.click(screen.getByRole("button", { name: "Deny" }));

        await waitFor(() => {
            expect(denyAccessRequest).toHaveBeenCalledWith(11);
        });
    });
});
