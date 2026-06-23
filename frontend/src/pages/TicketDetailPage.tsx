import { useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
    addTicketNote,
    fetchStatusWorkflowRules,
    fetchTicket,
    updateTicketStatus,
    type StatusWorkflowRules,
    type TicketDetail,
} from "../api/tickets";
import { fetchRepairActionPartUsage, type PartUsage } from "../api/inventory";
import { useAsyncData } from "../hooks/useAsyncData";
import { buildTransitionPath, getWorkflowAwareUiActions, QUICK_REPAIR_STATUS_COLORS, QUICK_REPAIR_STATUSES, toUiStatus } from "../lib/repairFlow";
import { FloatingMenu } from "../components/FloatingMenu";
import * as t from "../styles/theme";

const DEFAULT_TRANSITIONS: Record<string, string[]> = {
    "New Intake": ["Needs Diagnosis"],
    "Needs Diagnosis": ["Diagnosed", "Not Repairable", "Returned Unrepaired"],
    Diagnosed: ["Approved", "Customer Approval Needed", "Waiting for Parts", "Replaced Instead"],
    "Customer Approval Needed": ["Approved", "Customer Declined"],
    "Customer Declined": ["Returned Unrepaired"],
    Approved: ["Ready for Repair"],
    "Waiting for Parts": ["Ready for Repair"],
    "Ready for Repair": ["In Repair"],
    "In Repair": ["Ready for Pickup"],
    "Ready for Pickup": ["Picked Up / Closed"],
    "Replaced Instead": ["Picked Up / Closed"],
    "Picked Up / Closed": [],
    "Not Repairable": [],
    "Returned Unrepaired": [],
};

export default function TicketDetailPage() {
    const { ticketId = "" } = useParams();
    const [refreshKey, setRefreshKey] = useState(0);
    const [noteBody, setNoteBody] = useState("");
    const [noteBy, setNoteBy] = useState("");
    const [statusBy, setStatusBy] = useState("");
    const [statusNote, setStatusNote] = useState("");
    const [updatingStatus, setUpdatingStatus] = useState<null | string>(null);
    const [error, setError] = useState<string | null>(null);
    const [statusMenuOpen, setStatusMenuOpen] = useState(false);
    const [editingFinalPrice, setEditingFinalPrice] = useState(false);
    const [newFinalPrice, setNewFinalPrice] = useState("");
    const [newPaymentStatus, setNewPaymentStatus] = useState<"unpaid" | "partial" | "paid">("unpaid");
    const statusMenuButtonRef = useRef<HTMLButtonElement | null>(null);

    const { data: ticket, error: ticketLoadError } = useAsyncData<TicketDetail>(() => fetchTicket(ticketId), [ticketId, refreshKey]);
    const { data: statusRules } = useAsyncData<StatusWorkflowRules>(() => fetchStatusWorkflowRules(), []);
    const { data: partUsage = [] } = useAsyncData<PartUsage[]>(
        async () => {
            if (!ticket || ticket.repair_actions.length === 0) {
                return [];
            }
            const groups = await Promise.all(ticket.repair_actions.map((action) => fetchRepairActionPartUsage(action.id)));
            return groups.flat();
        },
        [ticket?.id, refreshKey]
    );

    const uiStatus = ticket ? toUiStatus(ticket.status) : "Diagnosing";
    const transitions = statusRules?.transitions ?? DEFAULT_TRANSITIONS;
    const rankedStatusActions = ticket ? getWorkflowAwareUiActions(ticket.status, transitions).map((entry) => entry.status) : [];
    const preferredOrder: (typeof QUICK_REPAIR_STATUSES)[number][] = ["Ready for Pickup", "Completed", "Canceled"];
    const prioritizedActions = preferredOrder.filter((status) => rankedStatusActions.includes(status));
    const secondaryActions = rankedStatusActions.filter((status) => !prioritizedActions.includes(status));
    const orderedActions = [...prioritizedActions, ...secondaryActions];
    const primaryActions = orderedActions.slice(0, 3);
    const overflowActions = orderedActions.slice(3);

    const timeline = useMemo(() => {
        if (!ticket) {
            return [] as Array<{ id: string; time: string; title: string; detail: string }>;
        }

        const fromHistory = ticket.history.map((item) => ({
            id: `status-${item.id}`,
            time: item.created_at,
            title: item.old_status ? `${item.old_status} -> ${item.new_status}` : item.new_status,
            detail: [item.note, item.changed_by].filter(Boolean).join(" · ") || "Status updated",
        }));

        const fromNotes = ticket.notes.map((note) => ({
            id: `note-${note.id}`,
            time: note.created_at,
            title: `Note: ${note.note_type}`,
            detail: `${note.body}${note.created_by ? ` · ${note.created_by}` : ""}`,
        }));

        return [...fromHistory, ...fromNotes].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime());
    }, [ticket]);

    async function moveToStatus(target: (typeof QUICK_REPAIR_STATUSES)[number], priceToSubmit?: number, paymentStatusToSubmit?: string) {
        if (!ticket) {
            return;
        }

        setUpdatingStatus(target);
        setStatusMenuOpen(false);
        setError(null);

        try {
            const path = buildTransitionPath(ticket.status, target, transitions);
            if (path.length === 0 && toUiStatus(ticket.status) !== target) {
                throw new Error("No valid transition path found for this status.");
            }

            for (let index = 0; index < path.length; index += 1) {
                const next = path[index];
                const note = index === path.length - 1 ? statusNote : "";
                await updateTicketStatus(ticket.id, next, statusBy, note, priceToSubmit, paymentStatusToSubmit);
            }

            setStatusNote("");
            setEditingFinalPrice(false);
            setNewFinalPrice("");
            setNewPaymentStatus("unpaid");
            setRefreshKey((current) => current + 1);
        } catch (requestError) {
            const message = requestError instanceof Error ? requestError.message : "";
            if (/final price/i.test(message)) {
                setError("Set a final price before moving this ticket to pickup or closeout.");
                setEditingFinalPrice(true);
            } else if (/loaner/i.test(message)) {
                setError("Close out any active loaner before moving this ticket to pickup or closeout.");
            } else {
                setError("Unable to update status right now. Refresh and try again.");
            }
        } finally {
            setUpdatingStatus(null);
        }
    }

    async function appendNote() {
        if (!ticket || !noteBody.trim()) {
            return;
        }

        try {
            await addTicketNote(ticket.id, "technician", noteBody.trim(), noteBy);
            setNoteBody("");
            setRefreshKey((current) => current + 1);
            setError(null);
        } catch (requestError) {
            setError(requestError instanceof Error ? requestError.message : "Unable to add note");
        }
    }

    if (ticketLoadError) {
        return <section style={t.panel}><p style={{ color: "#9b2c2c" }}>{ticketLoadError}</p></section>;
    }

    if (!ticket) {
        return <section style={t.panel}><p>Loading repair...</p></section>;
    }

    const statusColors = QUICK_REPAIR_STATUS_COLORS[uiStatus];

    return (
        <section style={t.pageWrap}>
            <div style={headerStyle}>
                <div>
                    <div style={{ color: "#56706a", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", fontSize: "0.76rem" }}>{ticket.ticket_number}</div>
                    <h2 style={{ margin: "6px 0 0" }}>
                        <Link to={`/customers/${ticket.customer_id}`} style={{ color: "inherit", textDecoration: "none" }}>
                            {ticket.customer_name}
                        </Link>
                    </h2>
                    <p style={{ ...t.pageIntro, marginTop: "6px" }}>{ticket.device_label} · {ticket.issue_category}</p>
                </div>
                <span style={{ borderRadius: "999px", border: `1px solid ${statusColors.border}`, color: statusColors.text, background: statusColors.bg, padding: "8px 12px", fontWeight: 700, alignSelf: "start" }}>
                    {uiStatus}
                </span>
            </div>

            <div style={t.panel}>
                <h3 style={{ ...t.heading, marginBottom: "10px" }}>One-Click Status</h3>
                <p style={{ ...t.meta, marginTop: 0, marginBottom: "10px" }}>
                    Primary next actions are shown first. Less common valid moves are available in More actions.
                </p>
                <div style={{ ...t.formActionsRow, gap: "8px", marginBottom: "10px" }}>
                    {primaryActions.map((status) => (
                        <button
                            key={status}
                            type="button"
                            onClick={() => {
                                // If moving to a final status and we don't have a final price, prompt for it
                                if (["Picked Up / Closed", "Completed", "Canceled"].includes(status) && ticket.final_price === null) {
                                    setEditingFinalPrice(true);
                                    setNewFinalPrice("");
                                    setError("Please set a final price before completing this ticket.");
                                } else {
                                    void moveToStatus(status, ticket.final_price || undefined);
                                }
                            }}
                            disabled={updatingStatus !== null}
                            style={status === "Completed" ? t.primaryBtn : t.secondaryBtn}
                        >
                            {updatingStatus === status ? "Updating..." : status}
                        </button>
                    ))}
                    {overflowActions.length > 0 ? (
                        <div>
                            <button
                                type="button"
                                ref={statusMenuButtonRef}
                                aria-label="More status actions"
                                onClick={() => setStatusMenuOpen((open) => !open)}
                                disabled={updatingStatus !== null}
                                style={overflowToggleButtonStyle}
                            >
                                ⋮
                            </button>
                            <FloatingMenu
                                open={statusMenuOpen}
                                anchorElement={statusMenuButtonRef.current}
                                onClose={() => setStatusMenuOpen(false)}
                                align="right"
                                style={overflowMenuStyle}
                            >
                                {overflowActions.map((status) => (
                                    <button
                                        key={status}
                                        type="button"
                                        onClick={() => {
                                            if (["Picked Up / Closed", "Completed", "Canceled"].includes(status) && ticket.final_price === null) {
                                                setEditingFinalPrice(true);
                                                setNewFinalPrice("");
                                                setError("Please set a final price before completing this ticket.");
                                            } else {
                                                void moveToStatus(status, ticket.final_price || undefined);
                                            }
                                        }}
                                        disabled={updatingStatus !== null}
                                        style={overflowMenuItemStyle}
                                    >
                                        {status}
                                    </button>
                                ))}
                            </FloatingMenu>
                        </div>
                    ) : null}
                    {primaryActions.length === 0 && overflowActions.length === 0 ? (
                        <span style={t.meta}>No valid next status actions from the current stage.</span>
                    ) : null}
                </div>
                <div style={{ ...t.fieldGridTwoCompact, marginTop: "12px" }}>
                    <input
                        value={statusBy}
                        onChange={(event) => setStatusBy(event.target.value)}
                        placeholder="Changed by"
                        style={t.input}
                    />
                    <input
                        value={statusNote}
                        onChange={(event) => setStatusNote(event.target.value)}
                        placeholder="Status note (optional)"
                        style={t.input}
                    />
                </div>
            </div>

            {error ? <div style={t.errorBanner}>{error}</div> : null}

            <div style={detailGridStyle}>
                <div style={t.panel}>
                    <h3 style={t.heading}>Customer Info</h3>
                    <DetailRow label="Phone" value={ticket.customer_phone || ticket.customer_alternate_phone || "Not set"} />
                    <DetailRow label="Issue" value={ticket.issue_description || ticket.issue_category} />
                    <DetailRow label="Estimated" value={ticket.estimated_price != null ? `$${ticket.estimated_price.toFixed(2)}` : "Not set"} />
                    <DetailRow label="Final" value={ticket.final_price != null ? `$${ticket.final_price.toFixed(2)}` : "Not collected"} />
                    <DetailRow label="Intake" value={new Date(ticket.intake_date).toLocaleString()} />
                    <DetailRow label="Last updated" value={new Date(ticket.updated_at).toLocaleString()} />
                </div>

                <div style={t.panel}>
                    <h3 style={t.heading}>Payment Info</h3>
                    <div style={{ ...t.subCard, marginBottom: "10px" }}>
                        <strong>Status</strong>
                        <div style={t.meta}>{ticket.payment_status}</div>
                    </div>
                    <div style={{ ...t.subCard, marginBottom: "10px" }}>
                        <strong>Estimate vs Final</strong>
                        <div style={t.meta}>Estimated: {ticket.estimated_price != null ? `$${ticket.estimated_price.toFixed(2)}` : "-"}</div>
                        <div style={{ ...t.meta, marginBottom: "8px" }}>
                            Final: {ticket.final_price != null ? `$${ticket.final_price.toFixed(2)}` : "-"}
                        </div>
                        {!editingFinalPrice ? (
                            <button
                                type="button"
                                onClick={() => {
                                    setEditingFinalPrice(true);
                                    setNewFinalPrice(ticket.final_price?.toString() || "");
                                    setNewPaymentStatus(ticket.payment_status as "unpaid" | "partial" | "paid" || "unpaid");
                                }}
                                style={{ ...t.secondaryBtn, padding: "6px 10px", fontSize: "0.9rem", alignSelf: "start" }}
                            >
                                Set Final Price
                            </button>
                        ) : (
                            <div style={{ display: "grid", gap: "8px" }}>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                                    <input
                                        type="number"
                                        value={newFinalPrice}
                                        onChange={(e) => setNewFinalPrice(e.target.value)}
                                        placeholder="Enter final price"
                                        step="0.01"
                                        min="0"
                                        style={{ ...t.input, padding: "6px 10px" }}
                                        autoFocus
                                    />
                                    <select
                                        value={newPaymentStatus}
                                        onChange={(e) => setNewPaymentStatus(e.target.value as "unpaid" | "partial" | "paid")}
                                        style={{ ...t.input, padding: "6px 10px" }}
                                    >
                                        <option value="unpaid">Unpaid</option>
                                        <option value="partial">Partial</option>
                                        <option value="paid">Paid (Card)</option>
                                    </select>
                                </div>
                                <div style={{ display: "grid", gridTemplateColumns: "auto auto", gap: "8px", justifySelf: "start" }}>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            if (newFinalPrice) {
                                                const price = parseFloat(newFinalPrice);
                                                if (!isNaN(price)) {
                                                    void moveToStatus("Completed", price, newPaymentStatus);
                                                }
                                            }
                                        }}
                                        disabled={updatingStatus !== null || !newFinalPrice}
                                        style={{ ...t.primaryBtn, padding: "6px 12px", fontSize: "0.9rem" }}
                                    >
                                        {updatingStatus ? "Saving..." : "Save & Complete"}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setEditingFinalPrice(false);
                                            setNewFinalPrice("");
                                            setNewPaymentStatus("unpaid");
                                            setError(null);
                                        }}
                                        style={{ ...t.secondaryBtn, padding: "6px 12px", fontSize: "0.9rem" }}
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                    <Link to={`/tickets/${ticket.id}/invoice`} style={invoiceLinkStyle}>Open Invoice</Link>
                </div>
            </div>

            <div style={detailGridStyle}>
                <div style={t.panel}>
                    <h3 style={t.heading}>Repair Notes (append-only log)</h3>
                    <div style={{ display: "grid", gap: "10px" }}>
                        <input
                            value={noteBy}
                            onChange={(event) => setNoteBy(event.target.value)}
                            placeholder="Created by"
                            style={t.input}
                        />
                        <textarea
                            value={noteBody}
                            onChange={(event) => setNoteBody(event.target.value)}
                            placeholder="Add technician or front desk note"
                            style={{ ...t.input, minHeight: "90px", resize: "vertical" }}
                        />
                        <button type="button" onClick={() => void appendNote()} style={{ ...t.primaryBtn, justifySelf: "start" }}>
                            Add Log Entry
                        </button>
                    </div>
                    <div style={{ display: "grid", gap: "10px", marginTop: "12px" }}>
                        {ticket.notes.length === 0 ? <p style={t.meta}>No notes yet.</p> : null}
                        {ticket.notes.map((note) => (
                            <article key={note.id} style={t.subCard}>
                                <strong>{note.note_type}</strong>
                                <div style={t.meta}>{new Date(note.created_at).toLocaleString()} · {note.created_by || "Unknown staff"}</div>
                                <p style={{ ...t.copy, marginTop: "6px", marginBottom: 0 }}>{note.body}</p>
                            </article>
                        ))}
                    </div>
                </div>

                <div style={t.panel}>
                    <h3 style={t.heading}>Parts Used</h3>
                    {partUsage.length === 0 ? (
                        <p style={t.meta}>No part usage recorded yet.</p>
                    ) : (
                        <div style={{ display: "grid", gap: "10px" }}>
                            {partUsage.map((usage) => (
                                <article key={usage.id} style={t.subCard}>
                                    <strong>{usage.part_number} · {usage.part_name}</strong>
                                    <div style={t.meta}>Qty {usage.quantity_used} · {new Date(usage.created_at).toLocaleString()}</div>
                                </article>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            <div style={t.panel}>
                <h3 style={t.heading}>Timeline / Status History</h3>
                {timeline.length === 0 ? (
                    <p style={t.meta}>No history recorded yet.</p>
                ) : (
                    <div style={{ display: "grid", gap: "10px" }}>
                        {timeline.map((entry) => (
                            <article key={entry.id} style={timelineRowStyle}>
                                <strong>{entry.title}</strong>
                                <div style={t.meta}>{new Date(entry.time).toLocaleString()}</div>
                                <p style={{ ...t.copy, marginTop: "6px", marginBottom: 0 }}>{entry.detail}</p>
                            </article>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}

function DetailRow(props: { label: string; value: string }) {
    return (
        <div style={{ display: "grid", gridTemplateColumns: "130px 1fr", gap: "12px", borderBottom: "1px solid rgba(29,43,40,0.08)", padding: "10px 0" }}>
            <strong>{props.label}</strong>
            <span>{props.value}</span>
        </div>
    );
}

const headerStyle = {
    ...t.panel,
    display: "flex",
    justifyContent: "space-between",
    gap: "10px",
    alignItems: "start",
    flexWrap: "wrap" as const,
};

const detailGridStyle = {
    display: "grid",
    gap: "10px",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
};

const invoiceLinkStyle = {
    textDecoration: "none",
    borderRadius: "999px",
    border: "1px solid rgba(29,43,40,0.14)",
    padding: "7px 12px",
    color: "#163731",
    background: "#ffffff",
    fontWeight: 700,
    display: "inline-block",
};

const timelineRowStyle = {
    borderRadius: "12px",
    border: "1px solid rgba(29,43,40,0.12)",
    background: "#f8f3ea",
    padding: "8px 12px",
};

const overflowToggleButtonStyle = {
    borderRadius: "10px",
    border: "1px solid rgba(29, 43, 40, 0.16)",
    background: "#ffffff",
    color: "#17342d",
    padding: "4px 9px",
    fontWeight: 800,
    fontSize: "1rem",
    lineHeight: 1,
    cursor: "pointer",
};

const overflowMenuStyle = {
    minWidth: "180px",
    borderRadius: "10px",
    border: "1px solid rgba(29, 43, 40, 0.16)",
    background: "#ffffff",
    boxShadow: "0 8px 18px rgba(19, 45, 40, 0.15)",
    display: "grid",
    padding: "6px",
    gap: "4px",
};

const overflowMenuItemStyle = {
    borderRadius: "8px",
    border: "1px solid transparent",
    background: "#f5f8f7",
    color: "#183831",
    textAlign: "left" as const,
    padding: "8px 9px",
    fontWeight: 600,
    cursor: "pointer",
};
