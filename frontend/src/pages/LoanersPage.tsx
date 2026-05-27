import { useState } from "react";
import * as t from "../styles/theme";
import { useAsyncData } from "../hooks/useAsyncData";

import {
    checkoutLoaner,
    createLoaner,
    fetchLoaners,
    returnLoaner,
    type LoanerPhone,
    updateLoanerStatus,
} from "../api/tickets";

export default function LoanersPage() {
    const [statusFilter, setStatusFilter] = useState("");
    const [actionError, setActionError] = useState<string | null>(null);
    const [refreshKey, setRefreshKey] = useState(0);
    const [createForm, setCreateForm] = useState({
        loaner_code: "",
        manufacturer: "",
        model: "",
        carrier_compatibility: "",
        charger_type: "",
        sim_type: "",
        filter_status: "",
        condition_current: "",
        default_deposit: "",
        notes: "",
    });
    const [checkoutForm, setCheckoutForm] = useState({
        loaner_id: "",
        ticket_id: "",
        customer_id: "",
        expected_return_date: "",
        condition_out: "",
        charger_included: false,
        sim_moved: false,
        outgoing_call_tested: false,
        incoming_call_tested: false,
        deposit_amount: "",
        checkout_staff: "",
        agreement_signed: false,
    });
    const [returnForm, setReturnForm] = useState({
        loaner_id: "",
        condition_returned: "",
        charger_returned: null as boolean | null,
        deposit_refunded: "",
        deposit_deducted: "",
        deduction_reason: "",
        return_staff: "",
        next_status: "Returned Needs Reset",
    });

    const { data: loaners = [], error: loadError } = useAsyncData<LoanerPhone[]>(
        () => fetchLoaners(statusFilter || undefined),
        [statusFilter, refreshKey]
    );

    const error = actionError ?? loadError;

    function triggerRefresh() {
        setRefreshKey((current) => current + 1);
    }

    async function handleCreateLoaner() {
        try {
            await createLoaner(createForm);
            setCreateForm({
                loaner_code: "",
                manufacturer: "",
                model: "",
                carrier_compatibility: "",
                charger_type: "",
                sim_type: "",
                filter_status: "",
                condition_current: "",
                default_deposit: "",
                notes: "",
            });
            setActionError(null);
            triggerRefresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Failed to create loaner");
        }
    }

    async function handleCheckout() {
        if (!checkoutForm.loaner_id || !checkoutForm.ticket_id || !checkoutForm.customer_id) {
            setActionError("Loaner, ticket, and customer IDs are required for checkout.");
            return;
        }
        try {
            await checkoutLoaner(Number(checkoutForm.loaner_id), checkoutForm);
            setCheckoutForm({
                loaner_id: "",
                ticket_id: "",
                customer_id: "",
                expected_return_date: "",
                condition_out: "",
                charger_included: false,
                sim_moved: false,
                outgoing_call_tested: false,
                incoming_call_tested: false,
                deposit_amount: "",
                checkout_staff: "",
                agreement_signed: false,
            });
            setActionError(null);
            triggerRefresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Failed to checkout loaner");
        }
    }

    async function handleReturn() {
        if (!returnForm.loaner_id) {
            setActionError("Loaner ID is required for return.");
            return;
        }
        try {
            await returnLoaner(Number(returnForm.loaner_id), returnForm);
            setReturnForm({
                loaner_id: "",
                condition_returned: "",
                charger_returned: null,
                deposit_refunded: "",
                deposit_deducted: "",
                deduction_reason: "",
                return_staff: "",
                next_status: "Returned Needs Reset",
            });
            setActionError(null);
            triggerRefresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Failed to return loaner");
        }
    }

    async function setQuickStatus(loanerId: number, status: string) {
        try {
            await updateLoanerStatus(loanerId, status);
            setActionError(null);
            triggerRefresh();
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Failed to update loaner status");
        }
    }

    return (
        <section style={t.pageWrap}>
            <div>
                <h2 style={{ margin: 0 }}>Loaners</h2>
                <p style={{ ...copyStyle, marginTop: "4px", marginBottom: 0, fontSize: "0.9rem" }}>Phase 2 loaner lifecycle: inventory, checkout, return, deposit tracking, and status handling.</p>
            </div>

            <div style={panelStyle}>
                <div style={t.formActionsRow}>
                    <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} style={inputStyle}>
                        <option value="">All statuses</option>
                        {statusOptions.map((status) => (
                            <option key={status} value={status}>{status}</option>
                        ))}
                    </select>
                </div>
                {error ? <p style={{ ...copyStyle, color: "#9b2c2c" }}>{error}</p> : null}
            </div>

            <div style={gridStyle}>
                <div style={panelStyle}>
                    <h3 style={headingStyle}>Add loaner</h3>
                    <Field label="Loaner code" value={createForm.loaner_code} onChange={(value) => setCreateForm({ ...createForm, loaner_code: value })} />
                    <Field label="Manufacturer" value={createForm.manufacturer} onChange={(value) => setCreateForm({ ...createForm, manufacturer: value })} />
                    <Field label="Model" value={createForm.model} onChange={(value) => setCreateForm({ ...createForm, model: value })} />
                    <Field label="Carrier compatibility" value={createForm.carrier_compatibility} onChange={(value) => setCreateForm({ ...createForm, carrier_compatibility: value })} />
                    <Field label="Default deposit" value={createForm.default_deposit} onChange={(value) => setCreateForm({ ...createForm, default_deposit: value })} />
                    <button type="button" style={buttonStyle} onClick={handleCreateLoaner}>Create loaner</button>
                </div>

                <div style={panelStyle}>
                    <h3 style={headingStyle}>Checkout loaner</h3>
                    <Field label="Loaner ID" value={checkoutForm.loaner_id} onChange={(value) => setCheckoutForm({ ...checkoutForm, loaner_id: value })} />
                    <Field label="Ticket ID" value={checkoutForm.ticket_id} onChange={(value) => setCheckoutForm({ ...checkoutForm, ticket_id: value })} />
                    <Field label="Customer ID" value={checkoutForm.customer_id} onChange={(value) => setCheckoutForm({ ...checkoutForm, customer_id: value })} />
                    <Field label="Expected return (ISO datetime)" value={checkoutForm.expected_return_date} onChange={(value) => setCheckoutForm({ ...checkoutForm, expected_return_date: value })} />
                    <Field label="Condition out" value={checkoutForm.condition_out} onChange={(value) => setCheckoutForm({ ...checkoutForm, condition_out: value })} />
                    <Field label="Deposit amount" value={checkoutForm.deposit_amount} onChange={(value) => setCheckoutForm({ ...checkoutForm, deposit_amount: value })} />
                    <Field label="Checkout staff" value={checkoutForm.checkout_staff} onChange={(value) => setCheckoutForm({ ...checkoutForm, checkout_staff: value })} />
                    <CheckboxField label="Charger included" checked={checkoutForm.charger_included} onChange={(checked) => setCheckoutForm({ ...checkoutForm, charger_included: checked })} />
                    <CheckboxField label="SIM moved" checked={checkoutForm.sim_moved} onChange={(checked) => setCheckoutForm({ ...checkoutForm, sim_moved: checked })} />
                    <CheckboxField label="Outgoing call tested" checked={checkoutForm.outgoing_call_tested} onChange={(checked) => setCheckoutForm({ ...checkoutForm, outgoing_call_tested: checked })} />
                    <CheckboxField label="Incoming call tested" checked={checkoutForm.incoming_call_tested} onChange={(checked) => setCheckoutForm({ ...checkoutForm, incoming_call_tested: checked })} />
                    <CheckboxField label="Agreement signed" checked={checkoutForm.agreement_signed} onChange={(checked) => setCheckoutForm({ ...checkoutForm, agreement_signed: checked })} />
                    <button type="button" style={buttonStyle} onClick={handleCheckout}>Checkout</button>
                </div>

                <div style={panelStyle}>
                    <h3 style={headingStyle}>Return loaner</h3>
                    <Field label="Loaner ID" value={returnForm.loaner_id} onChange={(value) => setReturnForm({ ...returnForm, loaner_id: value })} />
                    <Field label="Condition returned" value={returnForm.condition_returned} onChange={(value) => setReturnForm({ ...returnForm, condition_returned: value })} />
                    <Field label="Deposit refunded" value={returnForm.deposit_refunded} onChange={(value) => setReturnForm({ ...returnForm, deposit_refunded: value })} />
                    <Field label="Deposit deducted" value={returnForm.deposit_deducted} onChange={(value) => setReturnForm({ ...returnForm, deposit_deducted: value })} />
                    <Field label="Deduction reason" value={returnForm.deduction_reason} onChange={(value) => setReturnForm({ ...returnForm, deduction_reason: value })} />
                    <Field label="Return staff" value={returnForm.return_staff} onChange={(value) => setReturnForm({ ...returnForm, return_staff: value })} />
                    <label style={labelStyle}>
                        <span>Charger returned</span>
                        <select
                            value={returnForm.charger_returned === null ? "unknown" : returnForm.charger_returned ? "yes" : "no"}
                            onChange={(event) =>
                                setReturnForm({
                                    ...returnForm,
                                    charger_returned: event.target.value === "unknown" ? null : event.target.value === "yes",
                                })
                            }
                            style={inputStyle}
                        >
                            <option value="unknown">Unknown</option>
                            <option value="yes">Yes</option>
                            <option value="no">No</option>
                        </select>
                    </label>
                    <label style={labelStyle}>
                        <span>Next status</span>
                        <select value={returnForm.next_status} onChange={(event) => setReturnForm({ ...returnForm, next_status: event.target.value })} style={inputStyle}>
                            <option value="Available">Available</option>
                            <option value="Returned Needs Reset">Returned Needs Reset</option>
                            <option value="Returned Needs Cleaning">Returned Needs Cleaning</option>
                            <option value="Damaged">Damaged</option>
                            <option value="Lost">Lost</option>
                            <option value="Retired">Retired</option>
                        </select>
                    </label>
                    <button type="button" style={buttonStyle} onClick={handleReturn}>Return</button>
                </div>
            </div>

            <div style={panelStyle}>
                <h3 style={headingStyle}>Loaner inventory</h3>
                {loaners.length === 0 ? (
                    <p style={copyStyle}>No loaners in inventory yet.</p>
                ) : (
                    <div style={{ display: "grid", gap: "12px" }}>
                        {loaners.map((loaner) => (
                            <div key={loaner.id} style={loanerCardStyle}>
                                <div>
                                    <strong>{loaner.loaner_code}</strong>
                                    <div style={metaStyle}>{loaner.manufacturer ? `${loaner.manufacturer} ` : ""}{loaner.model}</div>
                                    <div style={metaStyle}>Status: {loaner.status}</div>
                                    <div style={metaStyle}>Default deposit: ${loaner.default_deposit}</div>
                                </div>
                                <div style={{ ...t.formActionsRow, gap: "8px" }}>
                                    <button type="button" style={miniButtonStyle} onClick={() => setQuickStatus(loaner.id, "Returned Needs Reset")}>Needs reset</button>
                                    <button type="button" style={miniButtonStyle} onClick={() => setQuickStatus(loaner.id, "Returned Needs Cleaning")}>Needs cleaning</button>
                                    <button type="button" style={miniButtonStyle} onClick={() => setQuickStatus(loaner.id, "Available")}>Set available</button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </section>
    );
}

function Field(props: { label: string; value: string; onChange: (value: string) => void }) {
    return (
        <label style={labelStyle}>
            <span>{props.label}</span>
            <input value={props.value} onChange={(event) => props.onChange(event.target.value)} style={inputStyle} />
        </label>
    );
}

function CheckboxField(props: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
    return (
        <label style={{ ...labelStyle, ...t.formActionsRow, gap: "8px" }}>
            <input type="checkbox" checked={props.checked} onChange={(event) => props.onChange(event.target.checked)} />
            <span>{props.label}</span>
        </label>
    );
}

// ─── theme aliases ───
const panelStyle = t.panel;
const copyStyle = t.copy;
const headingStyle = { marginTop: 0 };
const labelStyle = { ...t.label, marginBottom: "10px" } as const;
const inputStyle = t.input;
const buttonStyle = { ...t.primaryBtn, marginTop: "10px" } as const;
const miniButtonStyle = t.miniBtn;
const metaStyle = t.meta;
const gridStyle = {
    ...t.detailGrid,
    display: "grid",
    gap: "18px",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    minWidth: 0,
};

const loanerCardStyle = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
    gap: "14px",
    alignItems: "start",
    borderRadius: "14px",
    background: "#f8fbfa",
    border: "1px solid rgba(29, 43, 40, 0.1)",
    padding: "14px 16px",
    minWidth: 0,
};

const statusOptions = [
    "Available",
    "Checked Out",
    "Returned Needs Reset",
    "Returned Needs Cleaning",
    "Damaged",
    "Lost",
    "Retired",
];
