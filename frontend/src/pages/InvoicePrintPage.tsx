import { Link, useParams } from 'react-router-dom';

import { fetchTicket, type TicketDetail } from '../api/tickets';
import { useAsyncData } from '../hooks/useAsyncData';
import * as t from '../styles/theme';

export default function InvoicePrintPage() {
    const { ticketId = '' } = useParams();
    const { data: ticket, error } = useAsyncData<TicketDetail>(() => fetchTicket(ticketId), [ticketId]);

    if (error) {
        return <section style={t.panel}><p style={{ color: '#9b2c2c' }}>{error}</p></section>;
    }

    if (!ticket) {
        return <section style={t.panel}><p>Loading invoice…</p></section>;
    }

    const invoiceTotal = Number(ticket.final_price ?? ticket.estimated_price ?? 0);

    return (
        <section style={{ ...t.pageWrap, maxWidth: '960px', margin: '0 auto', paddingBottom: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                <div>
                    <h1 style={{ margin: 0, color: '#173f37' }}>Invoice</h1>
                    <p style={{ ...t.copy, marginTop: '6px', marginBottom: 0 }}>Print-friendly ticket closeout summary.</p>
                </div>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button type="button" style={t.primaryBtn} onClick={() => window.print()}>Print invoice</button>
                    <Link to={`/tickets/${ticket.id}`} style={{ ...t.secondaryBtn, textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>Back to ticket</Link>
                </div>
            </div>

            <div style={{ ...t.panel, marginTop: '18px' }}>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
                    <InfoBlock label="Ticket" value={ticket.ticket_number} />
                    <InfoBlock label="Customer" value={ticket.customer_name} />
                    <InfoBlock label="Phone" value={ticket.customer_phone || ticket.customer_alternate_phone || 'Not set'} />
                    <InfoBlock label="Device" value={ticket.device_label} />
                    <InfoBlock label="Issue" value={ticket.issue_category} />
                    <InfoBlock label="Status" value={ticket.status} />
                </div>
            </div>

            <div style={{ ...t.panel, marginTop: '18px' }}>
                <h3 style={{ marginTop: 0 }}>Repair actions</h3>
                {ticket.repair_actions.length === 0 ? (
                    <p style={t.copy}>No repair actions were recorded on this ticket.</p>
                ) : (
                    <div style={{ display: 'grid', gap: '10px' }}>
                        {ticket.repair_actions.map((action) => (
                            <div key={action.id} style={t.subCard}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                                    <strong>{action.repair_category_name ?? 'Repair action'}</strong>
                                    <span>${Number(action.final_price ?? action.calculated_price ?? 0).toFixed(2)}</span>
                                </div>
                                <div style={{ ...t.meta, marginTop: '6px' }}>{action.status}</div>
                                <div style={{ marginTop: '8px' }}>{action.action_description || 'No description'}</div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div style={{ ...t.panel, marginTop: '18px' }}>
                <h3 style={{ marginTop: 0 }}>Summary</h3>
                <div style={{ display: 'grid', gap: '10px' }}>
                    <SummaryRow label="Diagnostic fee" value={`$${Number(ticket.diagnostic_fee ?? 0).toFixed(2)}`} />
                    <SummaryRow label="Final total" value={`$${invoiceTotal.toFixed(2)}`} />
                    <SummaryRow label="Closeout status" value={ticket.status} />
                </div>
            </div>
        </section>
    );
}

function InfoBlock(props: { label: string; value: string }) {
    return (
        <div style={t.subCard}>
            <div style={t.meta}>{props.label}</div>
            <strong style={{ display: 'block', marginTop: '6px' }}>{props.value}</strong>
        </div>
    );
}

function SummaryRow(props: { label: string; value: string }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '10px 0', borderBottom: '1px solid rgba(29, 43, 40, 0.08)' }}>
            <strong>{props.label}</strong>
            <span>{props.value}</span>
        </div>
    );
}
