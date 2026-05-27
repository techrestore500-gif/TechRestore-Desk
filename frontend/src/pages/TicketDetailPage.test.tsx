import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { fetchRepairActionPartUsage, fetchStatusWorkflowRules, fetchTicket } from "../api/tickets";
import TicketDetailPage from "./TicketDetailPage";

vi.mock("../api/tickets", () => ({
    fetchTicket: vi.fn(),
    fetchStatusWorkflowRules: vi.fn(),
    fetchRepairActionPartUsage: vi.fn(),
    addTicketNote: vi.fn(),
    updateTicketStatus: vi.fn(),
}));

describe("TicketDetailPage", () => {
    it("loads core detail sections for repair workflow", async () => {
        vi.mocked(fetchTicket).mockResolvedValue({
            id: 9,
            ticket_number: "TR-00009",
            customer_id: 3,
            customer_name: "Detail Customer",
            customer_phone: "555-4444",
            customer_alternate_phone: null,
            device_model_id: 1,
            device_model_text_override: null,
            device_label: "Pixel 8",
            carrier: null,
            sim_type: null,
            imei_serial: null,
            device_color: null,
            filter_status: null,
            issue_category: "Battery",
            issue_description: "Battery drains fast",
            condition_summary: null,
            water_damage_status: "unknown",
            dropped_status: "unknown",
            powers_on_status: "yes",
            charges_status: "yes",
            customer_approval_limit: null,
            must_call_before_repair: false,
            customer_prefers_replacement_if_high: false,
            estimated_price: 89,
            final_price: null,
            diagnostic_fee: 0,
            status: "Needs Diagnosis",
            priority: "normal",
            intake_staff: null,
            assigned_technician: null,
            intake_date: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            history: [],
            notes: [],
            repair_actions: [
                {
                    id: 101,
                    ticket_id: 9,
                    repair_category_id: 2,
                    repair_category_name: "Battery",
                    action_description: "Replace battery",
                    part_cost: 12,
                    labor_minutes: 30,
                    difficulty_level: 2,
                    risk_level: 1,
                    calculated_price: 89,
                    final_price: null,
                    status: "logged",
                    performed_by: null,
                    performed_at: null,
                    requires_soldering: false,
                },
            ],
        });

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

        vi.mocked(fetchRepairActionPartUsage).mockResolvedValue([]);

        render(
            <MemoryRouter initialEntries={["/tickets/9"]}>
                <Routes>
                    <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
                </Routes>
            </MemoryRouter>
        );

        expect(await screen.findByText("TR-00009")).toBeInTheDocument();
        expect(screen.getByText("One-Click Status")).toBeInTheDocument();
        expect(screen.getByText("Repair Notes (append-only log)")).toBeInTheDocument();
        expect(screen.getByText("Timeline / Status History")).toBeInTheDocument();
    });
});
