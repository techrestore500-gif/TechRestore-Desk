export const queryKeys = {
    tickets: (search: string) => ["tickets", { search }] as const,
    ticketsPaged: (args: { page: number; pageSize: number; search: string; status?: string }) =>
        ["tickets", "paged", args] as const,
    queue: () => ["queue"] as const,
    parts: (filters: { category?: string; status?: string; lowStockOnly?: boolean }) => ["parts", filters] as const,
    lowStock: () => ["parts", "low-stock"] as const,
    donors: () => ["donors"] as const,
    partUsage: (partId: number) => ["part-usage", partId] as const,
    inventoryMovements: (args: { page: number; pageSize: number; partId?: number; movementType?: string }) =>
        ["inventory-movements", args] as const,
};
