import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import {
    fetchStatusWorkflowRules,
    fetchTickets,
    updateTicketStatus,
    type StatusWorkflowRules,
    type TicketSummary,
} from "../api/tickets";
import { useAsyncData } from "../hooks/useAsyncData";
import { buildTransitionPath, QUICK_REPAIR_STATUS_COLORS, QUICK_REPAIR_STATUSES, toUiStatus } from "../lib/repairFlow";
import * as t from "../styles/theme";

const TERMINAL_STATUSES = new Set(["Picked Up / Closed", "Not Repairable", "Returned Unrepaired", "Customer Declined"]);

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

export default function DashboardPage() {
    const [search, setSearch] = useState("");
    const [filterStatus, setFilterStatus] = useState<"All" | (typeof QUICK_REPAIR_STATUSES)[number]>("All");
    const [sortBy, setSortBy] = useState<"newest" | "oldest">("newest");
    const [reloadCounter, setReloadCounter] = useState(0);
    const [updatingTicketId, setUpdatingTicketId] = useState<number | null>(null);
    const [updateError, setUpdateError] = useState<string | null>(null);

    const { data: tickets = [], error } = useAsyncData<TicketSummary[]>(() => fetchTickets(), [reloadCounter]);
    const { data: statusRules } = useAsyncData<StatusWorkflowRules>(() => fetchStatusWorkflowRules(), []);

    const filteredTickets = useMemo(() => {
        const needle = search.trim().toLowerCase();
        const base = tickets.filter((ticket) => {
            const matchesSearch =
                !needle ||
                `${ticket.ticket_number} ${ticket.customer_name} ${ticket.customer_phone ?? ""} ${ticket.device_label} ${ticket.issue_category}`
                    .toLowerCase()
                    .includes(needle);
            const uiStatus = toUiStatus(ticket.status);
            const matchesStatus = filterStatus === "All" || uiStatus === filterStatus;
            return matchesSearch && matchesStatus;
        });

        return base.sort((a, b) => {
            const aTime = new Date(a.updated_at).getTime();
            const bTime = new Date(b.updated_at).getTime();
            return sortBy === "newest" ? bTime - aTime : aTime - bTime;
        });
    }, [filterStatus, search, sortBy, tickets]);

    const metrics = useMemo(() => {
        const today = new Date().toDateString();
        const activeRepairs = tickets.filter((ticket) => !TERMINAL_STATUSES.has(ticket.status)).length;
        const completedToday = tickets.filter((ticket) => ticket.status === "Picked Up / Closed" && new Date(ticket.updated_at).toDateString() === today).length;
        const waitingForParts = tickets.filter((ticket) => ticket.status === "Waiting for Parts").length;
        const unpaidRepairs = tickets.filter((ticket) => ticket.payment_status !== "paid").length;

        const recentCustomers = Array.from(
            new Map(
                [...tickets]
                    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                    .map((ticket) => [ticket.customer_id, { id: ticket.customer_id, name: ticket.customer_name, phone: ticket.customer_phone }])
            ).values()
        ).slice(0, 6);

        return { activeRepairs, completedToday, waitingForParts, unpaidRepairs, recentCustomers };
    }, [tickets]);

    async function handleQuickStatusChange(ticket: TicketSummary, targetStatus: (typeof QUICK_REPAIR_STATUSES)[number]) {
        setUpdatingTicketId(ticket.id);
        setUpdateError(null);
        try {
            const transitions = statusRules?.transitions ?? DEFAULT_TRANSITIONS;
            const path = buildTransitionPath(ticket.status, targetStatus, transitions);
            if (path.length === 0 && toUiStatus(ticket.status) !== targetStatus) {
                throw new Error("No valid transition path found from current status.");
            }

            for (const nextStatus of path) {
                await updateTicketStatus(ticket.id, nextStatus, "", "");
            }

            setReloadCounter((value) => value + 1);
        } catch (requestError) {
            setUpdateError(requestError instanceof Error ? requestError.message : "Could not update ticket status");
        } finally {
            setUpdatingTicketId(null);
        }
    }

    return (
        <section style={{ display: "grid", gap: "20px", width: "100%", maxWidth: "1280px", margin: "0 auto" }}>
            <div style={{ ...t.formActionsRow, justifyContent: "space-between" }}>
                <div>
                    <h2 style={{ margin: 0 }}>Service Desk</h2>
                    <p style={{ ...t.pageIntro, marginTop: "6px" }}>Fast repair tracking built for counter speed and technician flow.</p>
                </div>
                <Link to="/intake" style={newRepairButtonStyle}>+ New Repair</Link>
            </div>

            <div style={heroPanelStyle}>
                <div style={metricGridStyle}>
                    <MetricCard label="Active Repairs" value={metrics.activeRepairs} accent="#175f4a" />
                    <MetricCard label="Completed Today" value={metrics.completedToday} accent="#2e6c3e" />
                    <MetricCard label="Waiting for Parts" value={metrics.waitingForParts} accent="#8c4b1b" />
                    <MetricCard label="Unpaid Repairs" value={metrics.unpaidRepairs} accent="#9b2c2c" />
                </div>
            </div>

            <div style={t.panel}>
                <div style={{ display: "grid", gap: "10px" }}>
                    <input
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
                        placeholder="Search ticket, customer, phone, device, issue"
                        style={t.input}
                    />
                    <div style={{ ...t.formActionsRow, gap: "8px" }}>
                        <button
                            type="button"
                            onClick={() => setFilterStatus("All")}
                            style={{ ...filterChipStyle, ...(filterStatus === "All" ? activeFilterChipStyle : null) }}
                        >
                            All
                        </button>
                        {QUICK_REPAIR_STATUSES.map((status) => {
                            const colors = QUICK_REPAIR_STATUS_COLORS[status];
                            const active = filterStatus === status;
                            return (
                                <button
                                    key={status}
                                    type="button"
                                    onClick={() => setFilterStatus(status)}
                                    style={{
                                        ...filterChipStyle,
                                        background: active ? colors.text : colors.bg,
                                        borderColor: active ? colors.text : colors.border,
                                        color: active ? "#ffffff" : colors.text,
                                    }}
                                >
                                    {status}
                                </button>
                            );
                        })}
                        <select value={sortBy} onChange={(event) => setSortBy(event.target.value as "newest" | "oldest")} style={{ ...t.input, width: "auto" }}>
                            <option value="newest">Newest first</option>
                            <option value="oldest">Oldest first</option>
                        </select>
                    </div>
                </div>
            </div>

            {updateError ? <div style={t.errorBanner}>{updateError}</div> : null}
            {error ? <div style={t.errorBanner}>{error}</div> : null}

            <div style={boardGridStyle}>
                {filteredTickets.map((ticket) => {
                    const uiStatus = toUiStatus(ticket.status);
                    const statusColors = QUICK_REPAIR_STATUS_COLORS[uiStatus];
                    const updatedLabel = new Date(ticket.updated_at).toLocaleString();
                    return (
                        <article key={ticket.id} style={ticketCardStyle}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", alignItems: "start" }}>
                                <Link to={`/tickets/${ticket.id}`} style={{ textDecoration: "none", color: "#163731", fontWeight: 800 }}>
                                    {ticket.ticket_number}
                                </Link>
                                <span style={{ borderRadius: "999px", padding: "6px 10px", background: statusColors.bg, color: statusColors.text, border: `1px solid ${statusColors.border}`, fontSize: "0.78rem", fontWeight: 700 }}>
                                    {uiStatus}
                                </span>
                            </div>
                            <div style={{ fontWeight: 700, color: "#193d35", marginTop: "8px" }}>{ticket.customer_name}</div>
                            <div style={{ marginTop: "4px", color: "#3d5d55", fontSize: "0.9rem" }}>{ticket.device_label}</div>
                            <div style={{ marginTop: "4px", color: "#5a726c", fontSize: "0.85rem" }}>{ticket.issue_category}</div>
                            <div style={{ marginTop: "8px", color: "#6d807b", fontSize: "0.77rem" }}>Updated {updatedLabel}</div>

                            <div style={{ ...t.formActionsRow, gap: "8px", marginTop: "12px" }}>
                                {QUICK_REPAIR_STATUSES.map((status) => (
                                    <button
                                        key={status}
                                        type="button"
                                        onClick={() => void handleQuickStatusChange(ticket, status)}
                                        disabled={updatingTicketId === ticket.id || status === uiStatus}
                                        style={{
                                            ...quickActionChipStyle,
                                            opacity: status === uiStatus ? 0.55 : 1,
                                        }}
                                    >
                                        {status}
                                    </button>
                                ))}
                            </div>
                        </article>
                    );
                })}
            </div>

            <div style={t.panel}>
                <h3 style={{ marginTop: 0, marginBottom: "12px" }}>Recent Customers</h3>
                {metrics.recentCustomers.length === 0 ? (
                    <p style={t.copy}>No customer activity yet.</p>
                ) : (
                    <div style={recentCustomersStyle}>
                        {metrics.recentCustomers.map((customer) => (
                            <div key={`${customer.name}-${customer.phone ?? "none"}`} style={recentCustomerRowStyle}>
                                <strong>
                                    <Link to={`/customers/${customer.id}`} style={{ color: "inherit", textDecoration: "none" }}>
                                        {customer.name}
                                    </Link>
                                </strong>
                                <span>{customer.phone || "No phone on file"}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}

function MetricCard(props: { label: string; value: number; accent: string }) {
    return (
        <div style={{ ...metricCardStyle, borderColor: `${props.accent}33` }}>
            <div style={{ fontSize: "0.78rem", letterSpacing: "0.08em", textTransform: "uppercase", color: "#5d746e", fontWeight: 700 }}>{props.label}</div>
            <div style={{ fontSize: "2rem", color: props.accent, fontWeight: 800, marginTop: "6px" }}>{props.value}</div>
        </div>
    );
}

const newRepairButtonStyle = {
    textDecoration: "none",
    borderRadius: "999px",
    padding: "12px 18px",
    background: "linear-gradient(145deg, #196352 0%, #133f35 100%)",
    color: "#f5efe3",
    fontWeight: 700,
    boxShadow: "0 10px 20px rgba(18, 52, 45, 0.24)",
};

const heroPanelStyle = {
    ...t.panel,
    padding: "16px",
    background: "radial-gradient(circle at 16% 14%, rgba(230, 250, 241, 0.96) 0%, rgba(255, 249, 238, 0.96) 45%, rgba(248, 236, 218, 0.96) 100%)",
};

const metricGridStyle = {
    display: "grid",
    gap: "10px",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
};

const metricCardStyle = {
    border: "1px solid rgba(29, 43, 40, 0.1)",
    borderRadius: "16px",
    background: "rgba(255,255,255,0.85)",
    padding: "14px 16px",
};

const filterChipStyle = {
    borderRadius: "999px",
    border: "1px solid rgba(29,43,40,0.12)",
    background: "#ffffff",
    color: "#18342e",
    padding: "8px 11px",
    fontWeight: 700,
    fontSize: "0.82rem",
    cursor: "pointer",
};

const activeFilterChipStyle = {
    background: "#18473f",
    borderColor: "#18473f",
    color: "#ffffff",
};

const boardGridStyle = {
    display: "grid",
    gap: "12px",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
};

const ticketCardStyle = {
    ...t.panel,
    padding: "14px",
    borderRadius: "16px",
    boxShadow: "0 12px 20px rgba(26, 46, 41, 0.08)",
};

const quickActionChipStyle = {
    borderRadius: "999px",
    border: "1px solid rgba(29, 43, 40, 0.15)",
    background: "#ffffff",
    color: "#17342d",
    padding: "6px 9px",
    fontWeight: 700,
    fontSize: "0.73rem",
    cursor: "pointer",
};

const recentCustomersStyle = {
    display: "grid",
    gap: "8px",
    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
};

const recentCustomerRowStyle = {
    borderRadius: "12px",
    border: "1px solid rgba(29,43,40,0.12)",
    background: "#f8f2e7",
    padding: "10px 12px",
    display: "grid",
    gap: "4px",
    color: "#26463f",
};
