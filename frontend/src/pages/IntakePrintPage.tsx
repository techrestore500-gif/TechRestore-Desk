import { Link, useParams } from 'react-router-dom';

import { fetchTicket, type TicketDetail } from '../api/tickets';
import { useAsyncData } from '../hooks/useAsyncData';
import * as t from '../styles/theme';

export default function IntakePrintPage() {
    const { ticketId = '' } = useParams();
    const { data: ticket, error } = useAsyncData<TicketDetail>(() => fetchTicket(ticketId), [ticketId]);

    if (error) {
        return <section style={t.panel}><p style={{ color: '#9b2c2c' }}>{error}</p></section>;
    }

    if (!ticket) {
        return <section style={t.panel}><p>Loading intake form…</p></section>;
    }

    return (
        <section style={{ ...t.pageWrap, maxWidth: '960px', margin: '0 auto', paddingBottom: '32px' }}>
            <Header
                title="Intake form"
                subtitle="Print-friendly customer intake and device condition summary."
                ticketId={ticket.id}
            />

            <div style={{ ...t.panel, marginTop: '18px' }}>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
                    <InfoBlock label="Ticket" value={ticket.ticket_number} />
                    <InfoBlock label="Customer" value={ticket.customer_name} />
                    <InfoBlock label="Phone" value={ticket.customer_phone || ticket.customer_alternate_phone || 'Not set'} />
                    <InfoBlock label="Device" value={ticket.device_label} />
                    <InfoBlock label="Issue" value={ticket.issue_category} />
                    <InfoBlock label="Intake date" value={new Date(ticket.intake_date).toLocaleString()} />
                </div>
            </div>

            <div style={{ ...t.detailGrid, marginTop: '18px' }}>
                <div style={t.panel}>
                    <h3 style={{ marginTop: 0 }}>Device condition</h3>
                    <PrintRow label="Carrier" value={ticket.carrier || 'Not set'} />
                    <PrintRow label="SIM type" value={ticket.sim_type || 'Not set'} />
                    <PrintRow label="IMEI / serial" value={ticket.imei_serial || 'Not set'} />
                    <PrintRow label="Color" value={ticket.device_color || 'Not set'} />
                    <PrintRow label="Filter status" value={ticket.filter_status || 'Not set'} />
                    <PrintRow label="Condition summary" value={ticket.condition_summary || 'Not set'} />
                    <PrintRow label="Water damage" value={ticket.water_damage_status} />
                    <PrintRow label="Dropped" value={ticket.dropped_status} />
                    <PrintRow label="Powers on" value={ticket.powers_on_status} />
                    <PrintRow label="Charges" value={ticket.charges_status} />
                </div>

                <div style={t.panel}>
                    <h3 style={{ marginTop: 0 }}>Customer approval notes</h3>
                    <PrintRow label="Issue description" value={ticket.issue_description || 'Not set'} />
                    <PrintRow label="Approval limit" value={ticket.customer_approval_limit ? `$${ticket.customer_approval_limit.toFixed(2)}` : 'Not set'} />
                    <PrintRow label="Must call before repair" value={ticket.must_call_before_repair ? 'Yes' : 'No'} />
                    <PrintRow label="Replacement acceptable" value={ticket.customer_prefers_replacement_if_high ? 'Yes' : 'No'} />
                    <PrintRow label="Diagnostic fee" value={`$${Number(ticket.diagnostic_fee ?? 0).toFixed(2)}`} />
                    <PrintRow label="Intake staff" value={ticket.intake_staff || 'Not set'} />
                </div>
            </div>

            <div style={{ ...t.panel, marginTop: '18px' }}>
                <h3 style={{ marginTop: 0 }}>Acknowledgement</h3>
                <p style={t.copy}>
                    Device received for diagnostic and repair evaluation. Standard v1 workflow does not promise soldering-based charging-port or microphone repair.
                </p>
                <div style={{ display: 'grid', gap: '28px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', marginTop: '24px' }}>
                    <SignatureLine label="Customer signature" />
                    <SignatureLine label="Staff signature" />
                </div>
            </div>
        </section>
    );
}

function Header(props: { title: string; subtitle: string; ticketId: number }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
            <div>
                <h1 style={{ margin: 0, color: '#173f37' }}>{props.title}</h1>
                <p style={{ ...t.copy, marginTop: '6px', marginBottom: 0 }}>{props.subtitle}</p>
            </div>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button type="button" style={t.primaryBtn} onClick={() => window.print()}>Print</button>
                <Link to={`/tickets/${props.ticketId}`} style={{ ...t.secondaryBtn, textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>Back to ticket</Link>
            </div>
        </div>
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

function PrintRow(props: { label: string; value: string }) {
    return (
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', padding: '10px 0', borderBottom: '1px solid rgba(29, 43, 40, 0.08)' }}>
            <strong>{props.label}</strong>
            <span style={{ textAlign: 'right' }}>{props.value}</span>
        </div>
    );
}

function SignatureLine(props: { label: string }) {
    return (
        <div>
            <div style={{ borderBottom: '1px solid rgba(29, 43, 40, 0.35)', minHeight: '34px' }} />
            <div style={{ ...t.meta, marginTop: '8px' }}>{props.label}</div>
        </div>
    );
}