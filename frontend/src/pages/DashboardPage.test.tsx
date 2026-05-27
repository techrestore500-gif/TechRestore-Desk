import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { fetchStatusWorkflowRules, fetchTickets } from "../api/tickets";
import DashboardPage from "./DashboardPage";

vi.mock("../api/tickets", () => ({
    fetchTickets: vi.fn(),
    fetchStatusWorkflowRules: vi.fn(),
    updateTicketStatus: vi.fn(),
}));

describe("DashboardPage", () => {
    it("renders service desk metrics and ticket cards", async () => {
        vi.mocked(fetchStatusWorkflowRules).mockResolvedValue({
            transitions: {
                "New Intake": ["Needs Diagnosis"],
                "Needs Diagnosis": ["Diagnosed"],
                Diagnosed: ["Ready for Repair"],
                "Ready for Repair": ["In Repair"],
                "In Repair": ["Ready for Pickup"],
                "Ready for Pickup": ["Picked Up / Closed"],
                "Picked Up / Closed": [],
            },
            guardrails: {
                enforce_no_active_loaner_for_ready_for_pickup: true,
                enforce_no_active_loaner_for_closed_statuses: true,
                enforce_final_price_for_ready_for_pickup: true,
                enforce_final_price_for_closed_paid_statuses: true,
            },
            updated_at: new Date().toISOString(),
        });

        vi.mocked(fetchTickets).mockResolvedValue([
            {
                id: 42,
                ticket_number: "TR-00042",
                customer_id: 5,
                customer_name: "Dashboard Customer",
                customer_phone: "555-3333",
                device_label: "Pixel 7",
                issue_category: "Charging Port",
                status: "Needs Diagnosis",
                intake_date: new Date().toISOString(),
                estimated_price: null,
                final_price: null,
                updated_at: new Date().toISOString(),
            },
        ]);

        render(
            <MemoryRouter>
                <DashboardPage />
            </MemoryRouter>
        );

        expect(await screen.findByText("Service Desk")).toBeInTheDocument();
        expect(screen.getByText("TR-00042")).toBeInTheDocument();
        expect(screen.getAllByText("Dashboard Customer").length).toBeGreaterThan(0);
        expect(screen.getByText("Active Repairs")).toBeInTheDocument();
    });
});
