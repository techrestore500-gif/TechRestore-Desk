import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { fetchStatusWorkflowRules, fetchTickets, updateTicketStatus } from "../api/tickets";
import DashboardPage from "./DashboardPage";

vi.mock("../api/tickets", () => ({
    fetchTickets: vi.fn(),
    fetchStatusWorkflowRules: vi.fn(),
    updateTicketStatus: vi.fn(),
}));

describe("DashboardPage", () => {
    it("shows only valid next status actions and formats customer phone", async () => {
        vi.mocked(fetchStatusWorkflowRules).mockResolvedValue({
            transitions: {
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
                id: 77,
                ticket_number: "TR-00077",
                customer_id: 11,
                customer_name: "Action Customer",
                customer_phone: "5554443333",
                device_label: "iPhone 13",
                issue_category: "Screen",
                status: "Needs Diagnosis",
                payment_status: "unpaid",
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

        const ticketNumber = await screen.findByText("TR-00077");
        const card = ticketNumber.closest("article");
        expect(card).not.toBeNull();
        expect(within(card as HTMLElement).queryByRole("button", { name: "Canceled" })).not.toBeInTheDocument();
        expect(screen.getByText("+1 555-444-3333")).toBeInTheDocument();
    });

    it("executes transition path for selected valid action", async () => {
        vi.mocked(fetchStatusWorkflowRules).mockResolvedValue({
            transitions: {
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
                id: 78,
                ticket_number: "TR-00078",
                customer_id: 12,
                customer_name: "Path Customer",
                customer_phone: "5550001111",
                device_label: "Pixel 8",
                issue_category: "Battery",
                status: "Needs Diagnosis",
                payment_status: "unpaid",
                intake_date: new Date().toISOString(),
                estimated_price: null,
                final_price: null,
                updated_at: new Date().toISOString(),
            },
        ]);

        vi.mocked(updateTicketStatus).mockResolvedValue({
            id: 1,
            ticket_id: 78,
            old_status: "Needs Diagnosis",
            new_status: "Diagnosed",
            changed_by: "",
            note: null,
            created_at: new Date().toISOString(),
        });

        render(
            <MemoryRouter>
                <DashboardPage />
            </MemoryRouter>
        );

        const ticketNumber = await screen.findByText("TR-00078");
        const card = ticketNumber.closest("article");
        expect(card).not.toBeNull();
        fireEvent.click(within(card as HTMLElement).getByRole("button", { name: "In Repair" }));

        await waitFor(() => expect(updateTicketStatus).toHaveBeenCalledTimes(3));
        expect(updateTicketStatus).toHaveBeenNthCalledWith(1, 78, "Diagnosed", "", "");
        expect(updateTicketStatus).toHaveBeenNthCalledWith(2, 78, "Ready for Repair", "", "");
        expect(updateTicketStatus).toHaveBeenNthCalledWith(3, 78, "In Repair", "", "");
    });

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
                payment_status: "unpaid",
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

        expect(await screen.findByText("What Needs Attention")).toBeInTheDocument();
        expect(await screen.findByText("TR-00042")).toBeInTheDocument();
        expect((await screen.findAllByText("Dashboard Customer")).length).toBeGreaterThan(0);
        expect(screen.getByText("Active Repairs")).toBeInTheDocument();
    });
});
