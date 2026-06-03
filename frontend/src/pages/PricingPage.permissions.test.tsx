import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import PricingPage from "./PricingPage";

vi.mock("../auth/AuthProvider", () => ({
    useAuth: vi.fn(),
}));

vi.mock("../api/pricingCatalog", () => ({
    fetchPricingCatalog: vi.fn(),
    createPricingBrand: vi.fn(),
    createPricingModel: vi.fn(),
    createPricingIssueType: vi.fn(),
    createPricingRepairType: vi.fn(),
    createPricingRule: vi.fn(),
    updatePricingRule: vi.fn(),
    deletePricingRule: vi.fn(),
    updatePricingBrand: vi.fn(),
    updatePricingModel: vi.fn(),
    updatePricingIssueType: vi.fn(),
    updatePricingRepairType: vi.fn(),
}));

import { useAuth } from "../auth/AuthProvider";
import { fetchPricingCatalog } from "../api/pricingCatalog";

describe("PricingPage permissions", () => {
    it("shows read-only mode for technician", async () => {
        vi.mocked(useAuth).mockReturnValue({
            user: {
                id: 3,
                name: "Tech User",
                email: "tech@example.com",
                username: "tech",
                role: "technician",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: 1,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        } as never);

        vi.mocked(fetchPricingCatalog).mockResolvedValue({
            brands: [],
            models: [],
            issue_types: [],
            repair_types: [],
            rules: [],
        });

        render(<PricingPage />);

        expect(await screen.findByText("Read-only mode: only owner/admin can edit pricing configuration.")).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Add brand" })).toBeDisabled();
    });
});
