import { Link, useParams } from 'react-router-dom';

import { fetchLoanerAgreement, type LoanerAgreement } from '../api/tickets';
import { fetchLoanerAgreementDefaults } from '../api/system';
import { useAsyncData } from '../hooks/useAsyncData';
import * as t from '../styles/theme';

export default function LoanerAgreementPrintPage() {
    const { ticketId = '' } = useParams();
    const { data: agreement, error } = useAsyncData<LoanerAgreement>(() => fetchLoanerAgreement(ticketId), [ticketId]);
    const { data: defaults } = useAsyncData(() => fetchLoanerAgreementDefaults(), []);

    if (error) {
        return <section style={t.panel}><p style={{ color: '#9b2c2c' }}>{error}</p></section>;
    }

    if (!agreement) {
        return <section style={t.panel}><p>Loading loaner agreement…</p></section>;
    }

    return (
        <section style={{ ...t.pageWrap, maxWidth: '960px', margin: '0 auto', paddingBottom: '32px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
                <div>
                    <h1 style={{ margin: 0, color: '#173f37' }}>Loaner agreement</h1>
                    <p style={{ ...t.copy, marginTop: '6px', marginBottom: 0 }}>Print-friendly checkout acknowledgement for the active or latest loaner assignment.</p>
                </div>
                <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                    <button type="button" style={t.primaryBtn} onClick={() => window.print()}>Print agreement</button>
                    <Link to={`/tickets/${agreement.ticket_id}`} style={{ ...t.secondaryBtn, textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>Back to ticket</Link>
                </div>
            </div>

            <div style={{ ...t.panel, marginTop: '18px' }}>
                <div style={{ display: 'grid', gap: '10px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))' }}>
                    <InfoBlock label="Ticket" value={agreement.ticket_number} />
                    <InfoBlock label="Customer" value={agreement.customer_name} />
                    <InfoBlock label="Phone" value={agreement.customer_phone || 'Not set'} />
                    <InfoBlock label="Repair device" value={agreement.device_label} />
                    <InfoBlock label="Loaner device" value={`${agreement.loaner_code} · ${agreement.loaner_device_label}`} />
                    <InfoBlock label="Checked out" value={new Date(agreement.date_out).toLocaleString()} />
                </div>
            </div>

            <div style={{ ...t.detailGrid, marginTop: '18px' }}>
                <div style={t.panel}>
                    <h3 style={{ marginTop: 0 }}>Loaner condition</h3>
                    <PrintRow label="Issue category" value={agreement.issue_category} />
                    <PrintRow label="Condition out" value={agreement.condition_out || 'Not set'} />
                    <PrintRow label="Expected return" value={agreement.expected_return_date ? new Date(agreement.expected_return_date).toLocaleString() : 'Open-ended'} />
                    <PrintRow label="Deposit" value={`$${agreement.deposit_amount.toFixed(2)}`} />
                    <PrintRow label="Checkout staff" value={agreement.checkout_staff || 'Not set'} />
                    <PrintRow label="Agreement signed" value={agreement.agreement_signed ? 'Yes' : 'No'} />
                </div>

                <div style={t.panel}>
                    <h3 style={{ marginTop: 0 }}>Functional checks</h3>
                    <PrintRow label="Charger included" value={agreement.charger_included ? 'Yes' : 'No'} />
                    <PrintRow label="SIM moved" value={agreement.sim_moved ? 'Yes' : 'No'} />
                    <PrintRow label="Outgoing call tested" value={agreement.outgoing_call_tested ? 'Yes' : 'No'} />
                    <PrintRow label="Incoming call tested" value={agreement.incoming_call_tested ? 'Yes' : 'No'} />
                    <PrintRow label="Agreement status" value={agreement.status} />
                </div>
            </div>

            <div style={{ ...t.panel, marginTop: '18px' }}>
                <h3 style={{ marginTop: 0 }}>Acknowledgement</h3>
                <p style={t.copy}>{defaults?.responsibility_text ?? 'Customer accepts responsibility for the loaner device and listed accessories.'}</p>
                <p style={t.copy}>{defaults?.return_policy_text ?? 'Loaner device should be returned in similar condition when repair pickup is completed.'}</p>
                <p style={{ ...t.meta, marginTop: '8px' }}>{defaults?.signature_note_text ?? 'By signing, both parties acknowledge the checkout details above.'}</p>
                <div style={{ display: 'grid', gap: '28px', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', marginTop: '24px' }}>
                    <SignatureLine label="Customer signature" />
                    <SignatureLine label="Staff signature" />
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