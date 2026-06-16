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

    it("counts only completed unpaid tickets as unpaid repairs", async () => {
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
                id: 101,
                ticket_number: "TR-00101",
                customer_id: 21,
                customer_name: "Closed Unpaid",
                customer_phone: "5551112222",
                device_label: "Phone A",
                issue_category: "Screen",
                status: "Picked Up / Closed",
                payment_status: "unpaid",
                intake_date: new Date().toISOString(),
                estimated_price: null,
                final_price: 25,
                updated_at: new Date().toISOString(),
            },
            {
                id: 102,
                ticket_number: "TR-00102",
                customer_id: 22,
                customer_name: "Open Unpaid",
                customer_phone: "5553334444",
                device_label: "Phone B",
                issue_category: "Battery",
                status: "In Repair",
                payment_status: "unpaid",
                intake_date: new Date().toISOString(),
                estimated_price: null,
                final_price: 50,
                updated_at: new Date().toISOString(),
            },
            {
                id: 103,
                ticket_number: "TR-00103",
                customer_id: 23,
                customer_name: "Closed Paid",
                customer_phone: "5555556666",
                device_label: "Phone C",
                issue_category: "Port",
                status: "Picked Up / Closed",
                payment_status: "paid",
                intake_date: new Date().toISOString(),
                estimated_price: null,
                final_price: 40,
                updated_at: new Date().toISOString(),
            },
        ]);

        render(
            <MemoryRouter>
                <DashboardPage />
            </MemoryRouter>
        );

        await screen.findByText("TR-00101");
        const unpaidMetric = await screen.findByText("Unpaid Repairs");
        expect(unpaidMetric.parentElement?.parentElement).toHaveTextContent("1");
    });
});
