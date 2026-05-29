from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class HealthResponse(BaseModel):
    status: str
    app: str
    database_ready: bool
    supported_model_count: int
    repair_category_count: int


class SupportedModelResponse(BaseModel):
    id: int
    manufacturer: str | None
    device_family: str
    model_name: str
    model_aliases: str | None
    repair_policy: str
    notes: str | None


class RepairCategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    default_policy: str | None
    requires_soldering: bool
    active: bool


class RepairCategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    default_policy: str | None = None
    requires_soldering: bool = False


class RepairCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    default_policy: str | None = None
    requires_soldering: bool | None = None
    active: bool | None = None


class StatusWorkflowGuardrails(BaseModel):
    enforce_no_active_loaner_for_ready_for_pickup: bool = True
    enforce_no_active_loaner_for_closed_statuses: bool = True
    enforce_final_price_for_ready_for_pickup: bool = True
    enforce_final_price_for_closed_paid_statuses: bool = True


class StatusWorkflowRulesResponse(BaseModel):
    transitions: dict[str, list[str]]
    guardrails: StatusWorkflowGuardrails
    updated_at: str


class StatusWorkflowRulesUpdate(BaseModel):
    transitions: dict[str, list[str]] | None = None
    guardrails: StatusWorkflowGuardrails | None = None


class CustomerCreate(BaseModel):
    full_name: str = Field(min_length=1)
    primary_phone: str | None = None
    alternate_phone: str | None = None
    email: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_contact(self) -> "CustomerCreate":
        if not (self.primary_phone or self.alternate_phone):
            raise ValueError("Primary phone or alternate phone is required.")
        return self


class CustomerUpdate(BaseModel):
    full_name: str | None = None
    primary_phone: str | None = None
    alternate_phone: str | None = None
    email: str | None = None
    notes: str | None = None


class CustomerResponse(BaseModel):
    id: int
    full_name: str
    primary_phone: str | None
    alternate_phone: str | None
    email: str | None
    notes: str | None
    created_at: str
    updated_at: str


class TicketCreate(BaseModel):
    customer_id: int
    device_model_id: int | None = None
    device_model_text_override: str | None = None
    carrier: str | None = None
    sim_type: str | None = None
    imei_serial: str | None = None
    device_color: str | None = None
    filter_status: str | None = None
    issue_category: str = Field(min_length=1)
    issue_description: str | None = None
    condition_summary: str | None = None
    water_damage_status: str = "unknown"
    dropped_status: str = "unknown"
    powers_on_status: str = "unknown"
    charges_status: str = "unknown"
    customer_approval_limit: float | None = None
    must_call_before_repair: bool = False
    customer_prefers_replacement_if_high: bool = False
    estimated_price: float | None = None
    final_price: float | None = None
    payment_status: Literal["unpaid", "partial", "paid"] = "unpaid"
    diagnostic_fee: float = 0
    status: str = "New Intake"
    priority: Literal["low", "normal", "high"] = "normal"
    intake_staff: str | None = None
    assigned_technician: str | None = None
    intake_note: str | None = None


class TicketUpdate(BaseModel):
    device_model_id: int | None = None
    device_model_text_override: str | None = None
    carrier: str | None = None
    sim_type: str | None = None
    imei_serial: str | None = None
    device_color: str | None = None
    filter_status: str | None = None
    issue_category: str | None = None
    issue_description: str | None = None
    condition_summary: str | None = None
    water_damage_status: str | None = None
    dropped_status: str | None = None
    powers_on_status: str | None = None
    charges_status: str | None = None
    customer_approval_limit: float | None = None
    must_call_before_repair: bool | None = None
    customer_prefers_replacement_if_high: bool | None = None
    estimated_price: float | None = None
    final_price: float | None = None
    payment_status: Literal["unpaid", "partial", "paid"] | None = None
    diagnostic_fee: float | None = None
    status: str | None = None
    priority: Literal["low", "normal", "high"] | None = None
    intake_staff: str | None = None
    assigned_technician: str | None = None


class TicketStatusChange(BaseModel):
    new_status: str = Field(min_length=1)
    changed_by: str | None = None
    note: str | None = None
    final_price: float | None = None


class TicketNoteCreate(BaseModel):
    note_type: Literal[
        "front_desk",
        "technician",
        "customer_call",
        "pricing",
        "parts",
        "warranty",
        "internal",
    ]
    body: str = Field(min_length=1)
    created_by: str | None = None


class TicketSummaryResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    customer_name: str
    customer_phone: str | None
    device_label: str
    issue_category: str
    status: str
    payment_status: str
    intake_date: str
    estimated_price: float | None
    final_price: float | None
    updated_at: str


class TicketStatusHistoryResponse(BaseModel):
    id: int
    ticket_id: int
    old_status: str | None
    new_status: str
    changed_by: str | None
    note: str | None
    created_at: str


class TicketNoteResponse(BaseModel):
    id: int
    ticket_id: int
    note_type: str
    body: str
    created_by: str | None
    created_at: str


class TicketDetailResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    customer_name: str
    customer_phone: str | None
    customer_alternate_phone: str | None
    device_model_id: int | None
    device_model_text_override: str | None
    device_label: str
    carrier: str | None
    sim_type: str | None
    imei_serial: str | None
    device_color: str | None
    filter_status: str | None
    issue_category: str
    issue_description: str | None
    condition_summary: str | None
    water_damage_status: str
    dropped_status: str
    powers_on_status: str
    charges_status: str
    customer_approval_limit: float | None
    must_call_before_repair: bool
    customer_prefers_replacement_if_high: bool
    estimated_price: float | None
    final_price: float | None
    payment_status: str
    diagnostic_fee: float | None
    status: str
    priority: str
    intake_staff: str | None
    assigned_technician: str | None
    intake_date: str
    created_at: str
    updated_at: str
    history: list[TicketStatusHistoryResponse]
    notes: list[TicketNoteResponse]
    repair_actions: list[dict]


class TicketCloseRequest(BaseModel):
    final_price: float | None = None
    changed_by: str | None = None
    note: str | None = None


class TicketCloseResponse(BaseModel):
    ticket_id: int
    status: str
    closed: bool


class LoanerPhoneCreate(BaseModel):
    loaner_code: str = Field(min_length=1)
    manufacturer: str | None = None
    model: str = Field(min_length=1)
    carrier_compatibility: str | None = None
    charger_type: str | None = None
    sim_type: str | None = None
    filter_status: str | None = None
    condition_current: str | None = None
    default_deposit: float = 0
    notes: str | None = None


class LoanerPhoneUpdate(BaseModel):
    manufacturer: str | None = None
    model: str | None = None
    carrier_compatibility: str | None = None
    charger_type: str | None = None
    sim_type: str | None = None
    filter_status: str | None = None
    condition_current: str | None = None
    status: str | None = None
    default_deposit: float | None = None
    notes: str | None = None
    active: bool | None = None


class LoanerPhoneResponse(BaseModel):
    id: int
    loaner_code: str
    manufacturer: str | None
    model: str
    carrier_compatibility: str | None
    charger_type: str | None
    sim_type: str | None
    filter_status: str | None
    condition_current: str | None
    status: str
    default_deposit: float
    notes: str | None
    active: bool
    created_at: str
    updated_at: str


class LoanerCheckoutCreate(BaseModel):
    ticket_id: int
    customer_id: int
    expected_return_date: str | None = None
    condition_out: str | None = None
    charger_included: bool = False
    sim_moved: bool = False
    outgoing_call_tested: bool = False
    incoming_call_tested: bool = False
    deposit_amount: float = 0
    checkout_staff: str | None = None
    agreement_signed: bool = False


class LoanerReturnRequest(BaseModel):
    condition_returned: str | None = None
    charger_returned: bool | None = None
    deposit_refunded: float = 0
    deposit_deducted: float = 0
    deduction_reason: str | None = None
    return_staff: str | None = None
    next_status: Literal[
        "Available",
        "Returned Needs Reset",
        "Returned Needs Cleaning",
        "Damaged",
        "Lost",
        "Retired",
    ] = "Returned Needs Reset"


class LoanerCheckoutResponse(BaseModel):
    id: int
    loaner_phone_id: int
    ticket_id: int
    customer_id: int
    date_out: str
    expected_return_date: str | None
    date_returned: str | None
    condition_out: str | None
    condition_returned: str | None
    charger_included: bool
    charger_returned: bool | None
    sim_moved: bool
    outgoing_call_tested: bool
    incoming_call_tested: bool
    deposit_amount: float
    deposit_refunded: float
    deposit_deducted: float
    deduction_reason: str | None
    agreement_signed: bool
    checkout_staff: str | None
    return_staff: str | None
    status: str


class LoanerAgreementResponse(BaseModel):
    id: int
    ticket_id: int
    ticket_number: str
    customer_id: int
    customer_name: str
    customer_phone: str | None
    device_label: str
    issue_category: str
    loaner_phone_id: int
    loaner_code: str
    loaner_device_label: str
    date_out: str
    expected_return_date: str | None
    condition_out: str | None
    charger_included: bool
    sim_moved: bool
    outgoing_call_tested: bool
    incoming_call_tested: bool
    deposit_amount: float
    agreement_signed: bool
    checkout_staff: str | None
    status: str


class LoanerAlertSummary(BaseModel):
    checked_out_count: int
    overdue_count: int
    missing_charger_count: int
    needs_reset_or_cleaning_count: int


class DashboardSummaryResponse(BaseModel):
    open_tickets_count: int
    checked_out_loaners_count: int
    overdue_loaners_count: int


class DashboardAlertsResponse(BaseModel):
    summary: LoanerAlertSummary
    overdue_items: list[LoanerCheckoutResponse]


class PricingCalculateRequest(BaseModel):
    ticket_id: int | None = None
    repair_category_id: int | None = None
    part_cost: float = 0
    labor_minutes: int = 0
    difficulty_level: Literal[1, 2, 3, 4, 5] = 1
    risk_level: Literal[1, 2, 3, 4, 5] = 1
    base_labor_rate_per_hour: float | None = None
    part_markup_percent: float | None = None
    minimum_labor_charge: float | None = None
    diagnostic_fee: float | None = None
    rush_fee: float = 0
    discount: float = 0
    estimated_replacement_value: float | None = None


class PricingCalculationResponse(BaseModel):
    part_charge: float
    labor_base: float
    adjusted_labor: float
    raw_price: float
    customer_price: float
    requires_soldering: bool
    warnings: list[str]


class PricingDefaultsUpdate(BaseModel):
    base_labor_rate_per_hour: float | None = Field(default=None, ge=0)
    minimum_labor_charge: float | None = Field(default=None, ge=0)
    part_markup_percent: float | None = Field(default=None, ge=0)
    diagnostic_fee: float | None = Field(default=None, ge=0)


class RepairActionCreate(BaseModel):
    repair_category_id: int
    action_description: str | None = None
    part_cost: float = 0
    labor_minutes: int = 0
    difficulty_level: Literal[1, 2, 3, 4, 5] = 1
    risk_level: Literal[1, 2, 3, 4, 5] = 1
    diagnostic_fee: float = 0
    rush_fee: float = 0
    discount: float = 0
    estimated_replacement_value: float | None = None
    status: str = "planned"
    performed_by: str | None = None


class RepairActionResponse(BaseModel):
    id: int
    ticket_id: int
    repair_category_id: int
    repair_category_name: str | None
    action_description: str | None
    part_cost: float
    labor_minutes: int
    difficulty_level: int
    risk_level: int
    calculated_price: float | None
    final_price: float | None
    status: str
    performed_by: str | None
    performed_at: str | None
    requires_soldering: bool


class InventoryPurchaseItemCreate(BaseModel):
    item_type: str = Field(default="device", min_length=1)
    manufacturer: str | None = None
    item_name: str = Field(min_length=1)
    quantity: int = Field(ge=1)
    estimated_unit_cost: float | None = None
    line_total: float | None = None
    notes: str | None = None


class InventoryPurchaseItemResponse(BaseModel):
    id: int
    purchase_id: int
    item_type: str
    manufacturer: str | None
    item_name: str
    quantity: int
    estimated_unit_cost: float | None
    line_total: float | None
    notes: str | None
    created_at: str
    updated_at: str


class InventoryPurchaseCreate(BaseModel):
    purchase_date: str = Field(min_length=10)
    vendor: str | None = None
    reference_number: str | None = None
    total_cost: float = Field(ge=0)
    notes: str | None = None
    items: list[InventoryPurchaseItemCreate] = Field(default_factory=list)


class InventoryPurchaseResponse(BaseModel):
    id: int
    purchase_date: str
    vendor: str | None
    reference_number: str | None
    total_cost: float
    notes: str | None
    items: list[InventoryPurchaseItemResponse]
    created_at: str
    updated_at: str


class InventoryPurchaseListResponse(BaseModel):
    items: list[InventoryPurchaseResponse]


# ============================================================================
# Phase 4: Technician Queue and Hours Logging
# ============================================================================


class QueueTicketResponse(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    customer_name: str | None
    customer_phone: str | None
    manufacturer: str | None
    model_name: str | None
    issue_category: str
    status: str
    customer_approval_limit: float | None
    assigned_technician: str | None
    intake_date: str
    created_at: str


class TechnicianQueueResponse(BaseModel):
    """Queue grouped by status for technician workflow."""
    loaner_outstanding: list[QueueTicketResponse] = Field(alias="Loaner Outstanding")
    waiting_for_parts: list[QueueTicketResponse] = Field(alias="Waiting for Parts")
    approval_needed: list[QueueTicketResponse] = Field(alias="Customer Approval Needed")
    new_intake: list[QueueTicketResponse] = Field(alias="New Intake")
    needs_diagnosis: list[QueueTicketResponse] = Field(alias="Needs Diagnosis")

    model_config = ConfigDict(populate_by_name=True)


class QueueAssignmentRequest(BaseModel):
    ticket_id: int
    assigned_technician: str | None = None


class QueueAssignmentResponse(BaseModel):
    ticket_id: int
    assigned_technician: str | None
    updated: bool


class HoursLogCreate(BaseModel):
    technician: str = Field(min_length=1)
    work_date: str = Field(min_length=10)  # YYYY-MM-DD
    hours_worked: float = Field(ge=0)
    work_description: str | None = None
    ticket_id: int | None = None


class HoursClockInRequest(BaseModel):
    technician: str = Field(min_length=1)
    ticket_id: int | None = None
    work_description: str | None = None


class HoursClockOutRequest(BaseModel):
    technician: str = Field(min_length=1)
    ticket_id: int | None = None
    work_description: str | None = None


class HoursLogResponse(BaseModel):
    id: int
    ticket_id: int | None
    technician: str
    work_date: str
    hours_worked: float
    work_description: str | None
    created_at: str
    updated_at: str


class HoursClockSessionResponse(BaseModel):
    id: int
    ticket_id: int | None
    technician: str
    work_description: str | None
    clocked_in_at: str
    clocked_out_at: str | None
    status: str
    elapsed_seconds: int
    elapsed_hours: float
    created_at: str
    updated_at: str


class HoursClockOutResponse(BaseModel):
    session: HoursClockSessionResponse
    hours_entry: HoursLogResponse


class HoursSummaryResponse(BaseModel):
    by_technician: dict[str, float]
    total_hours: float
    date_range: dict[str, str]


class ReportTechnicianBreakdownResponse(BaseModel):
    technician: str
    total_hours: float
    tickets_worked: int
    closed_tickets_count: int
    total_revenue: float


class ReportRepairCategoryBreakdownResponse(BaseModel):
    repair_category: str
    action_count: int
    ticket_count: int
    total_final_price: float


class ReportSummaryResponse(BaseModel):
    date_range: dict[str, str]
    technician_filter: str | None = None
    repair_category_filter: str | None = None
    created_tickets_count: int
    closed_tickets_count: int
    total_revenue: float
    average_closed_ticket_revenue: float
    total_hours: float
    revenue_per_hour: float
    available_technicians: list[str] = Field(default_factory=list)
    available_repair_categories: list[str] = Field(default_factory=list)
    technician_breakdown: list[ReportTechnicianBreakdownResponse] = Field(default_factory=list)
    repair_category_breakdown: list[ReportRepairCategoryBreakdownResponse] = Field(default_factory=list)


class BackupResponse(BaseModel):
    file_name: str
    backup_path: str
    created_at: str
    file_size_bytes: int


class SystemActivityResponse(BaseModel):
    activity_type: str
    file_name: str
    created_at: str
    file_size_bytes: int
    file_path: str | None = None


class LoanerAgreementDefaultsResponse(BaseModel):
    responsibility_text: str
    return_policy_text: str
    signature_note_text: str
    updated_at: str


class LoanerAgreementDefaultsUpdate(BaseModel):
    responsibility_text: str | None = None
    return_policy_text: str | None = None
    signature_note_text: str | None = None


class NotificationTemplate(BaseModel):
    id: int
    template_key: str
    template_name: str
    description: str
    template_text: str
    placeholders: list[str]
    updated_at: str


class NotificationTemplatesUpdate(BaseModel):
    """Update notification template text for one or more templates."""
    pass  # Will accept arbitrary dict keys in the route


class TwilioSettingsResponse(BaseModel):
    account_sid: str | None = None
    phone_number: str | None = None
    public_webhook_base_url: str | None = None
    voicemail_greeting: str | None = None
    voicemail_greeting_audio_url: str | None = None
    twilio_auth_token_set: bool = False
    configured: bool = False
    created_at: str | None = None
    updated_at: str | None = None


class TwilioSettingsUpdate(BaseModel):
    account_sid: str | None = None
    auth_token: str | None = None
    clear_auth_token: bool = False
    phone_number: str | None = None
    public_webhook_base_url: str | None = None
    voicemail_greeting: str | None = None
    voicemail_greeting_audio_url: str | None = None


class VoicemailRecordResponse(BaseModel):
    id: int
    caller_number: str | None = None
    called_number: str | None = None
    call_sid: str | None = None
    recording_sid: str | None = None
    recording_url: str | None = None
    recording_duration_seconds: int | None = None
    transcription_text: str | None = None
    notes: str | None = None
    status: str
    customer_id: int | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    ticket_id: int | None = None
    listened_at: str | None = None
    archived_at: str | None = None
    created_at: str
    updated_at: str


class VoicemailRecordUpdate(BaseModel):
    status: Literal["new", "listened", "archived"] | None = None
    note: str | None = None
    customer_id: int | None = None
    ticket_id: int | None = None


class TwilioSetupStatusResponse(BaseModel):
    twilio_credentials_configured: bool
    public_webhook_base_url_configured: bool
    voice_webhook_url: str
    recording_callback_url: str
    recording_callback_route_active: bool
    last_voicemail: VoicemailRecordResponse | None = None


class JobDeadLetterResponse(BaseModel):
    id: int
    queue: str
    job_name: str
    payload: dict | None
    attempts: int
    error_message: str
    request_id: str | None
    created_at: str


class TicketSummaryListResponse(BaseModel):
    items: list[TicketSummaryResponse]
    total: int
    page: int
    page_size: int


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    entity_type: str
    entity_id: int | None
    action: str
    old_value: dict | list | str | int | float | bool | None
    new_value: dict | list | str | int | float | bool | None
    request_id: str | None
    created_at: str


class AuditLogListResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int


class QueryMetricEntryResponse(BaseModel):
    duration_ms: float
    sql: str
    request_id: str | None


class QueryMetricsResponse(BaseModel):
    total_queries: int
    total_duration_ms: float
    average_duration_ms: float
    slow_query_count: int
    slow_threshold_ms: float
    top_slowest: list[QueryMetricEntryResponse]


class RuntimeDiagnosticsResponse(BaseModel):
    database_type: str
    database_path: str | None = None
    database_url_configured: bool
    sqlite_under_var_data: bool | None = None
    persistence_status: str
    warning: str | None = None


# ============================================================================
# Phase 5: Inventory and Donor Devices
# ============================================================================


class PartCreate(BaseModel):
    part_number: str = Field(min_length=1)
    part_name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    device_compatibility: str | None = None
    supplier: str | None = None
    cost: float | None = None
    retail_price: float | None = None
    status: str = "In Stock"
    quantity_on_hand: int = 0
    quantity_ordered: int = 0
    reorder_level: int = 5
    reorder_quantity: int = 10
    notes: str | None = None


class PartUpdate(BaseModel):
    part_number: str | None = None
    part_name: str | None = None
    category: str | None = None
    device_compatibility: str | None = None
    supplier: str | None = None
    cost: float | None = None
    retail_price: float | None = None
    status: str | None = None
    quantity_on_hand: int | None = None
    quantity_ordered: int | None = None
    reorder_level: int | None = None
    reorder_quantity: int | None = None
    notes: str | None = None


class PartResponse(BaseModel):
    id: int
    part_number: str
    part_name: str
    category: str
    device_compatibility: str | None
    supplier: str | None
    cost: float | None
    retail_price: float | None
    status: str
    quantity_on_hand: int
    quantity_ordered: int
    reorder_level: int
    reorder_quantity: int
    notes: str | None
    created_at: str
    updated_at: str


class DonorCreate(BaseModel):
    device_identifier: str = Field(min_length=1)
    device_model: str = Field(min_length=1)
    status: str = "Available for Parts"
    condition_notes: str | None = None
    parts_harvested: list[int] = Field(default_factory=list)
    parts_available: list[int] = Field(default_factory=list)
    acquisition_date: str | None = None
    retirement_date: str | None = None


class DonorUpdate(BaseModel):
    device_identifier: str | None = None
    device_model: str | None = None
    status: str | None = None
    condition_notes: str | None = None
    parts_harvested: list[int] | None = None
    parts_available: list[int] | None = None
    acquisition_date: str | None = None
    retirement_date: str | None = None


class DonorResponse(BaseModel):
    id: int
    device_identifier: str
    device_model: str
    status: str
    condition_notes: str | None
    parts_harvested: list[int]
    parts_available: list[int]
    acquisition_date: str | None
    retirement_date: str | None
    created_at: str
    updated_at: str


class PartHarvestRequest(BaseModel):
    part_id: int


class PartUsageCreate(BaseModel):
    repair_action_id: int
    part_id: int
    quantity_used: int = Field(default=1, gt=0)


class PartUsageResponse(BaseModel):
    id: int
    repair_action_id: int
    part_id: int
    quantity_used: int
    created_at: str
    part_number: str
    part_name: str
    category: str | None
    ticket_id: int | None = None


class InventoryMovementResponse(BaseModel):
    id: int
    part_id: int | None
    donor_id: int | None
    movement_type: str
    quantity: int
    reason: str | None
    ticket_id: int | None
    repair_action_id: int | None
    actor_user_id: int | None
    request_id: str | None
    metadata: dict | None
    created_at: str


class InventoryMovementListResponse(BaseModel):
    items: list[InventoryMovementResponse]
    total: int
    page: int
    page_size: int


class PartStockAdjustmentRequest(BaseModel):
    quantity_delta: int
    movement_type: Literal["adjust", "transfer", "return", "correction"]
    reason: str = Field(min_length=1)
    ticket_id: int | None = None


class InventoryReconciliationRequest(BaseModel):
    part_id: int
    actual_quantity: int = Field(ge=0)
    reason: str = Field(min_length=1)
    apply_adjustment: bool = False
    resolved_by: str | None = None


class InventoryReconciliationResponse(BaseModel):
    id: int
    part_id: int
    expected_quantity: int
    actual_quantity: int
    discrepancy: int
    reason: str
    resolved_by: str | None
    created_at: str


class AttachmentResponse(BaseModel):
    id: int
    attachment_type: str
    entity_type: str
    entity_id: int
    storage_key: str
    original_filename: str
    mime_type: str
    file_size: int
    uploaded_by: int | None
    created_at: str


class AttachmentSignedUrlResponse(BaseModel):
    url: str
    expires_at: str


class AttachmentCleanupResponse(BaseModel):
    deleted_count: int
    deleted_keys: list[str]