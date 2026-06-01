import { useState } from "react";
import { useAsyncData } from "../hooks/useAsyncData";
import { PageHeader } from "../components/PageChrome";
import * as t from "../styles/theme";

import {
    createDonor,
    fetchDonors,
    fetchParts,
    harvestPartFromDonor,
    updateDonor,
    type DonorDevice,
    type Part,
} from "../api/inventory";

export function DonorsPage() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [actionLoading, setActionLoading] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);

    const [identifier, setIdentifier] = useState("");
    const [model, setModel] = useState("");
    const [conditionNotes, setConditionNotes] = useState("");
    const [harvestPartId, setHarvestPartId] = useState<Record<number, string>>({});
    const [availablePartId, setAvailablePartId] = useState<Record<number, string>>({});

    const { data, loading, error: loadError } = useAsyncData<{ donors: DonorDevice[]; parts: Part[] }>(
        async () => {
            const [donorItems, partItems] = await Promise.all([fetchDonors(), fetchParts()]);
            return { donors: donorItems, parts: partItems };
        },
        [refreshKey]
    );

    const donors = data?.donors ?? [];
    const parts = data?.parts ?? [];
    const error = actionError ?? loadError;

    function triggerRefresh() {
        setRefreshKey((current) => current + 1);
    }

    const handleAddDonor = async (event: React.FormEvent) => {
        event.preventDefault();
        if (!identifier || !model) {
            setActionError("Device identifier and model are required.");
            return;
        }
        try {
            setActionLoading(true);
            setActionError(null);
            await createDonor({
                device_identifier: identifier,
                device_model: model,
                condition_notes: conditionNotes || undefined,
                acquisition_date: new Date().toISOString().split("T")[0],
            });
            setIdentifier("");
            setModel("");
            setConditionNotes("");
            triggerRefresh();
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to create donor");
        } finally {
            setActionLoading(false);
        }
    };

    const handleHarvest = async (donorId: number) => {
        const value = harvestPartId[donorId];
        if (!value) {
            setActionError("Choose a part before harvesting.");
            return;
        }
        try {
            setActionLoading(true);
            setActionError(null);
            await harvestPartFromDonor(donorId, Number(value));
            setHarvestPartId((prev) => ({ ...prev, [donorId]: "" }));
            triggerRefresh();
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to harvest part");
        } finally {
            setActionLoading(false);
        }
    };

    const handleAddAvailablePart = async (donor: DonorDevice) => {
        const value = availablePartId[donor.id];
        if (!value) {
            setActionError("Choose a part to mark as available on donor.");
            return;
        }

        const partId = Number(value);
        if (donor.parts_harvested.includes(partId)) {
            setActionError("This part is already harvested for this donor.");
            return;
        }
        if (donor.parts_available.includes(partId)) {
            setActionError("This part is already marked available for this donor.");
            return;
        }

        try {
            setActionLoading(true);
            setActionError(null);
            await updateDonor(donor.id, {
                parts_available: [...donor.parts_available, partId],
            });
            setAvailablePartId((prev) => ({ ...prev, [donor.id]: "" }));
            triggerRefresh();
        } catch (err) {
            setActionError(err instanceof Error ? err.message : "Failed to update available parts");
        } finally {
            setActionLoading(false);
        }
    };

    const getPartLabel = (partId: number) => {
        const part = parts.find((item) => item.id === partId);
        if (!part) {
            return `Part #${partId}`;
        }
        return `${part.part_number} - ${part.part_name}`;
    };

    const getHarvestOptions = (donor: DonorDevice) => {
        if (donor.parts_available.length > 0) {
            return donor.parts_available
                .map((id) => parts.find((part) => part.id === id))
                .filter((part): part is Part => !!part);
        }

        return parts.filter((part) => !donor.parts_harvested.includes(part.id));
    };

    const grouped = {
        "Available for Parts": donors.filter((d) => d.status === "Available for Parts"),
        "Partially Harvested": donors.filter((d) => d.status === "Partially Harvested"),
        "Fully Harvested": donors.filter((d) => d.status === "Fully Harvested"),
        "Retired/Discarded": donors.filter((d) => d.status === "Retired/Discarded"),
    };

    return (
        <section style={{ ...t.pageWrap, gap: "20px" }}>
            <PageHeader
                kicker="Parts Harvesting"
                title="Donor Devices"
                description="Track donor lifecycle and harvested parts for inventory support."
            />

            {error && (
                <div style={{ padding: "10px 14px", background: "#fde8e8", color: "#9b2c2c", border: "1px solid #f8b4b4", borderRadius: "12px", marginBottom: "8px" }}>
                    Error: {error}
                </div>
            )}

            <div style={panelCardStyle}>
                <h3 style={{ marginTop: 0 }}>Add Donor Device</h3>
                <form onSubmit={handleAddDonor} style={{ display: "grid", gap: "0.65rem" }}>
                    <input placeholder="Device identifier (ex: Donor-E4810-001)" value={identifier} onChange={(e) => setIdentifier(e.target.value)} style={inputStyle} />
                    <input placeholder="Device model" value={model} onChange={(e) => setModel(e.target.value)} style={inputStyle} />
                    <input placeholder="Condition notes" value={conditionNotes} onChange={(e) => setConditionNotes(e.target.value)} style={inputStyle} />
                    <button type="submit" style={buttonStyle} disabled={loading || actionLoading}>{actionLoading ? "Saving..." : "Add Donor"}</button>
                </form>
            </div>

            {Object.entries(grouped).map(([status, items]) => (
                <div key={status} style={{ marginBottom: "1.2rem" }}>
                    <h3 style={{ marginBottom: "0.5rem" }}>{status} ({items.length})</h3>
                    {items.length === 0 ? (
                        <p style={{ color: "#7f8c8d", fontStyle: "italic" }}>No donors in this status.</p>
                    ) : (
                        <div style={{ display: "grid", gap: "0.8rem" }}>
                            {items.map((donor) => (
                                <div key={donor.id} style={donorCardStyle}>
                                    <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                                        <div>
                                            <strong>{donor.device_identifier}</strong>
                                            <div style={{ color: "#34495e" }}>{donor.device_model}</div>
                                            <div style={{ color: "#7f8c8d", fontSize: "0.9rem" }}>{donor.condition_notes || "No condition notes"}</div>
                                        </div>
                                        <div style={{ textAlign: "right" }}>
                                            <div>Harvested: {donor.parts_harvested.length}</div>
                                            <div>Available: {donor.parts_available.length}</div>
                                        </div>
                                    </div>

                                    <div style={{ marginTop: "0.8rem", display: "grid", gap: "0.75rem" }}>
                                        <div>
                                            <div style={labelStyle}>Available parts on donor</div>
                                            {donor.parts_available.length === 0 ? (
                                                <div style={mutedStyle}>No available parts marked yet.</div>
                                            ) : (
                                                <div style={chipWrapStyle}>
                                                    {donor.parts_available.map((id) => (
                                                        <span key={`available-${id}`} style={chipStyle}>{getPartLabel(id)}</span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>

                                        <div>
                                            <div style={labelStyle}>Harvested parts</div>
                                            {donor.parts_harvested.length === 0 ? (
                                                <div style={mutedStyle}>No harvested parts yet.</div>
                                            ) : (
                                                <div style={chipWrapStyle}>
                                                    {donor.parts_harvested.map((id) => (
                                                        <span key={`harvested-${id}`} style={harvestedChipStyle}>{getPartLabel(id)}</span>
                                                    ))}
                                                </div>
                                            )}
                                        </div>

                                        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                                            <select
                                                value={availablePartId[donor.id] || ""}
                                                onChange={(e) => setAvailablePartId((prev) => ({ ...prev, [donor.id]: e.target.value }))}
                                                style={{ ...inputStyle, flex: "1 1 280px", minWidth: 0, maxWidth: "100%" }}
                                            >
                                                <option value="">Select part to add as available...</option>
                                                {parts
                                                    .filter((part) => !donor.parts_available.includes(part.id) && !donor.parts_harvested.includes(part.id))
                                                    .map((part) => (
                                                        <option key={part.id} value={String(part.id)}>
                                                            {part.part_number} - {part.part_name}
                                                        </option>
                                                    ))}
                                            </select>
                                            <button style={buttonStyle} onClick={() => handleAddAvailablePart(donor)} type="button">Add Available Part</button>
                                        </div>

                                        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap" }}>
                                            <select
                                                value={harvestPartId[donor.id] || ""}
                                                onChange={(e) => setHarvestPartId((prev) => ({ ...prev, [donor.id]: e.target.value }))}
                                                style={{ ...inputStyle, flex: "1 1 280px", minWidth: 0, maxWidth: "100%" }}
                                            >
                                                <option value="">Select part to harvest...</option>
                                                {getHarvestOptions(donor).map((part) => (
                                                    <option key={part.id} value={String(part.id)}>
                                                        {part.part_number} - {part.part_name}
                                                    </option>
                                                ))}
                                            </select>
                                            <button style={buttonStyle} onClick={() => handleHarvest(donor.id)} type="button">Harvest Part</button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ))}
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
    padding: "0.58rem 0.92rem",
    background: "linear-gradient(145deg, #1f6657 0%, #184e42 100%)",
    color: "white",
    border: "none",
    borderRadius: "999px",
    cursor: "pointer",
    fontWeight: 700,
    letterSpacing: "0.01em",
    boxShadow: "0 8px 16px rgba(23, 70, 60, 0.2)",
};

const panelCardStyle = {
    background: "linear-gradient(145deg, rgba(255,255,255,0.88) 0%, rgba(243,249,247,0.88) 100%)",
    border: "1px solid rgba(28, 63, 56, 0.12)",
    padding: "1.2rem",
    borderRadius: "14px",
    boxShadow: "0 10px 20px rgba(20, 44, 38, 0.08)",
};

const donorCardStyle = {
    border: "1px solid #cdd8d6",
    borderRadius: "12px",
    background: "linear-gradient(145deg, #ffffff 0%, #f6fbf9 100%)",
    padding: "1rem",
    boxShadow: "0 10px 18px rgba(20, 44, 38, 0.08)",
};

const labelStyle = {
    color: "#34495e",
    fontWeight: 600,
    marginBottom: "0.35rem",
    fontSize: "0.92rem",
};

const mutedStyle = {
    color: "#7f8c8d",
    fontStyle: "italic" as const,
    fontSize: "0.9rem",
};

const chipWrapStyle = {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "0.4rem",
};

const chipStyle = {
    backgroundColor: "#e2f2ee",
    color: "#1b5e20",
    borderRadius: "999px",
    padding: "0.25rem 0.6rem",
    fontSize: "0.82rem",
};

const harvestedChipStyle = {
    backgroundColor: "#fff0dc",
    color: "#7a4300",
    borderRadius: "999px",
    padding: "0.25rem 0.6rem",
    fontSize: "0.82rem",
};
