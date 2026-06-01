import { useMemo, useState } from "react";

import {
    fetchInventoryPurchases,
    type InventoryMovement,
    type InventoryPurchase,
    type Part,
} from "../api/inventory";
import { LoadingBoundary } from "../components/LoadingBoundary";
import { PageHeader } from "../components/PageChrome";
import { useAsyncData } from "../hooks/useAsyncData";
import { useCreatePartMutation, useDeletePartMutation, useUpdatePartMutation } from "../hooks/mutations/useInventoryMutations";
import { useInventoryMovementsQuery, useLowStockPartsQuery, usePartUsageQuery, usePartsQuery } from "../hooks/queries/useInventoryQueries";
import { useUiStore } from "../store/uiStore";
import * as t from "../styles/theme";

const PART_STATUSES = ["In Stock", "Low Stock", "Ordered", "Backordered", "Discontinued", "Donor Only"];

export function InventoryPage() {
    const [selectedPartId, setSelectedPartId] = useState<number | null>(null);
    const [actionError, setActionError] = useState<string | null>(null);
    const inventoryFilters = useUiStore((state) => state.inventoryFilters);
    const setInventoryFilters = useUiStore((state) => state.setInventoryFilters);
    const inventoryPagination = useUiStore((state) => state.inventoryPagination);
    const setInventoryPagination = useUiStore((state) => state.setInventoryPagination);

    const [partNumber, setPartNumber] = useState("");
    const [partName, setPartName] = useState("");
    const [category, setCategory] = useState("Battery");
    const [quantityOnHand, setQuantityOnHand] = useState("0");
    const [reorderLevel, setReorderLevel] = useState("5");
    const [cost, setCost] = useState("");
    const [supplier, setSupplier] = useState("");
    const [notes, setNotes] = useState("");

    const { data: purchaseData } = useAsyncData<{ items: InventoryPurchase[] }>(async () => fetchInventoryPurchases(), []);

    const partsQuery = usePartsQuery({
        category: inventoryFilters.category || undefined,
        status: inventoryFilters.status || undefined,
        lowStockOnly: inventoryFilters.lowStockOnly,
    });
    const lowStockQuery = useLowStockPartsQuery();
    const movementsQuery = useInventoryMovementsQuery({
        page: inventoryPagination.page,
        pageSize: inventoryPagination.pageSize,
        partId: selectedPartId ?? undefined,
    });

    const createPartMutation = useCreatePartMutation();
    const updatePartMutation = useUpdatePartMutation();
    const deletePartMutation = useDeletePartMutation();

    const parts = partsQuery.data ?? [];
    const lowStockCount = lowStockQuery.data?.length ?? 0;

    const categories = useMemo(() => {
        const set = new Set(parts.map((part) => part.category));
        return Array.from(set).sort();
    }, [parts]);

    const selectedPart = useMemo(
        () => parts.find((part) => part.id === selectedPartId) ?? null,
        [parts, selectedPartId]
    );

    const { data: selectedPartUsage = [] } = usePartUsageQuery(selectedPartId);

    const usageByPartId = useMemo(() => {
        const nextMap: Record<number, typeof selectedPartUsage> = {};
        if (selectedPartId && selectedPartUsage.length > 0) {
            nextMap[selectedPartId] = selectedPartUsage;
        }
        return nextMap;
    }, [selectedPartId, selectedPartUsage]);

    const visibleError = actionError ?? (partsQuery.error instanceof Error ? partsQuery.error.message : null);

    const handleApplyFilters = (event: React.FormEvent) => {
        event.preventDefault();
        setInventoryPagination({ page: 1 });
    };

    const handleCreatePart = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!partNumber || !partName || !category) {
            setActionError("Part number, part name, and category are required.");
            return;
        }
        try {
            setActionError(null);
            await createPartMutation.mutateAsync({
                part_number: partNumber,
                part_name: partName,
                category,
                quantity_on_hand: Number(quantityOnHand),
                reorder_level: Number(reorderLevel),
                cost: cost ? Number(cost) : undefined,
                supplier: supplier || undefined,
                notes: notes || undefined,
            });
            setPartNumber("");
            setPartName("");
            setQuantityOnHand("0");
            setSupplier("");
            setNotes("");
            setCost("");
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to create part");
        }
    };

    const handleMarkDiscontinued = async (partId: number) => {
        if (!window.confirm("Mark this part as discontinued? It will no longer be available for active stock usage.")) {
            return;
        }
        try {
            setActionError(null);
            await deletePartMutation.mutateAsync(partId);
            if (selectedPartId === partId) {
                setSelectedPartId(null);
            }
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update part");
        }
    };

    const handleQuickStockAdjust = async (part: Part, delta: number) => {
        const nextQty = Math.max(0, part.quantity_on_hand + delta);
        try {
            setActionError(null);
            await updatePartMutation.mutateAsync({ partId: part.id, payload: { quantity_on_hand: nextQty } });
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update stock");
        }
    };

    const mutating = createPartMutation.isPending || updatePartMutation.isPending || deletePartMutation.isPending;

    const selectedPartLastUsed = selectedPartUsage.length > 0 ? selectedPartUsage[0].created_at : null;

    return (
        <section style={{ ...t.pageWrap, gap: "20px" }}>
            <PageHeader
                kicker="Inventory"
                title="Inventory"
                description={
                    <>
                        Track parts, stock movements, purchases, and low-stock risk.
                        {lowStockCount > 0 ? <strong style={{ color: "#b03a2e", marginLeft: "10px" }}>{lowStockCount} low-stock {lowStockCount === 1 ? "item" : "items"}</strong> : null}
                    </>
                }
            />

            {visibleError && (
                <div style={{ padding: "10px 14px", background: "#fde8e8", color: "#9b2c2c", border: "1px solid #f8b4b4", borderRadius: "12px", marginBottom: "8px" }}>
                    Error: {visibleError}
                </div>
            )}

            <div style={{ ...t.detailGrid, gap: "1.5rem", marginBottom: "1.5rem" }}>
                <div style={panelCardStyle}>
                    <h3 style={{ marginTop: 0 }}>Parts filters</h3>
                    <form onSubmit={handleApplyFilters} style={{ ...t.formStack, gap: "0.75rem" }}>
                        <select value={inventoryFilters.category} onChange={(e) => setInventoryFilters({ category: e.target.value })} style={inputStyle}>
                            <option value="">All categories</option>
                            {categories.map((item) => (
                                <option key={item} value={item}>{item}</option>
                            ))}
                        </select>
                        <select value={inventoryFilters.status} onChange={(e) => setInventoryFilters({ status: e.target.value })} style={inputStyle}>
                            <option value="">All statuses</option>
                            {PART_STATUSES.map((item) => (
                                <option key={item} value={item}>{item}</option>
                            ))}
                        </select>
                        <label style={{ ...t.formActionsRow, gap: "0.5rem" }}>
                            <input
                                type="checkbox"
                                checked={inventoryFilters.lowStockOnly}
                                onChange={(e) => setInventoryFilters({ lowStockOnly: e.target.checked })}
                            />
                            Low stock only
                        </label>
                        <button type="submit" style={buttonStyle}>Apply Filters</button>
                    </form>
                </div>

                <div style={panelCardStyle}>
                    <h3 style={{ marginTop: 0 }}>Add part</h3>
                    <form onSubmit={handleCreatePart} style={{ ...t.formStack, gap: "0.65rem" }}>
                        <input placeholder="Part number" value={partNumber} onChange={(e) => setPartNumber(e.target.value)} style={inputStyle} />
                        <input placeholder="Part name" value={partName} onChange={(e) => setPartName(e.target.value)} style={inputStyle} />
                        <input placeholder="Category" value={category} onChange={(e) => setCategory(e.target.value)} style={inputStyle} />
                        <input placeholder="Qty on hand" value={quantityOnHand} onChange={(e) => setQuantityOnHand(e.target.value)} type="number" min="0" style={inputStyle} />
                        <input placeholder="Reorder level" value={reorderLevel} onChange={(e) => setReorderLevel(e.target.value)} type="number" min="0" style={inputStyle} />
                        <input placeholder="Cost" value={cost} onChange={(e) => setCost(e.target.value)} type="number" min="0" step="0.01" style={inputStyle} />
                        <input placeholder="Supplier" value={supplier} onChange={(e) => setSupplier(e.target.value)} style={inputStyle} />
                        <input placeholder="Notes" value={notes} onChange={(e) => setNotes(e.target.value)} style={inputStyle} />
                        <button type="submit" disabled={mutating} style={buttonStyle}>{mutating ? "Saving..." : "Add Part"}</button>
                    </form>
                </div>
            </div>

            <div style={{ ...t.detailGrid, gap: "1.5rem" }}>
                <div style={{ overflowX: "auto", borderRadius: "12px", boxShadow: "0 10px 24px rgba(26, 46, 41, 0.08)" }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", backgroundColor: "white", border: "1px solid #d7e0df" }}>
                        <thead style={{ backgroundColor: "#1f4a41", color: "#f7f5ee" }}>
                            <tr>
                                <th style={thStyle}>Part</th>
                                <th style={thStyle}>Category</th>
                                <th style={thStyle}>Status</th>
                                <th style={thStyle}>Qty</th>
                                <th style={thStyle}>Cost</th>
                                <th style={thStyle}>Reorder</th>
                                <th style={thStyle}>Last Used</th>
                                <th style={thStyle}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {partsQuery.isLoading ? (
                                <tr><td style={tdStyle} colSpan={8}>Loading...</td></tr>
                            ) : parts.length === 0 ? (
                                <tr><td style={tdStyle} colSpan={8}>No parts found.</td></tr>
                            ) : (
                                parts.map((part) => {
                                    const isLow = part.quantity_on_hand <= part.reorder_level;
                                    const isSelected = selectedPart?.id === part.id;
                                    const partUsage = usageByPartId[part.id] ?? [];
                                    const lastUsed = partUsage.length > 0
                                        ? new Date(partUsage[0].created_at).toLocaleString()
                                        : "Never";
                                    return (
                                        <tr
                                            key={part.id}
                                            style={{ backgroundColor: isSelected ? "#e8f5f2" : isLow ? "#fff1ed" : "white", cursor: "pointer" }}
                                            onClick={() => setSelectedPartId(part.id)}
                                        >
                                            <td style={tdStyle}><strong>{part.part_number}</strong><div style={{ color: "#7f8c8d" }}>{part.part_name}</div></td>
                                            <td style={tdStyle}>{part.category}</td>
                                            <td style={tdStyle}>{part.status}</td>
                                            <td style={tdStyle}>{part.quantity_on_hand}</td>
                                            <td style={tdStyle}>{part.cost != null ? `$${Number(part.cost).toFixed(2)}` : "-"}</td>
                                            <td style={tdStyle}>{part.reorder_level}</td>
                                            <td style={tdStyle}>{lastUsed}</td>
                                            <td style={tdStyle}>
                                                <div style={{ ...t.formActionsRow, gap: "0.5rem" }}>
                                                    <button style={smallButtonStyle} type="button" onClick={(event) => { event.stopPropagation(); setSelectedPartId(part.id); }}>Usage</button>
                                                    <button style={smallButtonStyle} type="button" onClick={(event) => { event.stopPropagation(); handleQuickStockAdjust(part, 1); }}>Add stock</button>
                                                    <button style={smallButtonStyle} type="button" onClick={(event) => { event.stopPropagation(); handleQuickStockAdjust(part, -1); }}>Use part</button>
                                                    <button style={smallDangerStyle} type="button" onClick={(event) => { event.stopPropagation(); handleMarkDiscontinued(part.id); }}>Discontinue</button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                <div style={usagePanelStyle}>
                    <h3 style={{ marginTop: 0 }}>Usage inspector</h3>
                    {!selectedPart ? (
                        <p style={{ color: "#576963" }}>Choose a part from the table to inspect where it has been used.</p>
                    ) : (
                        <>
                            <div style={{ marginBottom: "0.8rem" }}>
                                <strong>{selectedPart.part_number}</strong>
                                <div style={{ color: "#425751", marginTop: "0.25rem" }}>{selectedPart.part_name}</div>
                                <div style={{ color: "#7f8c8d", marginTop: "0.35rem", fontSize: "0.92rem" }}>
                                    Qty on hand: {selectedPart.quantity_on_hand} · Reorder at: {selectedPart.reorder_level}
                                </div>
                            </div>

                            <div style={{ ...t.formStack, gap: "0.5rem", marginBottom: "1rem" }}>
                                <div style={usageStatStyle}>
                                    <span>Total usage events</span>
                                    <strong>{selectedPartUsage.length}</strong>
                                </div>
                                <div style={usageStatStyle}>
                                    <span>Total units consumed</span>
                                    <strong>{selectedPartUsage.reduce((sum, usage) => sum + usage.quantity_used, 0)}</strong>
                                </div>
                                <div style={usageStatStyle}>
                                    <span>Last used</span>
                                    <strong>{selectedPartLastUsed ? new Date(selectedPartLastUsed).toLocaleString() : "Never"}</strong>
                                </div>
                            </div>

                            <h4 style={{ margin: "0 0 0.6rem" }}>Recent usage</h4>
                            {selectedPartUsage.length === 0 ? (
                                <p style={{ color: "#576963" }}>No repair actions have consumed this part yet.</p>
                            ) : (
                                <div style={{ ...t.formStack, gap: "0.6rem" }}>
                                    {selectedPartUsage.slice(0, 5).map((usage) => (
                                        <div key={usage.id} style={usageRowStyle}>
                                            <strong>Ticket #{usage.ticket_id ?? "-"}</strong>
                                            <div style={{ color: "#425751", marginTop: "0.25rem" }}>Repair action #{usage.repair_action_id}</div>
                                            <div style={{ color: "#576963", marginTop: "0.25rem" }}>
                                                Qty {usage.quantity_used} · {new Date(usage.created_at).toLocaleString()}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}
                </div>

                <div style={usagePanelStyle}>
                    <h3 style={{ marginTop: 0 }}>Movements</h3>
                    <p style={{ color: "#576963" }}>
                        Operational trace of stock mutations and donor harvest effects.
                    </p>
                    <LoadingBoundary
                        loading={movementsQuery.isLoading}
                        error={movementsQuery.error instanceof Error ? movementsQuery.error.message : null}
                        loadingMessage="Loading movement ledger..."
                    >
                        {(movementsQuery.data?.items ?? []).length === 0 ? (
                            <p style={{ color: "#576963" }}>No movement records yet.</p>
                        ) : (
                            <div style={{ ...t.formStack, gap: "0.6rem" }}>
                                {(movementsQuery.data?.items ?? []).map((movement: InventoryMovement) => (
                                    <div key={movement.id} style={usageRowStyle}>
                                        <strong>{movement.movement_type}</strong>
                                        <div style={{ color: "#425751", marginTop: "0.25rem" }}>
                                            Qty {movement.quantity} · Part #{movement.part_id ?? "-"}
                                        </div>
                                        <div style={{ color: "#576963", marginTop: "0.25rem" }}>
                                            {movement.reason ?? "No reason"} · {new Date(movement.created_at).toLocaleString()}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                        <div style={{ ...t.formActionsRow, marginTop: "10px", justifyContent: "space-between" }}>
                            <button
                                type="button"
                                onClick={() => setInventoryPagination({ page: Math.max(1, inventoryPagination.page - 1) })}
                                disabled={inventoryPagination.page <= 1}
                            >
                                Prev
                            </button>
                            <span>Page {inventoryPagination.page}</span>
                            <button
                                type="button"
                                onClick={() => setInventoryPagination({ page: inventoryPagination.page + 1 })}
                                disabled={
                                    !movementsQuery.data ||
                                    inventoryPagination.page * inventoryPagination.pageSize >= movementsQuery.data.total
                                }
                            >
                                Next
                            </button>
                        </div>
                    </LoadingBoundary>
                </div>

                <div style={usagePanelStyle}>
                    <h3 style={{ marginTop: 0 }}>Purchases</h3>
                    <p style={{ color: "#576963" }}>
                        Shop acquisition batches with quantities, unit costs, and batch totals.
                    </p>
                    {purchaseData?.items.length ? (
                        <div style={{ ...t.formStack, gap: "0.75rem" }}>
                            {purchaseData.items.map((purchase) => (
                                <div key={purchase.id} style={usageRowStyle}>
                                    <strong>{purchase.purchase_date}</strong>
                                    <div style={{ color: "#425751", marginTop: "0.25rem" }}>
                                        Total ${Number(purchase.total_cost).toFixed(2)}{purchase.vendor ? ` · ${purchase.vendor}` : ""}
                                    </div>
                                    <div style={{ color: "#576963", marginTop: "0.35rem" }}>
                                        {purchase.items.map((item) => `${item.quantity}x ${item.item_name} @ $${Number(item.estimated_unit_cost ?? 0).toFixed(2)}`).join(" · ")}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p style={{ color: "#576963" }}>No purchase batches recorded yet.</p>
                    )}
                </div>
            </div>
        </section>
    );
}

const inputStyle = {
    ...t.input,
    width: "100%",
    minWidth: 0,
    padding: "0.58rem 0.62rem",
    border: "1px solid #bfd0cb",
    borderRadius: "8px",
    boxSizing: "border-box" as const,
    backgroundColor: "#ffffff",
    color: "#19352f",
};

const buttonStyle = {
    padding: "0.58rem 0.9rem",
    background: "linear-gradient(145deg, #1f6657 0%, #184e42 100%)",
    color: "white",
    border: "none",
    borderRadius: "999px",
    cursor: "pointer",
    fontWeight: 700,
    letterSpacing: "0.01em",
    boxShadow: "0 8px 16px rgba(23, 70, 60, 0.2)",
};

const smallButtonStyle = {
    ...buttonStyle,
    padding: "0.3rem 0.5rem",
    fontSize: "0.8rem",
};

const smallDangerStyle = {
    ...smallButtonStyle,
    background: "linear-gradient(145deg, #b83e2f 0%, #9b3024 100%)",
};

const panelCardStyle = {
    background: "linear-gradient(145deg, rgba(255,255,255,0.88) 0%, rgba(243,249,247,0.88) 100%)",
    border: "1px solid rgba(28, 63, 56, 0.12)",
    padding: "1rem",
    borderRadius: "12px",
    boxShadow: "0 10px 20px rgba(20, 44, 38, 0.08)",
};

const usagePanelStyle = {
    background: "linear-gradient(145deg, #f8fcfb 0%, #eef5f3 100%)",
    border: "1px solid #ccddd8",
    borderRadius: "12px",
    padding: "1rem",
    boxShadow: "0 10px 20px rgba(21, 43, 39, 0.08)",
};

const usageStatStyle = {
    display: "flex",
    justifyContent: "space-between",
    gap: "1rem",
    padding: "0.6rem 0.75rem",
    backgroundColor: "white",
    borderRadius: "6px",
    border: "1px solid #e3eaef",
};

const usageRowStyle = {
    padding: "0.75rem",
    backgroundColor: "white",
    borderRadius: "6px",
    border: "1px solid #e3eaef",
};

const thStyle = { padding: "0.72rem", textAlign: "left" as const, borderBottom: "1px solid rgba(255,255,255,0.22)", fontSize: "0.9rem" };
const tdStyle = { padding: "0.72rem", borderBottom: "1px solid #ebf1ef", verticalAlign: "top" as const };
