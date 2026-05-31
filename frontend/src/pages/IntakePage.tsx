import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import {
    createQuickRepair,
    fetchCustomers,
    fetchTickets,
    updateVoicemail,
    type Customer,
    type PaymentStatus,
    type QuickRepairStatus,
    type TicketSummary,
} from "../api/tickets";
import { QUICK_REPAIR_STATUSES, QUICK_REPAIR_STATUS_COLORS } from "../lib/repairFlow";
import * as t from "../styles/theme";

type QuickFormState = {
    customerName: string;
    phoneNumber: string;
    deviceBrand: string;
    deviceModel: string;
    issueProblem: string;
    optionalNotes: string;
    estimatedCharge: string;
    paymentStatus: PaymentStatus;
    repairStatus: QuickRepairStatus;
};

const initialState: QuickFormState = {
    customerName: "",
    phoneNumber: "",
    deviceBrand: "",
    deviceModel: "",
    issueProblem: "",
    optionalNotes: "",
    estimatedCharge: "",
    paymentStatus: "unpaid",
    repairStatus: "New Intake",
};

export default function IntakePage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [form, setForm] = useState<QuickFormState>(initialState);
    const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
    const [customerMatches, setCustomerMatches] = useState<Customer[]>([]);
    const [recentTickets, setRecentTickets] = useState<TicketSummary[]>([]);
    const [voicemailId, setVoicemailId] = useState<number | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let ignore = false;

        void (async () => {
            try {
                const tickets = await fetchTickets();
                if (!ignore) {
                    setRecentTickets(tickets.slice(0, 150));
                }
            } catch {
                if (!ignore) {
                    setRecentTickets([]);
                }
            }
        })();

        return () => {
            ignore = true;
        };
    }, []);

    useEffect(() => {
        const caller = searchParams.get("caller") ?? "";
        const customer = searchParams.get("customer") ?? "";
        const voicemail = searchParams.get("voicemail");
        if (caller || customer) {
            setForm((current) => ({
                ...current,
                phoneNumber: caller || current.phoneNumber,
                customerName: customer || current.customerName,
            }));
        }
        if (voicemail) {
            const parsed = Number(voicemail);
            if (!Number.isNaN(parsed)) {
                setVoicemailId(parsed);
            }
        }
    }, [searchParams]);

    useEffect(() => {
        const query = form.customerName.trim();
        if (query.length < 2) {
            setCustomerMatches([]);
            return;
        }

        let ignore = false;
        const timer = window.setTimeout(() => {
            void (async () => {
                try {
                    const matches = await fetchCustomers(query);
                    if (!ignore) {
                        setCustomerMatches(matches.slice(0, 8));
                    }
                } catch {
                    if (!ignore) {
                        setCustomerMatches([]);
                    }
                }
            })();
        }, 120);

        return () => {
            ignore = true;
            window.clearTimeout(timer);
        };
    }, [form.customerName]);

    const deviceSuggestions = useMemo(() => {
        const fromRecent = new Set<string>();
        for (const ticket of recentTickets) {
            if (ticket.device_label) {
                fromRecent.add(ticket.device_label);
            }
            if (fromRecent.size >= 18) {
                break;
            }
        }

        if (selectedCustomer) {
            const customerDevices = recentTickets
                .filter((ticket) => ticket.customer_id === selectedCustomer.id)
                .map((ticket) => ticket.device_label)
                .filter(Boolean);
            for (const label of customerDevices) {
                fromRecent.add(label);
                if (fromRecent.size >= 18) {
                    break;
                }
            }
        }

        return Array.from(fromRecent);
    }, [recentTickets, selectedCustomer]);

    async function handleSubmit() {
        const requiredFields = [
            form.customerName.trim(),
            form.phoneNumber.trim(),
            form.deviceBrand.trim(),
            form.deviceModel.trim(),
            form.issueProblem.trim(),
        ];
        if (requiredFields.some((value) => value.length === 0)) {
            setError("Customer name, phone, device brand/model, and issue are required.");
            return;
        }

        setSubmitting(true);
        setError(null);

        try {
            const ticket = await createQuickRepair({
                customer_id: selectedCustomer?.id,
                customer_name: form.customerName,
                phone_number: form.phoneNumber,
                device_brand: form.deviceBrand,
                device_model: form.deviceModel,
                issue_problem: form.issueProblem,
                optional_notes: form.optionalNotes,
                estimated_charge: form.estimatedCharge.trim() ? Number(form.estimatedCharge) : null,
                payment_status: form.paymentStatus,
                repair_status: form.repairStatus,
            });
            if (voicemailId !== null) {
                await updateVoicemail(voicemailId, { ticket_id: ticket.id, status: "listened" });
            }
            navigate(`/tickets/${ticket.id}`);
        } catch (requestError) {
            setError(requestError instanceof Error ? requestError.message : "Unable to create repair ticket");
        } finally {
            setSubmitting(false);
        }
    }

    function applyCustomer(customer: Customer) {
        setSelectedCustomer(customer);
        setForm((current) => ({
            ...current,
            customerName: customer.full_name,
            phoneNumber: customer.primary_phone || customer.alternate_phone || current.phoneNumber,
        }));
        setCustomerMatches([]);
    }

    function onCustomerNameChange(value: string) {
        setForm((current) => ({ ...current, customerName: value }));
        if (selectedCustomer && selectedCustomer.full_name.toLowerCase() !== value.trim().toLowerCase()) {
            setSelectedCustomer(null);
        }
    }

    return (
        <section style={t.pageWrap}>
            <div style={{ ...t.formActionsRow, justifyContent: "space-between", alignItems: "baseline" }}>
                <div>
                    <h2 style={{ margin: 0 }}>Quick New Repair</h2>
                    <p style={{ ...t.pageIntro, marginTop: "6px" }}>Single-screen intake built for walk-ins. Tab through fields and press Ctrl+Enter to create.</p>
                </div>
                <div style={{ fontSize: "0.84rem", color: "#4b635d", fontWeight: 700 }}>Target: under 15 seconds</div>
            </div>

            <div style={quickPanelStyle}>
                <form
                    onSubmit={(event) => {
                        event.preventDefault();
                        void handleSubmit();
                    }}
                    onKeyDown={(event) => {
                        if (event.key === "Enter" && event.ctrlKey) {
                            event.preventDefault();
                            void handleSubmit();
                        }
                    }}
                    style={{ ...t.formStack, gap: "20px" }}
                >
                    <div style={quickFormLayoutStyle}>
                        <section style={formSectionStyle}>
                            <div style={sectionTitleStyle}>Customer</div>
                            <div style={twoColumnGridStyle}>
                                <label style={labelStyle}>
                                    <span>Customer name</span>
                                    <input
                                        value={form.customerName}
                                        onChange={(event) => onCustomerNameChange(event.target.value)}
                                        placeholder="Start typing customer name"
                                        style={inputStyle}
                                        autoFocus
                                    />
                                    {customerMatches.length > 0 ? (
                                        <div style={matchListStyle}>
                                            {customerMatches.map((customer) => (
                                                <button
                                                    key={customer.id}
                                                    type="button"
                                                    style={matchRowStyle}
                                                    onClick={() => applyCustomer(customer)}
                                                >
                                                    <strong>{customer.full_name}</strong>
                                                    <span>{customer.primary_phone || customer.alternate_phone || "No phone"}</span>
                                                </button>
                                            ))}
                                        </div>
                                    ) : null}
                                </label>

                                <label style={labelStyle}>
                                    <span>Phone number</span>
                                    <input
                                        value={form.phoneNumber}
                                        onChange={(event) => setForm((current) => ({ ...current, phoneNumber: event.target.value }))}
                                        placeholder="(555) 555-1234"
                                        style={inputStyle}
                                        inputMode="tel"
                                    />
                                </label>
                            </div>
                        </section>

                        <section style={formSectionStyle}>
                            <div style={sectionTitleStyle}>Device</div>
                            <div style={twoColumnGridStyle}>
                                <label style={labelStyle}>
                                    <span>Device brand</span>
                                    <input
                                        value={form.deviceBrand}
                                        onChange={(event) => setForm((current) => ({ ...current, deviceBrand: event.target.value }))}
                                        placeholder="Apple, Samsung, Google"
                                        style={inputStyle}
                                        list="brand-suggestions"
                                    />
                                    <datalist id="brand-suggestions">
                                        <option value="Apple" />
                                        <option value="Samsung" />
                                        <option value="Google" />
                                        <option value="Motorola" />
                                        <option value="OnePlus" />
                                    </datalist>
                                </label>

                                <label style={labelStyle}>
                                    <span>Device model</span>
                                    <input
                                        value={form.deviceModel}
                                        onChange={(event) => setForm((current) => ({ ...current, deviceModel: event.target.value }))}
                                        placeholder="iPhone 13, Galaxy S23"
                                        style={inputStyle}
                                        list="model-suggestions"
                                    />
                                    <datalist id="model-suggestions">
                                        {deviceSuggestions.map((device) => (
                                            <option key={device} value={device} />
                                        ))}
                                    </datalist>
                                </label>
                            </div>
                        </section>

                        <section style={formSectionStyle}>
                            <div style={sectionTitleStyle}>Repair Issue</div>
                            <label style={labelStyle}>
                                <span>Issue/problem</span>
                                <textarea
                                    value={form.issueProblem}
                                    onChange={(event) => setForm((current) => ({ ...current, issueProblem: event.target.value }))}
                                    placeholder="Example: Screen cracked, touch not responding on right side"
                                    style={{ ...inputStyle, minHeight: "84px", resize: "vertical" }}
                                />
                            </label>
                        </section>

                        <section style={{ ...formSectionStyle, ...secondarySectionStyle }}>
                            <div style={sectionTitleStyle}>Optional Notes</div>
                            <label style={labelStyle}>
                                <span>Optional notes</span>
                                <textarea
                                    value={form.optionalNotes}
                                    onChange={(event) => setForm((current) => ({ ...current, optionalNotes: event.target.value }))}
                                    placeholder="Any quick context from customer conversation"
                                    style={{ ...inputStyle, ...secondaryInputStyle, minHeight: "66px", resize: "vertical" }}
                                />
                            </label>
                        </section>

                        <section style={formSectionStyle}>
                            <div style={sectionTitleStyle}>Billing & Status</div>
                            <div style={twoColumnGridStyle}>
                                <label style={labelStyle}>
                                    <span>Estimated charge</span>
                                    <input
                                        value={form.estimatedCharge}
                                        onChange={(event) => setForm((current) => ({ ...current, estimatedCharge: event.target.value }))}
                                        placeholder="89.00"
                                        style={inputStyle}
                                        inputMode="decimal"
                                    />
                                </label>

                                <label style={labelStyle}>
                                    <span>Payment status</span>
                                    <select
                                        value={form.paymentStatus}
                                        onChange={(event) => setForm((current) => ({ ...current, paymentStatus: event.target.value as PaymentStatus }))}
                                        style={inputStyle}
                                    >
                                        <option value="unpaid">Unpaid</option>
                                        <option value="partial">Partially Paid</option>
                                        <option value="paid">Paid</option>
                                    </select>
                                </label>
                            </div>

                            <div style={{ ...labelStyle, marginTop: "4px" }}>
                                <span>Repair status</span>
                                <div style={statusRowStyle}>
                                    {QUICK_REPAIR_STATUSES.map((status) => {
                                        const colors = QUICK_REPAIR_STATUS_COLORS[status];
                                        const active = form.repairStatus === status;
                                        return (
                                            <button
                                                key={status}
                                                type="button"
                                                onClick={() => setForm((current) => ({ ...current, repairStatus: status }))}
                                                style={{
                                                    ...statusChipStyle,
                                                    background: active ? colors.text : colors.bg,
                                                    color: active ? "#ffffff" : colors.text,
                                                    borderColor: active ? colors.text : colors.border,
                                                }}
                                            >
                                                {status}
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                        </section>
                    </div>

                    {error ? <div style={t.errorBanner}>{error}</div> : null}

                    <div style={{ ...t.formActionsRow, justifyContent: "space-between" }}>
                        <div style={{ fontSize: "0.82rem", color: "#5b726c" }}>Keyboard: Tab through fields, Ctrl+Enter to submit.</div>
                        <button type="submit" disabled={submitting} style={primaryButtonStyle}>
                            {submitting ? "Creating repair..." : "Create Repair Ticket"}
                        </button>
                    </div>
                </form>
            </div>
        </section>
    );
}

const labelStyle = t.label;
const inputStyle = t.input;
const primaryButtonStyle = t.primaryBtn;

const quickPanelStyle = {
    ...t.panel,
    borderRadius: "20px",
    background: "linear-gradient(158deg, rgba(255,255,255,0.96) 0%, rgba(244,250,247,0.95) 48%, rgba(238,248,245,0.92) 100%)",
};

const quickFormLayoutStyle = {
    display: "grid",
    gap: "14px",
    minWidth: 0,
};

const formSectionStyle = {
    display: "grid",
    gap: "10px",
    minWidth: 0,
};

const sectionTitleStyle = {
    fontSize: "0.73rem",
    letterSpacing: "0.04em",
    textTransform: "uppercase" as const,
    color: "#56706a",
    fontWeight: 800,
};

const twoColumnGridStyle = {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "12px 16px",
    minWidth: 0,
};

const secondarySectionStyle = {
    opacity: 0.95,
};

const secondaryInputStyle = {
    fontSize: "0.95rem",
    background: "#fbfdfc",
};

const matchListStyle = {
    display: "grid",
    gap: "6px",
    marginTop: "6px",
    maxHeight: "210px",
    overflowY: "auto" as const,
};

const matchRowStyle = {
    border: "1px solid rgba(29, 43, 40, 0.14)",
    borderRadius: "12px",
    background: "#ffffff",
    color: "#163731",
    padding: "8px 10px",
    textAlign: "left" as const,
    display: "grid",
    gap: "4px",
    cursor: "pointer",
    minWidth: 0,
};

const statusRowStyle = {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "8px",
};

const statusChipStyle = {
    borderRadius: "999px",
    border: "1px solid transparent",
    padding: "7px 12px",
    fontWeight: 700,
    cursor: "pointer",
    fontSize: "0.82rem",
};
