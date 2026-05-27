import { Link, useParams } from "react-router-dom";

import { fetchCustomer, fetchCustomerTickets, type Customer, type TicketSummary } from "../api/tickets";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

export default function CustomerDetailPage() {
    const { customerId = "" } = useParams();

    const { data, error } = useAsyncData<{ customer: Customer; tickets: TicketSummary[] }>(async () => {
        const numericId = Number(customerId);
        const [customer, tickets] = await Promise.all([fetchCustomer(numericId), fetchCustomerTickets(numericId)]);
        return { customer, tickets };
    }, [customerId]);

    if (error) {
        return <section style={t.panel}><p style={{ color: "#9b2c2c" }}>{error}</p></section>;
    }

    if (!data) {
        return <section style={t.panel}><p>Loading customer history...</p></section>;
    }

    const { customer, tickets } = data;
    const openTickets = tickets.filter((ticket) => ticket.status !== "Picked Up / Closed").length;
    const paidTickets = tickets.filter((ticket) => ticket.payment_status === "paid").length;
    const latestTicket = tickets[0] ?? null;

    return (
        <section style={t.pageWrap}>
            <div style={headerStyle}>
                <div>
                    <div style={{ color: "#56706a", fontWeight: 700, letterSpacing: "0.08em", textTransform: "uppercase", fontSize: "0.76rem" }}>
                        Customer Record
                    </div>
                    <h2 style={{ margin: "6px 0 0" }}>{customer.full_name}</h2>
                    <p style={{ ...t.pageIntro, marginTop: "6px" }}>
                        {customer.primary_phone || customer.alternate_phone || "No phone on file"}
                        {customer.email ? ` · ${customer.email}` : ""}
                    </p>
                </div>
                <div style={{ display: "grid", gap: "8px", textAlign: "right" }}>
                    <div style={summaryPillStyle}>Tickets: {tickets.length}</div>
                    <div style={summaryPillStyle}>Open: {openTickets}</div>
                    <div style={summaryPillStyle}>Paid: {paidTickets}</div>
                </div>
            </div>

            <div style={t.panel}>
                <h3 style={t.heading}>Customer Notes</h3>
                <p style={{ ...t.copy, marginBottom: 0 }}>{customer.notes || "No customer notes on file."}</p>
            </div>

            <div style={detailGridStyle}>
                <div style={t.panel}>
                    <h3 style={t.heading}>Contact Details</h3>
                    <DetailRow label="Primary Phone" value={customer.primary_phone || "Not set"} />
                    <DetailRow label="Alternate Phone" value={customer.alternate_phone || "Not set"} />
                    <DetailRow label="Email" value={customer.email || "Not set"} />
                    <DetailRow label="Created" value={new Date(customer.created_at).toLocaleString()} />
                    <DetailRow label="Updated" value={new Date(customer.updated_at).toLocaleString()} />
                </div>

                <div style={t.panel}>
                    <h3 style={t.heading}>Repair History</h3>
                    {latestTicket ? (
                        <div style={{ ...t.subCard, marginBottom: "12px" }}>
                            <strong>Latest</strong>
                            <div style={t.meta}>{latestTicket.ticket_number} · {latestTicket.device_label}</div>
                            <div style={t.meta}>{latestTicket.status} · {latestTicket.payment_status}</div>
                        </div>
                    ) : null}
                    {tickets.length === 0 ? (
                        <p style={t.meta}>No tickets recorded for this customer.</p>
                    ) : (
                        <div style={{ display: "grid", gap: "10px" }}>
                            {tickets.map((ticket) => (
                                <article key={ticket.id} style={ticketRowStyle}>
                                    <div style={{ display: "flex", justifyContent: "space-between", gap: "8px", flexWrap: "wrap" }}>
                                        <Link to={`/tickets/${ticket.id}`} style={{ textDecoration: "none", color: "#163731", fontWeight: 800 }}>
                                            {ticket.ticket_number}
                                        </Link>
                                        <span style={statusBadgeStyle}>{ticket.status}</span>
                                    </div>
                                    <div style={{ ...t.copy, marginTop: "6px", marginBottom: 0 }}>{ticket.device_label}</div>
                                    <div style={t.meta}>{ticket.issue_category}</div>
                                    <div style={t.meta}>
                                        Payment: {ticket.payment_status}
                                        {ticket.final_price != null ? ` · $${ticket.final_price.toFixed(2)}` : ""}
                                    </div>
                                    <div style={t.meta}>Updated {new Date(ticket.updated_at).toLocaleString()}</div>
                                </article>
                            ))}
                        </div>
                    )}
                </div>
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
    gap: "12px",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
};

const ticketRowStyle = {
    borderRadius: "12px",
    border: "1px solid rgba(29,43,40,0.12)",
    background: "#f8f3ea",
    padding: "10px 12px",
};

const statusBadgeStyle = {
    borderRadius: "999px",
    border: "1px solid rgba(29,43,40,0.12)",
    background: "#ffffff",
    padding: "4px 9px",
    fontSize: "0.78rem",
    fontWeight: 700,
};

const summaryPillStyle = {
    borderRadius: "999px",
    border: "1px solid rgba(29,43,40,0.12)",
    background: "#ffffff",
    padding: "8px 12px",
    fontWeight: 700,
};
