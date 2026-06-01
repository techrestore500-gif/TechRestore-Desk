import { useQuery } from "@tanstack/react-query";

import {
    fetchDonors,
    fetchInventoryMovements,
    fetchLowStockParts,
    fetchPartUsage,
    fetchParts,
} from "../../api/inventory";
import { queryKeys } from "../queryKeys";

export function usePartsQuery(filters: { category?: string; status?: string; lowStockOnly?: boolean }) {
    return useQuery({
        queryKey: queryKeys.parts(filters),
        queryFn: () => fetchParts(filters),
    });
}

export function useLowStockPartsQuery() {
    return useQuery({
        queryKey: queryKeys.lowStock(),
        queryFn: fetchLowStockParts,
    });
}

export function useDonorsQuery() {
    return useQuery({
        queryKey: queryKeys.donors(),
        queryFn: () => fetchDonors(),
    });
}

export function usePartUsageQuery(partId: number | null) {
    return useQuery({
        queryKey: queryKeys.partUsage(partId ?? -1),
        queryFn: () => fetchPartUsage(partId as number),
        enabled: partId !== null,
    });
}

export function useInventoryMovementsQuery(args: { page: number; pageSize: number; partId?: number; movementType?: string }) {
    return useQuery({
        queryKey: queryKeys.inventoryMovements(args),
        queryFn: () => fetchInventoryMovements(args),
        placeholderData: (previous) => previous,
    });
}
