import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { fetchTickets } from "../../api/tickets";
import { QueryTestProvider } from "../../test/queryTestUtils";
import { useTicketsQuery } from "./useTicketsQuery";

vi.mock("../../api/tickets", () => ({
    fetchTickets: vi.fn(),
}));

describe("useTicketsQuery", () => {
    it("loads ticket list for a query", async () => {
        vi.mocked(fetchTickets).mockResolvedValue([
            {
                id: 1,
                ticket_number: "TR-001",
                customer_id: 1,
                customer_name: "A",
                customer_phone: "555",
                device_label: "Phone",
                issue_category: "Screen",
                status: "New Intake",
                intake_date: new Date().toISOString(),
                estimated_price: null,
                final_price: null,
                updated_at: new Date().toISOString(),
            },
        ]);

        const { result } = renderHook(() => useTicketsQuery("TR"), {
            wrapper: QueryTestProvider,
        });

        await waitFor(() => {
            expect(result.current.isSuccess).toBe(true);
        });

        expect(fetchTickets).toHaveBeenCalledWith("TR");
        expect(result.current.data?.length).toBe(1);
    });
});
