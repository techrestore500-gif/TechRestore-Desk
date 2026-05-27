import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { fetchCustomers, fetchTickets } from "../api/tickets";
import IntakePage from "./IntakePage";

vi.mock("../api/tickets", () => ({
    fetchCustomers: vi.fn(),
    fetchTickets: vi.fn(),
    createQuickRepair: vi.fn(),
}));

describe("IntakePage", () => {
    it("renders quick intake fields and customer suggestions", async () => {
        vi.mocked(fetchTickets).mockResolvedValue([]);
        vi.mocked(fetchCustomers).mockResolvedValue([
            {
                id: 4,
                full_name: "Alex Rivera",
                primary_phone: "555-9080",
                alternate_phone: null,
                email: null,
                notes: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        ]);

        render(
            <MemoryRouter>
                <IntakePage />
            </MemoryRouter>
        );

        expect(screen.getByText("Quick New Repair")).toBeInTheDocument();
        expect(screen.getByLabelText("Issue/problem")).toBeInTheDocument();

        fireEvent.change(screen.getByLabelText("Customer name"), { target: { value: "Al" } });

        await waitFor(() => {
            expect(fetchCustomers).toHaveBeenCalledWith("Al");
        });

        expect(await screen.findByText("Alex Rivera")).toBeInTheDocument();
    });
});
