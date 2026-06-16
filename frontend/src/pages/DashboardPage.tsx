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
import { formatPhone } from "../lib/format";
import { buildTransitionPath, getWorkflowAwareUiActions, QUICK_REPAIR_STATUS_COLORS, QUICK_REPAIR_STATUSES, toUiStatus } from "../lib/repairFlow";
import { MetricTile, PageHeader, SectionCard } from "../components/PageChrome";
import * as t from "../styles/theme";

const TERMINAL_STATUSES = new Set(["Picked Up / Closed", "Not Repairable", "Returned Unrepaired", "Customer Declined"]);

function isChargeableOpenBalance(ticket: TicketSummary): boolean {
    return ticket.status === "Picked Up / Closed" && ticket.payment_status !== "paid";
}

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
    const [openOverflowTicketId, setOpenOverflowTicketId] = useState<number | null>(null);

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
        const unpaidRepairs = tickets.filter((ticket) => isChargeableOpenBalance(ticket)).length;

        const recentCustomers = Array.from(
            new Map(
                [...tickets]
                    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
                    .map((ticket) => [ticket.customer_id, { id: ticket.customer_id, name: ticket.customer_name, phone: ticket.customer_phone }])
            ).values()
        ).slice(0, 6);

        return { activeRepairs, completedToday, waitingForParts, unpaidRepairs, recentCustomers };
    }, [tickets]);

    const latestUpdatedAt = useMemo(() => {
        if (tickets.length === 0) {
            return null;
        }
        const newest = [...tickets].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())[0];
        return newest?.updated_at ?? null;
    }, [tickets]);

    async function handleQuickStatusChange(ticket: TicketSummary, targetStatus: (typeof QUICK_REPAIR_STATUSES)[number]) {
        setUpdatingTicketId(ticket.id);
        setOpenOverflowTicketId(null);
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
            const message = requestError instanceof Error ? requestError.message : "";
            if (/final price/i.test(message)) {
                setUpdateError("Set a final price before moving this ticket to pickup or closeout.");
            } else if (/loaner/i.test(message)) {
                setUpdateError("Close out any active loaner before moving this ticket to pickup or closeout.");
            } else {
                setUpdateError("Could not update ticket status right now. Refresh and try again.");
            }
        } finally {
            setUpdatingTicketId(null);
        }
    }

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Today"
                title="What Needs Attention"
                description="See urgent repairs, unpaid tickets, and fresh activity in one counter-friendly view."
                actions={
                    <div style={{ ...t.formActionsRow, gap: "8px" }}>
                        <Link to="/intake" style={newRepairButtonStyle}>+ New Repair</Link>
                        <Link to="/voicemail" style={quickLinkBtnStyle}>Check Voicemail</Link>
                    </div>
                }
            />

            <div style={{ ...t.meta, marginTop: "-2px" }}>
                Last updated: {latestUpdatedAt ? new Date(latestUpdatedAt).toLocaleString() : "No ticket activity yet"}
            </div>

            <div style={heroPanelStyle}>
                <div style={metricGridStyle}>
                    <MetricTile label="Active Repairs" value={metrics.activeRepairs} />
                    <MetricTile label="Completed Today" value={metrics.completedToday} />
                    <MetricTile label="Waiting for Parts" value={metrics.waitingForParts} />
                    <MetricTile label="Unpaid Repairs" value={metrics.unpaidRepairs} />
                </div>
            </div>

            <SectionCard title="Desk Filters" description="Search active tickets, narrow by stage, and decide what to handle next.">
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
            </SectionCard>

            {updateError ? <div style={t.errorBanner}>{updateError}</div> : null}
            {error ? <div style={t.errorBanner}>{error}</div> : null}

            <div style={deskLanesStyle}>
                <SectionCard title={`Live tickets (${filteredTickets.length})`} description="Most recently updated tickets first.">
                    <div style={boardGridStyle}>
                        {filteredTickets.map((ticket) => {
                            const uiStatus = toUiStatus(ticket.status);
                            const statusColors = QUICK_REPAIR_STATUS_COLORS[uiStatus];
                            const updatedLabel = new Date(ticket.updated_at).toLocaleString();
                            const transitions = statusRules?.transitions ?? DEFAULT_TRANSITIONS;
                            const rankedActions = getWorkflowAwareUiActions(ticket.status, transitions);
                            const primaryActions = rankedActions.slice(0, 2);
                            const overflowActions = rankedActions.slice(2);
                            const isOverflowOpen = openOverflowTicketId === ticket.id;
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
                                        {primaryActions.map(({ status }) => (
                                            <button
                                                key={status}
                                                type="button"
                                                onClick={() => void handleQuickStatusChange(ticket, status)}
                                                disabled={updatingTicketId === ticket.id}
                                                style={quickActionChipStyle}
                                            >
                                                {status}
                                            </button>
                                        ))}
                                        {overflowActions.length > 0 ? (
                                            <div style={{ position: "relative" }}>
                                                <button
                                                    type="button"
                                                    aria-label="More status actions"
                                                    onClick={() => setOpenOverflowTicketId(isOverflowOpen ? null : ticket.id)}
                                                    disabled={updatingTicketId === ticket.id}
                                                    style={overflowToggleButtonStyle}
                                                >
                                                    ⋮
                                                </button>
                                                {isOverflowOpen ? (
                                                    <div style={overflowMenuStyle}>
                                                        {overflowActions.map(({ status }) => (
                                                            <button
                                                                key={status}
                                                                type="button"
                                                                onClick={() => void handleQuickStatusChange(ticket, status)}
                                                                disabled={updatingTicketId === ticket.id}
                                                                style={overflowMenuItemStyle}
                                                            >
                                                                {status}
                                                            </button>
                                                        ))}
                                                    </div>
                                                ) : null}
                                            </div>
                                        ) : null}
                                        {primaryActions.length === 0 && overflowActions.length === 0 ? (
                                            <span style={{ ...t.meta, fontSize: "0.78rem" }}>No next status action</span>
                                        ) : null}
                                    </div>
                                </article>
                            );
                        })}
                    </div>
                </SectionCard>

                <div style={{ display: "grid", gap: "12px", alignContent: "start" }}>
                    <SectionCard title="Fast Actions" compact tone="soft">
                        <div style={{ ...t.formStack, gap: "8px" }}>
                            <Link to="/tickets" style={quickWorkflowCardStyle}>Search Tickets</Link>
                            <Link to="/voicemail" style={quickWorkflowCardStyle}>Open Voicemail Inbox</Link>
                            <Link to="/operations" style={quickWorkflowCardStyle}>Open Shop Tools</Link>
                        </div>
                    </SectionCard>

                    <SectionCard title="Recent Customers" compact>
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
                                        <span>{customer.phone ? formatPhone(customer.phone) : "No phone on file"}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </SectionCard>
                </div>
            </div>
        </section>
    );
}

const newRepairButtonStyle = {
    textDecoration: "none",
    borderRadius: "12px",
    padding: "11px 14px",
    background: "linear-gradient(145deg, #1e9488 0%, #156e67 100%)",
    color: "#f5fffd",
    fontWeight: 700,
    boxShadow: "0 10px 20px rgba(17, 85, 86, 0.26)",
};

const quickLinkBtnStyle = {
    ...newRepairButtonStyle,
    background: "rgba(255,255,255,0.86)",
    color: "#16414b",
    border: "1px solid rgba(20, 67, 73, 0.18)",
    boxShadow: "none",
};

const heroPanelStyle = {
    ...t.panel,
    padding: "14px",
    background: "radial-gradient(circle at 16% 14%, rgba(222, 252, 246, 0.92) 0%, rgba(255, 249, 238, 0.94) 45%, rgba(244, 228, 200, 0.9) 100%)",
};

const metricGridStyle = {
    display: "grid",
    gap: "10px",
    gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
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

const deskLanesStyle = {
    display: "grid",
    gap: "12px",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
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
    position: "absolute" as const,
    top: "110%",
    right: 0,
    minWidth: "180px",
    borderRadius: "10px",
    border: "1px solid rgba(29, 43, 40, 0.16)",
    background: "#ffffff",
    boxShadow: "0 8px 18px rgba(19, 45, 40, 0.15)",
    zIndex: 10,
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

const recentCustomersStyle = {
    display: "grid",
    gap: "8px",
    gridTemplateColumns: "1fr",
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

const quickWorkflowCardStyle = {
    ...t.subCard,
    textDecoration: "none",
    color: "#163b46",
    fontWeight: 700,
    borderRadius: "12px",
    padding: "10px 12px",
};
