import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { type TicketSummary } from "../api/tickets";
import { LoadingBoundary } from "../components/LoadingBoundary";
import { ScannerInput } from "../components/ScannerInput";
import { DataTable } from "../components/table/DataTable";
import { PageHeader, SectionCard } from "../components/PageChrome";
import { useTicketsQuery } from "../hooks/queries/useTicketsQuery";
import { formatDeskDateTime, formatMoney, formatPhone } from "../lib/format";
import { useUiStore } from "../store/uiStore";
import * as t from "../styles/theme";

export default function TicketsPage() {
    const [page, setPage] = useState(1);
    const [viewName, setViewName] = useState("");
    const search = useUiStore((state) => state.ticketSearch);
    const statusFilter = useUiStore((state) => state.ticketStatusFilter);
    const setSearch = useUiStore((state) => state.setTicketSearch);
    const setStatusFilter = useUiStore((state) => state.setTicketStatusFilter);
    const ticketSavedViews = useUiStore((state) => state.ticketSavedViews);
    const saveTicketView = useUiStore((state) => state.saveTicketView);
    const applyTicketView = useUiStore((state) => state.applyTicketView);
    const deleteTicketView = useUiStore((state) => state.deleteTicketView);
    const { data: tickets = [], isLoading, error } = useTicketsQuery(search);

    const filtered = useMemo(() => {
        const q = search.trim().toLowerCase();
        return tickets.filter((ticket) => {
            const matchesSearch =
                !q ||
                `${ticket.ticket_number} ${ticket.customer_name} ${ticket.customer_phone ?? ""} ${ticket.issue_category} ${ticket.device_label}`
                    .toLowerCase()
                    .includes(q);
            const matchesStatus = !statusFilter || ticket.status === statusFilter;
            return matchesSearch && matchesStatus;
        });
    }, [search, statusFilter, tickets]);

    const statuses = useMemo(
        () => Array.from(new Set(tickets.map((ticket) => ticket.status))).sort(),
        [tickets]
    );

    const unpaidCount = filtered.filter((ticket) => ticket.status === "Picked Up / Closed" && ticket.payment_status !== "paid").length;
    const openCount = filtered.filter((ticket) => ticket.status !== "Picked Up / Closed").length;

    const bulkActions = [
        {
            key: "copy-ticket-numbers",
            label: "Copy Ticket Numbers",
            onClick: (rows: TicketSummary[]) => {
                const values = rows.map((row) => row.ticket_number).join(", ");
                if (values) {
                    void navigator.clipboard?.writeText(values);
                }
            },
        },
    ];

    const columns = [
        {
            key: "ticket_number",
            header: "Ticket",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.ticket_number,
            render: (ticket: TicketSummary) => <Link to={`/tickets/${ticket.id}`}>{ticket.ticket_number}</Link>,
        },
        {
            key: "customer",
            header: "Customer",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.customer_name,
            render: (ticket: TicketSummary) => (
                <div>
                    <Link to={`/customers/${ticket.customer_id}`}>{ticket.customer_name}</Link>
                    <div style={metaStyle}>{formatPhone(ticket.customer_phone)}</div>
                </div>
            ),
        },
        {
            key: "device",
            header: "Device",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.device_label,
            render: (ticket: TicketSummary) => <strong>{ticket.device_label}</strong>,
        },
        {
            key: "issue",
            header: "Issue",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.issue_category,
            render: (ticket: TicketSummary) => ticket.issue_category,
        },
        {
            key: "status",
            header: "Status",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.status,
            render: (ticket: TicketSummary) => ticket.status,
        },
        {
            key: "balance",
            header: "Balance",
            sortable: true,
            sortValue: (ticket: TicketSummary) => Number(ticket.status === "Picked Up / Closed" && ticket.payment_status !== "paid" ? ticket.final_price ?? ticket.estimated_price ?? 0 : 0),
            render: (ticket: TicketSummary) => {
                if (ticket.status !== "Picked Up / Closed" || ticket.payment_status === "paid") {
                    return "Paid";
                }
                const due = Math.max(Number(ticket.final_price ?? ticket.estimated_price ?? 0), 0);
                return formatMoney(due, "$0.00");
            },
        },
        {
            key: "updated_at",
            header: "Updated",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.updated_at,
            render: (ticket: TicketSummary) => formatDeskDateTime(ticket.updated_at),
        },
    ];

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Ticket Management"
                title="Tickets"
                description="Compact ticket board for fast search, status checks, and payment follow-up."
                actions={
                    <div style={{ ...t.formActionsRow, gap: "8px" }}>
                        <Link to="/intake" style={{ ...t.primaryBtn, textDecoration: "none" }}>+ New Repair</Link>
                    </div>
                }
            />

            <div style={t.fieldGridTwoCompact}>
                <div style={summaryTileStyle}>
                    <div style={summaryLabelStyle}>Visible Tickets</div>
                    <div style={summaryValueStyle}>{filtered.length}</div>
                </div>
                <div style={summaryTileStyle}>
                    <div style={summaryLabelStyle}>Open Flow</div>
                    <div style={summaryValueStyle}>{openCount}</div>
                </div>
                <div style={summaryTileStyle}>
                    <div style={summaryLabelStyle}>Unpaid</div>
                    <div style={summaryValueStyle}>{unpaidCount}</div>
                </div>
            </div>

            <div style={ticketsWorkbenchStyle}>
                <SectionCard title="Search and status filters" compact>
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <ScannerInput
                            value={search}
                            onChange={setSearch}
                            onScanSubmit={setSearch}
                            placeholder="Search ticket, customer, phone, device, or issue"
                        />
                        <div style={{ ...t.formActionsRow, gap: "8px" }}>
                            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={t.input}>
                                <option value="">All statuses</option>
                                {statuses.map((status) => (
                                    <option key={status} value={status}>
                                        {status}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>
                </SectionCard>

                <SectionCard title="Saved views" compact tone="soft">
                    <div style={{ ...t.formStack, gap: "8px" }}>
                        <div style={{ ...t.formActionsRow, gap: "8px" }}>
                            <input
                                value={viewName}
                                onChange={(event) => setViewName(event.target.value)}
                                placeholder="Saved view name"
                                style={{ ...t.input, flex: "1 1 180px", minWidth: 0 }}
                            />
                            <button
                                type="button"
                                style={t.secondaryBtn}
                                onClick={() => {
                                    saveTicketView(viewName);
                                    setViewName("");
                                }}
                            >
                                Save view
                            </button>
                        </div>
                        <div style={{ ...t.formActionsRow, gap: "6px" }}>
                            {Object.keys(ticketSavedViews).length === 0 ? <span style={t.meta}>No saved views yet.</span> : null}
                            {Object.keys(ticketSavedViews).map((name) => (
                                <div key={name} style={{ ...t.formActionsRow, gap: "4px" }}>
                                    <button type="button" style={t.miniBtn} onClick={() => applyTicketView(name)}>{name}</button>
                                    <button type="button" aria-label={`Delete saved view ${name}`} style={t.miniBtn} onClick={() => deleteTicketView(name)}>x</button>
                                </div>
                            ))}
                        </div>
                    </div>
                </SectionCard>
            </div>

            <SectionCard title="Ticket list" compact>
                <LoadingBoundary loading={isLoading} error={error instanceof Error ? error.message : null} loadingMessage="Loading tickets…">
                    <DataTable
                        rows={filtered}
                        columns={columns}
                        page={page}
                        pageSize={15}
                        onPageChange={setPage}
                        bulkActions={bulkActions}
                        rowActions={(ticket: TicketSummary) => (
                            <div style={{ display: "flex", gap: "6px", flexWrap: "nowrap", whiteSpace: "nowrap" }}>
                                <Link to={`/tickets/${ticket.id}`} style={{ ...t.miniBtn, textDecoration: "none" }}>Open</Link>
                                <button
                                    type="button"
                                    style={t.miniBtn}
                                    onClick={() => {
                                        if (ticket.customer_phone) {
                                            void navigator.clipboard?.writeText(formatPhone(ticket.customer_phone));
                                        }
                                    }}
                                >
                                    Copy phone
                                </button>
                            </div>
                        )}
                    />
                </LoadingBoundary>
            </SectionCard>
        </section>
    );
}

const metaStyle = t.meta;

const ticketsWorkbenchStyle = {
    display: "grid",
    gap: "12px",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
};

const summaryTileStyle = {
    ...t.subCard,
    display: "grid",
    gap: "4px",
    borderRadius: "14px",
};

const summaryLabelStyle = {
    color: "#48707b",
    fontSize: "0.76rem",
    fontWeight: 800,
    letterSpacing: "0.08em",
    textTransform: "uppercase" as const,
};

const summaryValueStyle = {
    color: "#123943",
    fontSize: "1.5rem",
    fontWeight: 800,
};
