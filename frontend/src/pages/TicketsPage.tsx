import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { type TicketSummary } from "../api/tickets";
import { LoadingBoundary } from "../components/LoadingBoundary";
import { ScannerInput } from "../components/ScannerInput";
import { DataTable } from "../components/table/DataTable";
import { PageHeader, SectionCard } from "../components/PageChrome";
import { useTicketsQuery } from "../hooks/queries/useTicketsQuery";
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
            render: (ticket: TicketSummary) => <Link to={`/customers/${ticket.customer_id}`}>{ticket.customer_name}</Link>,
        },
        {
            key: "device",
            header: "Device / Issue",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.device_label,
            render: (ticket: TicketSummary) => (
                <div>
                    <strong>{ticket.device_label}</strong>
                    <div style={metaStyle}>{ticket.issue_category}</div>
                </div>
            ),
        },
        {
            key: "status",
            header: "Status",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.status,
            render: (ticket: TicketSummary) => ticket.status,
        },
        {
            key: "payment_status",
            header: "Payment",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.payment_status,
            render: (ticket: TicketSummary) => ticket.payment_status,
        },
        {
            key: "intake_date",
            header: "Intake",
            sortable: true,
            sortValue: (ticket: TicketSummary) => ticket.intake_date,
            render: (ticket: TicketSummary) => formatDate(ticket.intake_date),
        },
    ];

    return (
        <section style={{ display: "grid", gap: "16px", width: "100%" }}>
            <PageHeader
                kicker="Ticket Management"
                title="Tickets"
                description="Search by ticket number, customer, phone, issue, or model."
            />

            <SectionCard title="Search and saved views" compact>
                <div style={{ ...t.formStack, gap: "8px" }}>
                    <ScannerInput
                        value={search}
                        onChange={setSearch}
                        onScanSubmit={setSearch}
                        placeholder="Search tickets"
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
                        <input
                            value={viewName}
                            onChange={(event) => setViewName(event.target.value)}
                            placeholder="Saved view name"
                            style={{ ...t.input, flex: "1 1 180px", minWidth: 0, maxWidth: "320px" }}
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
                        {Object.keys(ticketSavedViews).map((name) => (
                            <div key={name} style={{ ...t.formActionsRow, gap: "4px" }}>
                                <button type="button" style={t.miniBtn} onClick={() => applyTicketView(name)}>{name}</button>
                                <button type="button" style={t.miniBtn} onClick={() => deleteTicketView(name)}>x</button>
                            </div>
                        ))}
                    </div>
                </div>
            </SectionCard>

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
                                            void navigator.clipboard?.writeText(ticket.customer_phone);
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

function formatDate(value: string) {
    return new Date(value).toLocaleString();
}

const metaStyle = t.meta;
