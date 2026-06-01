/**
 * Inventory, parts, donor devices, and purchase records API.
 *
 * Previously these functions were misplaced in api/tickets.ts.
 */

import { apiFetch, getJson } from "./client";

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
    const response = await apiFetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }

    return (await response.json()) as TResponse;
}

async function patchJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
    const response = await apiFetch(path, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }

    return (await response.json()) as TResponse;
}

async function deleteRequest(path: string): Promise<void> {
    const response = await apiFetch(path, { method: "DELETE" });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
}

// ─── Types ────────────────────────────────────────────────────────────────────

export type Part = {
    id: number;
    part_number: string;
    part_name: string;
    category: string;
    device_compatibility: string | null;
    supplier: string | null;
    cost: number | null;
    retail_price: number | null;
    status: string;
    quantity_on_hand: number;
    quantity_ordered: number;
    reorder_level: number;
    reorder_quantity: number;
    notes: string | null;
    created_at: string;
    updated_at: string;
};

export type DonorDevice = {
    id: number;
    device_identifier: string;
    device_model: string;
    status: string;
    condition_notes: string | null;
    parts_harvested: number[];
    parts_available: number[];
    acquisition_date: string | null;
    retirement_date: string | null;
    created_at: string;
    updated_at: string;
};

export type PartUsage = {
    id: number;
    repair_action_id: number;
    part_id: number;
    quantity_used: number;
    created_at: string;
    part_number: string;
    part_name: string;
    category: string | null;
    ticket_id?: number | null;
};

export type InventoryMovement = {
    id: number;
    part_id: number | null;
    donor_id: number | null;
    movement_type: string;
    quantity: number;
    reason: string | null;
    ticket_id: number | null;
    repair_action_id: number | null;
    actor_user_id: number | null;
    request_id: string | null;
    metadata: Record<string, unknown> | null;
    created_at: string;
};

export type InventoryMovementPage = {
    items: InventoryMovement[];
    total: number;
    page: number;
    page_size: number;
};

export type InventoryReconciliation = {
    id: number;
    part_id: number;
    expected_quantity: number;
    actual_quantity: number;
    discrepancy: number;
    reason: string;
    resolved_by: string | null;
    created_at: string;
};

export type InventoryPurchaseItem = {
    id: number;
    purchase_id: number;
    item_type: string;
    manufacturer: string | null;
    item_name: string;
    quantity: number;
    estimated_unit_cost: number | null;
    line_total: number | null;
    notes: string | null;
    created_at: string;
    updated_at: string;
};

export type InventoryPurchase = {
    id: number;
    purchase_date: string;
    vendor: string | null;
    reference_number: string | null;
    total_cost: number;
    notes: string | null;
    items: InventoryPurchaseItem[];
    created_at: string;
    updated_at: string;
};

export type InventoryPurchaseList = {
    items: InventoryPurchase[];
};

// ─── Parts ────────────────────────────────────────────────────────────────────

export async function fetchParts(filters?: {
    category?: string;
    status?: string;
    lowStockOnly?: boolean;
}): Promise<Part[]> {
    const params = new URLSearchParams();
    if (filters?.category) params.set("category", filters.category);
    if (filters?.status) params.set("status", filters.status);
    if (filters?.lowStockOnly) params.set("low_stock_only", "true");
    const query = params.toString();
    return getJson<Part[]>(`/api/inventory/parts${query ? `?${query}` : ""}`);
}

export async function createPart(payload: {
    part_number: string;
    part_name: string;
    category: string;
    device_compatibility?: string;
    supplier?: string;
    cost?: number;
    status?: string;
    quantity_on_hand?: number;
    reorder_level?: number;
    notes?: string;
}): Promise<Part> {
    return postJson<Part>("/api/inventory/parts", payload);
}

export async function updatePart(partId: number, payload: Partial<Part>): Promise<Part> {
    return patchJson<Part>(`/api/inventory/parts/${partId}`, payload);
}

export async function deletePart(partId: number): Promise<void> {
    await deleteRequest(`/api/inventory/parts/${partId}`);
}

export async function fetchLowStockParts(): Promise<Part[]> {
    return getJson<Part[]>("/api/inventory/low-stock");
}

export async function fetchPartUsage(partId: number): Promise<PartUsage[]> {
    return getJson<PartUsage[]>(`/api/inventory/parts/${partId}/usage`);
}

export async function fetchRepairActionPartUsage(repairActionId: number): Promise<PartUsage[]> {
    return getJson<PartUsage[]>(`/api/inventory/repair-actions/${repairActionId}/parts`);
}

export async function logPartUsage(payload: {
    repair_action_id: number;
    part_id: number;
    quantity_used: number;
}): Promise<PartUsage> {
    return postJson<PartUsage>("/api/inventory/parts/usage", payload);
}

export async function adjustPartStock(
    partId: number,
    payload: {
        quantity_delta: number;
        movement_type: "adjust" | "transfer" | "return" | "correction";
        reason: string;
        ticket_id?: number;
    },
): Promise<Part> {
    return postJson<Part>(`/api/inventory/parts/${partId}/adjust`, payload);
}

// ─── Donor devices ────────────────────────────────────────────────────────────

export async function fetchDonors(filters?: { status?: string; deviceModel?: string }): Promise<DonorDevice[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.set("status", filters.status);
    if (filters?.deviceModel) params.set("device_model", filters.deviceModel);
    const query = params.toString();
    return getJson<DonorDevice[]>(`/api/inventory/donors${query ? `?${query}` : ""}`);
}

export async function createDonor(payload: {
    device_identifier: string;
    device_model: string;
    condition_notes?: string;
    status?: string;
    acquisition_date?: string;
}): Promise<DonorDevice> {
    return postJson<DonorDevice>("/api/inventory/donors", payload);
}

export async function updateDonor(donorId: number, payload: Partial<DonorDevice>): Promise<DonorDevice> {
    return patchJson<DonorDevice>(`/api/inventory/donors/${donorId}`, payload);
}

export async function harvestPartFromDonor(donorId: number, partId: number): Promise<DonorDevice> {
    return postJson<DonorDevice>(`/api/inventory/donors/${donorId}/harvest`, { part_id: partId });
}

// ─── Inventory movements ──────────────────────────────────────────────────────

export async function fetchInventoryMovements(filters: {
    page: number;
    pageSize: number;
    partId?: number;
    movementType?: string;
}): Promise<InventoryMovementPage> {
    const params = new URLSearchParams();
    params.set("page", String(filters.page));
    params.set("page_size", String(filters.pageSize));
    if (filters.partId) params.set("part_id", String(filters.partId));
    if (filters.movementType) params.set("movement_type", filters.movementType);
    return getJson<InventoryMovementPage>(`/api/inventory/movements?${params.toString()}`);
}

export async function reconcilePartStock(payload: {
    part_id: number;
    actual_quantity: number;
    reason: string;
    apply_adjustment?: boolean;
    resolved_by?: string;
}): Promise<InventoryReconciliation> {
    return postJson<InventoryReconciliation>("/api/inventory/reconciliation", payload);
}

export async function fetchInventoryReconciliations(partId?: number): Promise<InventoryReconciliation[]> {
    const params = new URLSearchParams();
    if (partId) params.set("part_id", String(partId));
    const suffix = params.toString();
    return getJson<InventoryReconciliation[]>(`/api/inventory/reconciliation${suffix ? `?${suffix}` : ""}`);
}

// ─── Purchases ────────────────────────────────────────────────────────────────

export async function fetchInventoryPurchases(): Promise<InventoryPurchaseList> {
    return getJson<InventoryPurchaseList>("/api/inventory/purchases");
}
