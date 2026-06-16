import { apiFetch, getJson } from "./client";
export { fetchVoicemails, updateVoicemail, type VoicemailRecord } from "./system";

export type SupportedModel = {
    id: number;
    manufacturer: string | null;
    device_family: string;
    model_name: string;
    model_aliases: string | null;
    repair_policy: string;
    notes: string | null;
};

export type Customer = {
    id: number;
    full_name: string;
    primary_phone: string | null;
    alternate_phone: string | null;
    email: string | null;
    notes: string | null;
    created_at: string;
    updated_at: string;
};

export type PaymentStatus = "unpaid" | "partial" | "paid";

export type QuickRepairStatus =
    | "New Intake"
    | "Diagnosing"
    | "Waiting for Part"
    | "In Repair"
    | "Ready for Pickup"
    | "Completed"
    | "Canceled";

export type QuickRepairPayload = {
    customer_id?: number;
    customer_name: string;
    phone_number: string;
    device_brand: string;
    device_model: string;
    issue_problem: string;
    optional_notes?: string;
    estimated_charge?: number | null;
    payment_status: PaymentStatus;
    repair_status: QuickRepairStatus;
};

export type TicketSummary = {
    id: number;
    ticket_number: string;
    customer_id: number;
    customer_name: string;
    customer_phone: string | null;
    device_label: string;
    issue_category: string;
    status: string;
    payment_status: string;
    intake_date: string;
    estimated_price: number | null;
    final_price: number | null;
    updated_at: string;
    completed_at: string | null;
};

export type TicketSummaryList = {
    items: TicketSummary[];
    total: number;
    page: number;
    page_size: number;
};

export type TicketHistoryItem = {
    id: number;
    ticket_id: number;
    old_status: string | null;
    new_status: string;
    changed_by: string | null;
    note: string | null;
    created_at: string;
};

export type TicketNote = {
    id: number;
    ticket_id: number;
    note_type: string;
    body: string;
    created_by: string | null;
    created_at: string;
};

export type LoanerPhone = {
    id: number;
    loaner_code: string;
    manufacturer: string | null;
    model: string;
    carrier_compatibility: string | null;
    charger_type: string | null;
    sim_type: string | null;
    filter_status: string | null;
    condition_current: string | null;
    status: string;
    default_deposit: number;
    notes: string | null;
    active: boolean;
    created_at: string;
    updated_at: string;
};

export type LoanerCheckout = {
    id: number;
    loaner_phone_id: number;
    ticket_id: number;
    customer_id: number;
    date_out: string;
    expected_return_date: string | null;
    date_returned: string | null;
    condition_out: string | null;
    condition_returned: string | null;
    charger_included: boolean;
    charger_returned: boolean | null;
    sim_moved: boolean;
    outgoing_call_tested: boolean;
    incoming_call_tested: boolean;
    deposit_amount: number;
    deposit_refunded: number;
    deposit_deducted: number;
    deduction_reason: string | null;
    agreement_signed: boolean;
    checkout_staff: string | null;
    return_staff: string | null;
    status: string;
};

export type LoanerAgreement = {
    id: number;
    ticket_id: number;
    ticket_number: string;
    customer_id: number;
    customer_name: string;
    customer_phone: string | null;
    device_label: string;
    issue_category: string;
    loaner_phone_id: number;
    loaner_code: string;
    loaner_device_label: string;
    date_out: string;
    expected_return_date: string | null;
    condition_out: string | null;
    charger_included: boolean;
    sim_moved: boolean;
    outgoing_call_tested: boolean;
    incoming_call_tested: boolean;
    deposit_amount: number;
    agreement_signed: boolean;
    checkout_staff: string | null;
    status: string;
};

export type DashboardSummary = {
    open_tickets_count: number;
    checked_out_loaners_count: number;
    overdue_loaners_count: number;
};

export type LoanerAlertSummary = {
    checked_out_count: number;
    overdue_count: number;
    missing_charger_count: number;
    needs_reset_or_cleaning_count: number;
};

export type DashboardAlerts = {
    summary: LoanerAlertSummary;
    overdue_items: LoanerCheckout[];
};

export type PricingCalculation = {
    part_charge: number;
    labor_base: number;
    adjusted_labor: number;
    raw_price: number;
    customer_price: number;
    requires_soldering: boolean;
    warnings: string[];
};

export type RepairAction = {
    id: number;
    ticket_id: number;
    repair_category_id: number;
    repair_category_name: string | null;
    action_description: string | null;
    part_cost: number;
    labor_minutes: number;
    difficulty_level: number;
    risk_level: number;
    calculated_price: number | null;
    final_price: number | null;
    status: string;
    performed_by: string | null;
    performed_at: string | null;
    requires_soldering: boolean;
};

export type PricingRules = {
    defaults: {
        base_labor_rate_per_hour: number;
        minimum_labor_charge: number;
        part_markup_percent: number;
        diagnostic_fee: number;
    };
    difficulty_multipliers: Record<string, number>;
    risk_multipliers: Record<string, number>;
    repair_categories: Array<{
        id: number;
        name: string;
        description: string | null;
        default_policy: string | null;
        requires_soldering: number;
    }>;
};

export type RepairCategory = {
    id: number;
    name: string;
    description: string | null;
    default_policy: string | null;
    requires_soldering: boolean;
    active: boolean;
};

export type StatusWorkflowGuardrails = {
    enforce_no_active_loaner_for_ready_for_pickup: boolean;
    enforce_no_active_loaner_for_closed_statuses: boolean;
    enforce_final_price_for_ready_for_pickup: boolean;
    enforce_final_price_for_closed_paid_statuses: boolean;
};

export type StatusWorkflowRules = {
    transitions: Record<string, string[]>;
    guardrails: StatusWorkflowGuardrails;
    updated_at: string;
};

export type TicketDetail = {
    id: number;
    ticket_number: string;
    customer_id: number;
    customer_name: string;
    customer_phone: string | null;
    customer_alternate_phone: string | null;
    device_model_id: number | null;
    device_model_text_override: string | null;
    device_label: string;
    carrier: string | null;
    sim_type: string | null;
    imei_serial: string | null;
    device_color: string | null;
    filter_status: string | null;
    issue_category: string;
    issue_description: string | null;
    condition_summary: string | null;
    water_damage_status: string;
    dropped_status: string;
    powers_on_status: string;
    charges_status: string;
    customer_approval_limit: number | null;
    must_call_before_repair: boolean;
    customer_prefers_replacement_if_high: boolean;
    estimated_price: number | null;
    final_price: number | null;
    payment_status: string;
    diagnostic_fee: number | null;
    status: string;
    priority: string;
    intake_staff: string | null;
    assigned_technician: string | null;
    intake_date: string;
    created_at: string;
    updated_at: string;
    history: TicketHistoryItem[];
    notes: TicketNote[];
    repair_actions: RepairAction[];
};

export type IntakeFormPayload = {
    customer: {
        full_name: string;
        primary_phone: string;
        alternate_phone: string;
        email: string;
        notes: string;
    };
    ticket: {
        device_model_id: number | null;
        device_model_text_override: string;
        carrier: string;
        sim_type: string;
        imei_serial: string;
        device_color: string;
        filter_status: string;
        issue_category: string;
        issue_description: string;
        condition_summary: string;
        water_damage_status: string;
        dropped_status: string;
        powers_on_status: string;
        charges_status: string;
        customer_approval_limit: string;
        must_call_before_repair: boolean;
        customer_prefers_replacement_if_high: boolean;
        diagnostic_fee: string;
        intake_staff: string;
        intake_note: string;
    };
};

async function postJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
    const response = await apiFetch(path, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }

    return (await response.json()) as TResponse;
}

export async function fetchSupportedModels(): Promise<SupportedModel[]> {
    return getJson<SupportedModel[]>("/api/supported-models");
}

export async function fetchCustomers(search?: string): Promise<Customer[]> {
    const params = new URLSearchParams();
    if (search) {
        params.set("search", search);
    }
    const query = params.toString();
    return getJson<Customer[]>(`/api/customers${query ? `?${query}` : ""}`);
}

export async function fetchCustomer(customerId: number): Promise<Customer> {
    return getJson<Customer>(`/api/customers/${customerId}`);
}

export async function fetchCustomerTickets(customerId: number): Promise<TicketSummary[]> {
    return getJson<TicketSummary[]>(`/api/customers/${customerId}/tickets`);
}

export async function fetchTickets(search?: string): Promise<TicketSummary[]> {
    const params = new URLSearchParams();
    if (search) {
        params.set("search", search);
    }
    const query = params.toString();
    return getJson<TicketSummary[]>(`/api/tickets${query ? `?${query}` : ""}`);
}

export async function fetchTicketsPaged(args: {
    page: number;
    pageSize: number;
    search?: string;
    status?: string;
}): Promise<TicketSummaryList> {
    const params = new URLSearchParams();
    params.set("page", String(args.page));
    params.set("page_size", String(args.pageSize));
    if (args.search) {
        params.set("search", args.search);
    }
    if (args.status) {
        params.set("status", args.status);
    }
    return getJson<TicketSummaryList>(`/api/tickets/paged?${params.toString()}`);
}

export async function fetchTicket(ticketId: string): Promise<TicketDetail> {
    return getJson<TicketDetail>(`/api/tickets/${ticketId}`);
}

export async function fetchLoanerAgreement(ticketId: string): Promise<LoanerAgreement> {
    return getJson<LoanerAgreement>(`/api/tickets/${ticketId}/loaner-agreement`);
}

export async function createIntake(payload: IntakeFormPayload): Promise<TicketDetail> {
    const customer = await postJson<Customer>("/api/customers", {
        full_name: payload.customer.full_name,
        primary_phone: payload.customer.primary_phone || null,
        alternate_phone: payload.customer.alternate_phone || null,
        email: payload.customer.email || null,
        notes: payload.customer.notes || null,
    });

    return postJson<TicketDetail>("/api/tickets", {
        customer_id: customer.id,
        device_model_id: payload.ticket.device_model_id,
        device_model_text_override: payload.ticket.device_model_text_override || null,
        carrier: payload.ticket.carrier || null,
        sim_type: payload.ticket.sim_type || null,
        imei_serial: payload.ticket.imei_serial || null,
        device_color: payload.ticket.device_color || null,
        filter_status: payload.ticket.filter_status || null,
        issue_category: payload.ticket.issue_category,
        issue_description: payload.ticket.issue_description || null,
        condition_summary: payload.ticket.condition_summary || null,
        water_damage_status: payload.ticket.water_damage_status,
        dropped_status: payload.ticket.dropped_status,
        powers_on_status: payload.ticket.powers_on_status,
        charges_status: payload.ticket.charges_status,
        customer_approval_limit: payload.ticket.customer_approval_limit ? Number(payload.ticket.customer_approval_limit) : null,
        must_call_before_repair: payload.ticket.must_call_before_repair,
        customer_prefers_replacement_if_high: payload.ticket.customer_prefers_replacement_if_high,
        diagnostic_fee: payload.ticket.diagnostic_fee ? Number(payload.ticket.diagnostic_fee) : 0,
        intake_staff: payload.ticket.intake_staff || null,
        intake_note: payload.ticket.intake_note || null,
    });
}

function mapQuickToBackendStatus(status: QuickRepairStatus): string {
    switch (status) {
        case "New Intake":
            return "New Intake";
        case "Diagnosing":
            return "Needs Diagnosis";
        case "Waiting for Part":
            return "Waiting for Parts";
        case "In Repair":
            return "In Repair";
        case "Ready for Pickup":
            return "Ready for Pickup";
        case "Completed":
            return "Picked Up / Closed";
        case "Canceled":
            return "Not Repairable";
        default:
            return "New Intake";
    }
}

export async function createQuickRepair(payload: QuickRepairPayload): Promise<TicketDetail> {
    const normalizedName = payload.customer_name.trim();
    const normalizedPhone = payload.phone_number.trim();

    let customerId = payload.customer_id;
    if (!customerId) {
        const customer = await postJson<Customer>("/api/customers", {
            full_name: normalizedName,
            primary_phone: normalizedPhone || null,
            alternate_phone: null,
            email: null,
            notes: null,
        });
        customerId = customer.id;
    }

    const issueSummary = payload.issue_problem.trim();
    const issueCategory = issueSummary.split(/[.!?]/)[0]?.trim().slice(0, 80) || "General Repair";
    const intakeLines = [
        payload.optional_notes?.trim() || "",
        `Payment status: ${payload.payment_status}`,
    ].filter(Boolean);

    return postJson<TicketDetail>("/api/tickets", {
        customer_id: customerId,
        device_model_id: null,
        device_model_text_override: `${payload.device_brand.trim()} ${payload.device_model.trim()}`.trim(),
        issue_category: issueCategory,
        issue_description: issueSummary,
        estimated_price: payload.estimated_charge ?? null,
        payment_status: payload.payment_status,
        status: mapQuickToBackendStatus(payload.repair_status),
        intake_note: intakeLines.join("\n"),
        water_damage_status: "unknown",
        dropped_status: "unknown",
        powers_on_status: "unknown",
        charges_status: "unknown",
    });
}

export async function addTicketNote(ticketId: number, noteType: string, body: string, createdBy: string): Promise<TicketNote> {
    return postJson<TicketNote>(`/api/tickets/${ticketId}/notes`, {
        note_type: noteType,
        body,
        created_by: createdBy || null,
    });
}

export async function updateTicketStatus(ticketId: number, newStatus: string, changedBy: string, note: string, finalPrice?: number): Promise<TicketHistoryItem> {
    return postJson<TicketHistoryItem>(`/api/tickets/${ticketId}/status`, {
        new_status: newStatus,
        changed_by: changedBy || null,
        note: note || null,
        ...(finalPrice !== undefined ? { final_price: finalPrice } : {}),
    });
}

async function patchJson<TResponse>(path: string, body: unknown): Promise<TResponse> {
    const response = await apiFetch(path, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }

    return (await response.json()) as TResponse;
}

export async function closeTicket(ticketId: number, finalPrice: number | null, changedBy: string, note: string) {
    return postJson<{ ticket_id: number; status: string; closed: boolean }>(`/api/tickets/${ticketId}/close`, {
        final_price: finalPrice,
        changed_by: changedBy || null,
        note: note || null,
    });
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
    return getJson<DashboardSummary>("/api/dashboard/summary");
}

export async function fetchDashboardAlerts(): Promise<DashboardAlerts> {
    return getJson<DashboardAlerts>("/api/dashboard/alerts");
}

export async function fetchLoaners(status?: string): Promise<LoanerPhone[]> {
    const params = new URLSearchParams();
    if (status) {
        params.set("status", status);
    }
    const query = params.toString();
    return getJson<LoanerPhone[]>(`/api/loaners${query ? `?${query}` : ""}`);
}

export async function createLoaner(payload: {
    loaner_code: string;
    manufacturer: string;
    model: string;
    carrier_compatibility: string;
    charger_type: string;
    sim_type: string;
    filter_status: string;
    condition_current: string;
    default_deposit: string;
    notes: string;
}): Promise<LoanerPhone> {
    return postJson<LoanerPhone>("/api/loaners", {
        loaner_code: payload.loaner_code,
        manufacturer: payload.manufacturer || null,
        model: payload.model,
        carrier_compatibility: payload.carrier_compatibility || null,
        charger_type: payload.charger_type || null,
        sim_type: payload.sim_type || null,
        filter_status: payload.filter_status || null,
        condition_current: payload.condition_current || null,
        default_deposit: payload.default_deposit ? Number(payload.default_deposit) : 0,
        notes: payload.notes || null,
    });
}

export async function checkoutLoaner(
    loanerId: number,
    payload: {
        ticket_id: string;
        customer_id: string;
        expected_return_date: string;
        condition_out: string;
        charger_included: boolean;
        sim_moved: boolean;
        outgoing_call_tested: boolean;
        incoming_call_tested: boolean;
        deposit_amount: string;
        checkout_staff: string;
        agreement_signed: boolean;
    }
): Promise<LoanerCheckout> {
    return postJson<LoanerCheckout>(`/api/loaners/${loanerId}/checkout`, {
        ticket_id: Number(payload.ticket_id),
        customer_id: Number(payload.customer_id),
        expected_return_date: payload.expected_return_date || null,
        condition_out: payload.condition_out || null,
        charger_included: payload.charger_included,
        sim_moved: payload.sim_moved,
        outgoing_call_tested: payload.outgoing_call_tested,
        incoming_call_tested: payload.incoming_call_tested,
        deposit_amount: payload.deposit_amount ? Number(payload.deposit_amount) : 0,
        checkout_staff: payload.checkout_staff || null,
        agreement_signed: payload.agreement_signed,
    });
}

export async function returnLoaner(
    loanerId: number,
    payload: {
        condition_returned: string;
        charger_returned: boolean | null;
        deposit_refunded: string;
        deposit_deducted: string;
        deduction_reason: string;
        return_staff: string;
        next_status: string;
    }
): Promise<LoanerCheckout> {
    return postJson<LoanerCheckout>(`/api/loaners/${loanerId}/return`, {
        condition_returned: payload.condition_returned || null,
        charger_returned: payload.charger_returned,
        deposit_refunded: payload.deposit_refunded ? Number(payload.deposit_refunded) : 0,
        deposit_deducted: payload.deposit_deducted ? Number(payload.deposit_deducted) : 0,
        deduction_reason: payload.deduction_reason || null,
        return_staff: payload.return_staff || null,
        next_status: payload.next_status,
    });
}

export async function updateLoanerStatus(loanerId: number, status: string): Promise<LoanerPhone> {
    return patchJson<LoanerPhone>(`/api/loaners/${loanerId}`, { status });
}

export async function fetchPricingRules(): Promise<PricingRules> {
    return getJson<PricingRules>("/api/pricing/rules");
}

export async function updatePricingRules(payload: {
    base_labor_rate_per_hour?: number;
    minimum_labor_charge?: number;
    part_markup_percent?: number;
    diagnostic_fee?: number;
}): Promise<{ defaults: PricingRules["defaults"] }> {
    return patchJson<{ defaults: PricingRules["defaults"] }>("/api/pricing/rules", payload);
}

export async function fetchRepairCategories(includeInactive = false): Promise<RepairCategory[]> {
    const query = includeInactive ? "?include_inactive=true" : "";
    return getJson<RepairCategory[]>(`/api/repair-categories${query}`);
}

export async function createRepairCategory(payload: {
    name: string;
    description?: string | null;
    default_policy?: string | null;
    requires_soldering?: boolean;
}): Promise<RepairCategory> {
    return postJson<RepairCategory>("/api/repair-categories", payload);
}

export async function updateRepairCategory(
    repairCategoryId: number,
    payload: {
        name?: string;
        description?: string | null;
        default_policy?: string | null;
        requires_soldering?: boolean;
        active?: boolean;
    }
): Promise<RepairCategory> {
    return patchJson<RepairCategory>(`/api/repair-categories/${repairCategoryId}`, payload);
}

export async function fetchStatusWorkflowRules(): Promise<StatusWorkflowRules> {
    return getJson<StatusWorkflowRules>("/api/status-workflow");
}

export async function updateStatusWorkflowRules(payload: {
    transitions?: Record<string, string[]>;
    guardrails?: Partial<StatusWorkflowGuardrails>;
}): Promise<StatusWorkflowRules> {
    return patchJson<StatusWorkflowRules>("/api/status-workflow", payload);
}

export async function calculatePricing(payload: {
    ticket_id: number;
    repair_category_id: number;
    part_cost: number;
    labor_minutes: number;
    difficulty_level: number;
    risk_level: number;
    diagnostic_fee: number;
    rush_fee: number;
    discount: number;
    estimated_replacement_value?: number | null;
}): Promise<PricingCalculation> {
    return postJson<PricingCalculation>("/api/pricing/calculate", payload);
}

export async function addRepairAction(ticketId: number, payload: {
    repair_category_id: number;
    action_description: string;
    part_cost: number;
    labor_minutes: number;
    difficulty_level: number;
    risk_level: number;
    diagnostic_fee: number;
    rush_fee: number;
    discount: number;
    estimated_replacement_value?: number | null;
    status?: string;
    performed_by?: string;
}): Promise<RepairAction> {
    return postJson<RepairAction>(`/api/tickets/${ticketId}/repair-actions`, payload);
}


// ============================================================================
// Phase 4: Technician Queue and Hours Logging
// ============================================================================


export type QueueTicket = {
    id: number;
    ticket_number: string;
    customer_id: number;
    customer_name: string | null;
    customer_phone: string | null;
    manufacturer: string | null;
    model_name: string | null;
    issue_category: string;
    status: string;
    customer_approval_limit: number | null;
    assigned_technician: string | null;
    intake_date: string;
    created_at: string;
};

export type TechnicianQueue = {
    "Loaner Outstanding": QueueTicket[];
    "Waiting for Parts": QueueTicket[];
    "Customer Approval Needed": QueueTicket[];
    "New Intake": QueueTicket[];
    "Needs Diagnosis": QueueTicket[];
};

export type QueueAssignmentResult = {
    ticket_id: number;
    assigned_technician: string | null;
    updated: boolean;
};

export type ReportSummary = {
    date_range: {
        start: string;
        end: string;
    };
    technician_filter: string | null;
    repair_category_filter: string | null;
    created_tickets_count: number;
    closed_tickets_count: number;
    total_revenue: number;
    average_closed_ticket_revenue: number;
    total_hours: number;
    revenue_per_hour: number;
    available_technicians: string[];
    available_repair_categories: string[];
    technician_breakdown: Array<{
        technician: string;
        total_hours: number;
        tickets_worked: number;
        closed_tickets_count: number;
        total_revenue: number;
    }>;
    repair_category_breakdown: Array<{
        repair_category: string;
        action_count: number;
        ticket_count: number;
        total_final_price: number;
    }>;
};


export async function fetchTechnicianQueue(): Promise<TechnicianQueue> {
    return getJson<TechnicianQueue>("/api/queue");
}

export async function assignQueueTicket(ticketId: number, assignedTechnician: string | null): Promise<QueueAssignmentResult> {
    return postJson<QueueAssignmentResult>("/api/queue/assign", {
        ticket_id: ticketId,
        assigned_technician: assignedTechnician,
    });
}

export async function fetchReportSummary(filters?: {
    startDate?: string;
    endDate?: string;
    technician?: string;
    repairCategory?: string;
}): Promise<ReportSummary> {
    const params = new URLSearchParams();
    if (filters?.startDate) params.set("start_date", filters.startDate);
    if (filters?.endDate) params.set("end_date", filters.endDate);
    if (filters?.technician) params.set("technician", filters.technician);
    if (filters?.repairCategory) params.set("repair_category", filters.repairCategory);
    const query = params.toString();
    return getJson<ReportSummary>(`/api/reports/summary${query ? `?${query}` : ""}`);
}