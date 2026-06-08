import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
    createRepairCategory,
    fetchPricingRules,
    fetchRepairCategories,
    fetchStatusWorkflowRules,
    fetchSupportedModels,
    updateStatusWorkflowRules,
    updatePricingRules,
    updateRepairCategory,
    type PricingRules,
    type RepairCategory,
    type StatusWorkflowGuardrails,
    type StatusWorkflowRules,
    type SupportedModel,
} from "../api/tickets";
import {
    createDatabaseBackup,
    exportDataSnapshot,
    fetchLoanerAgreementDefaults,
    fetchNotificationTemplates,
    fetchSystemActivityHistory,
    fetchRuntimeDiagnostics,
    fetchTwilioSetupStatus,
    fetchTwilioSettings,
    clearTwilioSettings,
    updateLoanerAgreementDefaults,
    updateNotificationTemplates,
    updateTwilioSettings,
    type LoanerAgreementDefaults,
    type NotificationTemplate,
    type RuntimeDiagnostics,
    type SystemActivity,
    type TwilioSettings,
    type TwilioSetupStatus,
} from "../api/system";
import { useAsyncData } from "../hooks/useAsyncData";
import { PageHeader, SectionCard } from "../components/PageChrome";
import * as t from "../styles/theme";

// ─── localStorage helpers ───
function loadSetting<T>(key: string, fallback: T, legacyKeys: string[] = []): T {
    try {
        const raw = localStorage.getItem(key);
        if (raw) return JSON.parse(raw) as T;

        for (const legacyKey of legacyKeys) {
            const legacyRaw = localStorage.getItem(legacyKey);
            if (legacyRaw) {
                localStorage.setItem(key, legacyRaw);
                return JSON.parse(legacyRaw) as T;
            }
        }

        return fallback;
    } catch {
        return fallback;
    }
}
function saveSetting<T>(key: string, value: T) {
    localStorage.setItem(key, JSON.stringify(value));
}

// ─── default roster ───
const DEFAULT_ROSTER = ["Mattis"];

export default function SettingsPage() {
    const [settingsFocus, setSettingsFocus] = useState<"all" | "business" | "communications" | "workflow" | "system">("all");
    // Shop info
    const [shopName, setShopName] = useState(() => loadSetting<string>("techRestore.shopName", "Tech Restore", ["tag.shopName"]));
    const [shopPhone, setShopPhone] = useState(() => loadSetting<string>("techRestore.shopPhone", "", ["tag.shopPhone"]));
    const [shopEmail, setShopEmail] = useState(() => loadSetting<string>("techRestore.shopEmail", "", ["tag.shopEmail"]));
    const [shopSaved, setShopSaved] = useState(false);

    // Technician roster
    const [roster, setRoster] = useState<string[]>(() => loadSetting<string[]>("techRestore.techRoster", DEFAULT_ROSTER, ["tag.techRoster"]));
    const [newTech, setNewTech] = useState("");
    const [rosterSaved, setRosterSaved] = useState(false);

    // Pricing defaults
    const [laborRate, setLaborRate] = useState("");
    const [diagFee, setDiagFee] = useState("");
    const [warrantyDays, setWarrantyDays] = useState(() => loadSetting<string>("techRestore.warrantyDays", "90", ["tag.warrantyDays"]));
    const [pricingSaved, setPricingSaved] = useState(false);
    const [pricingError, setPricingError] = useState<string | null>(null);
    const [pricingRulesRefreshKey, setPricingRulesRefreshKey] = useState(0);
    const [repairCategoryRefreshKey, setRepairCategoryRefreshKey] = useState(0);
    const [repairCategoryBusyId, setRepairCategoryBusyId] = useState<number | null>(null);
    const [repairCategoryMessage, setRepairCategoryMessage] = useState<string | null>(null);
    const [repairCategoryError, setRepairCategoryError] = useState<string | null>(null);
    const [workflowRulesRefreshKey, setWorkflowRulesRefreshKey] = useState(0);
    const [workflowTransitionsDraft, setWorkflowTransitionsDraft] = useState<Record<string, string>>({});
    const [workflowGuardrailsDraft, setWorkflowGuardrailsDraft] = useState<StatusWorkflowGuardrails | null>(null);
    const [workflowMessage, setWorkflowMessage] = useState<string | null>(null);
    const [workflowError, setWorkflowError] = useState<string | null>(null);
    const [loanerDefaultsRefreshKey, setLoanerDefaultsRefreshKey] = useState(0);
    const [loanerDefaultsDraft, setLoanerDefaultsDraft] = useState<LoanerAgreementDefaults | null>(null);
    const [loanerDefaultsMessage, setLoanerDefaultsMessage] = useState<string | null>(null);
    const [loanerDefaultsError, setLoanerDefaultsError] = useState<string | null>(null);
    const [notificationTemplatesRefreshKey, setNotificationTemplatesRefreshKey] = useState(0);
    const [notificationTemplatesDraft, setNotificationTemplatesDraft] = useState<Record<string, string>>({});
    const [notificationTemplatesMessage, setNotificationTemplatesMessage] = useState<string | null>(null);
    const [notificationTemplatesError, setNotificationTemplatesError] = useState<string | null>(null);
    const [twilioRefreshKey, setTwilioRefreshKey] = useState(0);
    const [twilioDraft, setTwilioDraft] = useState<TwilioSettings | null>(null);
    const [twilioAuthToken, setTwilioAuthToken] = useState("");
    const [showTwilioToken, setShowTwilioToken] = useState(false);
    const [twilioMessage, setTwilioMessage] = useState<string | null>(null);
    const [twilioError, setTwilioError] = useState<string | null>(null);
    const [newCategory, setNewCategory] = useState({
        name: "",
        description: "",
        default_policy: "",
        requires_soldering: false,
    });
    const [systemBusy, setSystemBusy] = useState<"backup" | "export" | null>(null);
    const [systemMessage, setSystemMessage] = useState<string | null>(null);
    const [systemError, setSystemError] = useState<string | null>(null);
    const [systemHistoryRefreshKey, setSystemHistoryRefreshKey] = useState(0);
    const { data: systemHistory = [], error: systemHistoryError } = useAsyncData<SystemActivity[]>(
        () => fetchSystemActivityHistory(),
        [systemHistoryRefreshKey]
    );
    const { data: runtimeDiagnostics, error: runtimeDiagnosticsError } = useAsyncData<RuntimeDiagnostics>(
        () => fetchRuntimeDiagnostics(),
        [systemHistoryRefreshKey, twilioRefreshKey]
    );
    const { data: supportedModels = [], error: supportedModelsError } = useAsyncData<SupportedModel[]>(() => fetchSupportedModels(), []);
    const { data: pricingRules, error: pricingRulesError } = useAsyncData<PricingRules>(() => fetchPricingRules(), [pricingRulesRefreshKey]);
    const { data: statusWorkflowRules } = useAsyncData<StatusWorkflowRules>(() => fetchStatusWorkflowRules(), [workflowRulesRefreshKey]);
    const { data: loanerAgreementDefaults } = useAsyncData<LoanerAgreementDefaults>(
        () => fetchLoanerAgreementDefaults(),
        [loanerDefaultsRefreshKey]
    );
    const { data: notificationTemplates = [] } = useAsyncData<NotificationTemplate[]>(
        () => fetchNotificationTemplates(),
        [notificationTemplatesRefreshKey]
    );
    const { data: twilioSettings } = useAsyncData<TwilioSettings>(
        () => fetchTwilioSettings(),
        [twilioRefreshKey]
    );
    const { data: twilioSetupStatus, error: twilioSetupStatusError } = useAsyncData<TwilioSetupStatus>(
        () => fetchTwilioSetupStatus(),
        [twilioRefreshKey]
    );
    const { data: managedRepairCategories = [], error: managedRepairCategoriesError } = useAsyncData<RepairCategory[]>(
        () => fetchRepairCategories(true),
        [repairCategoryRefreshKey]
    );

    const deviceFamilies = Array.from(new Set(supportedModels.map((model) => model.device_family))).sort((left, right) => left.localeCompare(right));
    const repairCategories = pricingRules?.repair_categories ?? [];

    // Reset saved flash after 2s
    useEffect(() => {
        if (shopSaved) {
            const t = setTimeout(() => setShopSaved(false), 2000);
            return () => clearTimeout(t);
        }
    }, [shopSaved]);
    useEffect(() => {
        if (rosterSaved) {
            const t = setTimeout(() => setRosterSaved(false), 2000);
            return () => clearTimeout(t);
        }
    }, [rosterSaved]);
    useEffect(() => {
        if (pricingSaved) {
            const t = setTimeout(() => setPricingSaved(false), 2000);
            return () => clearTimeout(t);
        }
    }, [pricingSaved]);
    useEffect(() => {
        if (!pricingRules) {
            return;
        }
        setLaborRate(String(pricingRules.defaults.base_labor_rate_per_hour));
        setDiagFee(String(pricingRules.defaults.diagnostic_fee));
    }, [pricingRules]);
    useEffect(() => {
        if (!statusWorkflowRules) {
            return;
        }
        const nextDraft: Record<string, string> = {};
        Object.entries(statusWorkflowRules.transitions).forEach(([fromStatus, targets]) => {
            nextDraft[fromStatus] = targets.join(", ");
        });
        setWorkflowTransitionsDraft(nextDraft);
        setWorkflowGuardrailsDraft(statusWorkflowRules.guardrails);
    }, [statusWorkflowRules]);
    useEffect(() => {
        if (!loanerAgreementDefaults) {
            return;
        }
        setLoanerDefaultsDraft(loanerAgreementDefaults);
    }, [loanerAgreementDefaults]);

    useEffect(() => {
        if (notificationTemplates.length === 0) {
            return;
        }
        const nextDraft: Record<string, string> = {};
        notificationTemplates.forEach((template) => {
            nextDraft[template.template_key] = template.template_text;
        });
        setNotificationTemplatesDraft(nextDraft);
    }, [notificationTemplates]);

    useEffect(() => {
        if (!twilioSettings) {
            return;
        }
        setTwilioDraft(twilioSettings);
        setTwilioAuthToken("");
    }, [twilioSettings]);

    function handleSaveShop(e: React.FormEvent) {
        e.preventDefault();
        saveSetting("techRestore.shopName", shopName);
        saveSetting("techRestore.shopPhone", shopPhone);
        saveSetting("techRestore.shopEmail", shopEmail);
        setShopSaved(true);
    }

    function handleAddTech(e: React.FormEvent) {
        e.preventDefault();
        const name = newTech.trim();
        if (!name || roster.includes(name)) return;
        const updated = [...roster, name];
        setRoster(updated);
        saveSetting("techRestore.techRoster", updated);
        setNewTech("");
        setRosterSaved(true);
    }

    function handleRemoveTech(name: string) {
        const updated = roster.filter((n) => n !== name);
        setRoster(updated);
        saveSetting("techRestore.techRoster", updated);
    }

    async function handleSavePricing(e: React.FormEvent) {
        e.preventDefault();
        setPricingError(null);
        saveSetting("techRestore.warrantyDays", warrantyDays);
        const laborRateNumber = Number(laborRate);
        const diagFeeNumber = Number(diagFee);
        if (Number.isNaN(laborRateNumber) || Number.isNaN(diagFeeNumber)) {
            setPricingError("Labor rate and diagnostic fee must be valid numbers.");
            return;
        }

        try {
            await updatePricingRules({
                base_labor_rate_per_hour: laborRateNumber,
                diagnostic_fee: diagFeeNumber,
            });
            setPricingSaved(true);
            setPricingRulesRefreshKey((current) => current + 1);
        } catch (error) {
            setPricingError(error instanceof Error ? error.message : "Unable to save pricing defaults");
        }
    }

    async function handleCreateRepairCategory(e: React.FormEvent) {
        e.preventDefault();
        const name = newCategory.name.trim();
        if (!name) {
            setRepairCategoryError("Category name is required.");
            return;
        }

        try {
            setRepairCategoryError(null);
            await createRepairCategory({
                name,
                description: newCategory.description.trim() || null,
                default_policy: newCategory.default_policy.trim() || null,
                requires_soldering: newCategory.requires_soldering,
            });
            setRepairCategoryMessage(`Created category: ${name}`);
            setNewCategory({ name: "", description: "", default_policy: "", requires_soldering: false });
            setPricingRulesRefreshKey((current) => current + 1);
            setRepairCategoryRefreshKey((current) => current + 1);
        } catch (error) {
            setRepairCategoryError(error instanceof Error ? error.message : "Could not create repair category");
        }
    }

    async function handleToggleCategory(category: RepairCategory) {
        try {
            setRepairCategoryError(null);
            setRepairCategoryBusyId(category.id);
            await updateRepairCategory(category.id, { active: !category.active });
            setRepairCategoryMessage(
                `${category.name} marked as ${category.active ? "inactive" : "active"}.`
            );
            setPricingRulesRefreshKey((current) => current + 1);
            setRepairCategoryRefreshKey((current) => current + 1);
        } catch (error) {
            setRepairCategoryError(error instanceof Error ? error.message : "Could not update repair category");
        } finally {
            setRepairCategoryBusyId(null);
        }
    }

    async function handleSaveWorkflowRules(e: React.FormEvent) {
        e.preventDefault();
        if (!workflowGuardrailsDraft) {
            return;
        }

        try {
            setWorkflowError(null);
            const normalized: Record<string, string[]> = {};
            Object.entries(workflowTransitionsDraft).forEach(([fromStatus, rawTargets]) => {
                const targets = rawTargets
                    .split(",")
                    .map((item) => item.trim())
                    .filter(Boolean);
                normalized[fromStatus] = Array.from(new Set(targets));
            });

            await updateStatusWorkflowRules({
                transitions: normalized,
                guardrails: workflowGuardrailsDraft,
            });
            setWorkflowMessage("Status workflow rules saved.");
            setWorkflowRulesRefreshKey((current) => current + 1);
        } catch (error) {
            setWorkflowError(error instanceof Error ? error.message : "Could not save status workflow rules");
        }
    }

    async function handleSaveLoanerAgreementDefaults(e: React.FormEvent) {
        e.preventDefault();
        if (!loanerDefaultsDraft) {
            return;
        }

        try {
            setLoanerDefaultsError(null);
            await updateLoanerAgreementDefaults({
                responsibility_text: loanerDefaultsDraft.responsibility_text,
                return_policy_text: loanerDefaultsDraft.return_policy_text,
                signature_note_text: loanerDefaultsDraft.signature_note_text,
            });
            setLoanerDefaultsMessage("Loaner agreement defaults saved.");
            setLoanerDefaultsRefreshKey((current) => current + 1);
        } catch (error) {
            setLoanerDefaultsError(error instanceof Error ? error.message : "Could not save loaner agreement defaults");
        }
    }

    async function handleSaveNotificationTemplates(e: React.FormEvent) {
        e.preventDefault();
        if (Object.keys(notificationTemplatesDraft).length === 0) {
            return;
        }

        try {
            setNotificationTemplatesError(null);
            const payload: Record<string, { template_text: string }> = {};
            Object.entries(notificationTemplatesDraft).forEach(([key, text]) => {
                payload[key] = { template_text: text };
            });
            await updateNotificationTemplates(payload);
            setNotificationTemplatesMessage("Notification templates saved.");
            setNotificationTemplatesRefreshKey((current) => current + 1);
        } catch (error) {
            setNotificationTemplatesError(error instanceof Error ? error.message : "Could not save notification templates");
        }
    }

    async function handleSaveTwilioSettings(e: React.FormEvent) {
        e.preventDefault();
        if (!twilioDraft) {
            return;
        }

        try {
            setTwilioError(null);
            const next = await updateTwilioSettings({
                account_sid: twilioDraft.account_sid,
                phone_number: twilioDraft.phone_number,
                public_webhook_base_url: twilioDraft.public_webhook_base_url,
                voicemail_greeting: twilioDraft.voicemail_greeting,
                voicemail_greeting_audio_url: twilioDraft.voicemail_greeting_audio_url,
                auth_token: twilioAuthToken.trim() ? twilioAuthToken.trim() : undefined,
            });
            setTwilioDraft(next);
            setTwilioAuthToken("");
            setShowTwilioToken(false);
            setTwilioMessage(next.configured ? "Twilio settings saved and configured." : "Twilio settings saved.");
            setTwilioRefreshKey((current) => current + 1);
        } catch (error) {
            setTwilioError(error instanceof Error ? error.message : "Could not save Twilio settings");
        }
    }

    async function handleClearTwilioSettings() {
        try {
            setTwilioError(null);
            const next = await clearTwilioSettings();
            setTwilioDraft(next);
            setTwilioAuthToken("");
            setShowTwilioToken(false);
            setTwilioMessage("Twilio credentials cleared.");
            setTwilioRefreshKey((current) => current + 1);
        } catch (error) {
            setTwilioError(error instanceof Error ? error.message : "Could not clear Twilio settings");
        }
    }

    function refreshSystemHistory() {
        setSystemHistoryRefreshKey((current) => current + 1);
    }

    async function handleCreateBackup() {
        try {
            setSystemBusy("backup");
            setSystemError(null);
            const result = await createDatabaseBackup();
            setSystemMessage(`Backup created: ${result.file_name}`);
            refreshSystemHistory();
        } catch (error) {
            setSystemError(error instanceof Error ? error.message : "Backup failed");
        } finally {
            setSystemBusy(null);
        }
    }

    async function handleExportData() {
        try {
            setSystemBusy("export");
            setSystemError(null);
            const { fileName, blob } = await exportDataSnapshot();
            const url = window.URL.createObjectURL(blob);
            const anchor = document.createElement("a");
            anchor.href = url;
            anchor.download = fileName;
            anchor.click();
            window.URL.revokeObjectURL(url);
            setSystemMessage(`Export ready: ${fileName}`);
            refreshSystemHistory();
        } catch (error) {
            setSystemError(error instanceof Error ? error.message : "Export failed");
        } finally {
            setSystemBusy(null);
        }
    }

    const twilioReady = Boolean(
        twilioSetupStatus?.twilio_credentials_configured && twilioSetupStatus?.public_webhook_base_url_configured
    );
    const activeCategoryCount = managedRepairCategories.filter((category) => category.active).length;
    const workflowRuleCount = Object.keys(workflowTransitionsDraft).length;
    const showSection = (section: "business" | "communications" | "workflow" | "system") => settingsFocus === "all" || settingsFocus === section;

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Administration"
                title="Settings"
                description="Business info, phone and voicemail, workflow policy, templates, and system backup tools."
            />

            <SectionCard title="Settings sections" compact>
                <div style={{ ...t.formStack, gap: "10px" }}>
                    <div style={{ ...t.formActionsRow, justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                            <strong style={{ color: "#153d47" }}>Focused mode</strong>
                            <div style={{ ...t.meta, marginTop: "4px" }}>Show one section at a time for faster admin work.</div>
                        </div>
                        <div style={{ ...t.formActionsRow, gap: "8px" }}>
                            <button type="button" style={settingsFocus === "all" ? t.primaryBtn : t.miniBtn} onClick={() => setSettingsFocus("all")}>All</button>
                            <button type="button" style={settingsFocus === "business" ? t.primaryBtn : t.miniBtn} onClick={() => setSettingsFocus("business")}>Business Info</button>
                            <button type="button" style={settingsFocus === "communications" ? t.primaryBtn : t.miniBtn} onClick={() => setSettingsFocus("communications")}>Phone / Voicemail</button>
                            <button type="button" style={settingsFocus === "workflow" ? t.primaryBtn : t.miniBtn} onClick={() => setSettingsFocus("workflow")}>Ticket Workflow</button>
                            <button type="button" style={settingsFocus === "system" ? t.primaryBtn : t.miniBtn} onClick={() => setSettingsFocus("system")}>System / Backup</button>
                        </div>
                    </div>
                    <div style={{ ...t.formActionsRow, gap: "8px" }}>
                        <a href="#settings-business" style={{ ...t.miniBtn, textDecoration: "none" }}>Business info</a>
                        <a href="#settings-communications" style={{ ...t.miniBtn, textDecoration: "none" }}>Phone / voicemail</a>
                        <a href="#settings-workflow" style={{ ...t.miniBtn, textDecoration: "none" }}>Ticket workflow</a>
                        <a href="#settings-system" style={{ ...t.miniBtn, textDecoration: "none" }}>System / backup</a>
                        <Link to="/market-updates-admin" style={{ ...t.miniBtn, textDecoration: "none" }}>Market SMS admin</Link>
                    </div>
                </div>
                <div style={t.fieldGridTwoCompact}>
                    <div style={statusTileStyle}>
                        <div style={statusTileLabelStyle}>Technicians</div>
                        <div style={statusTileValueStyle}>{roster.length}</div>
                    </div>
                    <div style={statusTileStyle}>
                        <div style={statusTileLabelStyle}>Active categories</div>
                        <div style={statusTileValueStyle}>{activeCategoryCount}</div>
                    </div>
                    <div style={statusTileStyle}>
                        <div style={statusTileLabelStyle}>Workflow states</div>
                        <div style={statusTileValueStyle}>{workflowRuleCount}</div>
                    </div>
                    <div style={statusTileStyle}>
                        <div style={statusTileLabelStyle}>Twilio readiness</div>
                        <div style={statusTileValueStyle}>{twilioReady ? "Ready" : "Needs setup"}</div>
                    </div>
                </div>
            </SectionCard>

            {showSection("business") ? <div id="settings-business" style={sectionLabelStyle}>Business Info</div> : null}

            {/* ── Shop Info ── */}
            {showSection("business") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Shop info</h3>
                <form onSubmit={handleSaveShop} style={t.formStack}>
                    <label style={t.label}>
                        Shop name
                        <input value={shopName} onChange={(e) => setShopName(e.target.value)} style={{ ...t.input, marginTop: "4px" }} placeholder="Tech Restore" />
                    </label>
                    <label style={t.label}>
                        Phone
                        <input value={shopPhone} onChange={(e) => setShopPhone(e.target.value)} style={{ ...t.input, marginTop: "4px" }} placeholder="(555) 000-0000" />
                    </label>
                    <label style={t.label}>
                        Email
                        <input value={shopEmail} onChange={(e) => setShopEmail(e.target.value)} type="email" style={{ ...t.input, marginTop: "4px" }} placeholder="repairs@example.com" />
                    </label>
                    <div style={t.formActionsRow}>
                        <button type="submit" style={t.primaryBtn}>Save shop info</button>
                        {shopSaved && <span style={savedChip}>Saved!</span>}
                    </div>
                </form>
            </div> : null}

            {showSection("communications") ? <div style={t.detailGrid}>
                <div>
                    <div id="settings-communications" style={sectionLabelStyle}>Phone / Voicemail</div>
                    <p style={{ ...t.meta, marginTop: 0, marginBottom: "10px" }}>Twilio voice setup and customer messaging templates.</p>
                </div>
            </div> : null}

            {showSection("communications") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Phone / Twilio</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    Connect a Twilio number to receive unanswered calls and store voicemail recordings inside Tech Restore.
                </p>
                {twilioDraft ? (
                    <form onSubmit={handleSaveTwilioSettings} style={t.formStack}>
                        <div style={t.fieldGridTwo}>
                            <label style={t.label}>
                                Twilio Account SID
                                <input
                                    value={twilioDraft.account_sid ?? ""}
                                    onChange={(event) => setTwilioDraft((current) => current ? { ...current, account_sid: event.target.value } : current)}
                                    placeholder="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                                    style={{ ...t.input, marginTop: "4px" }}
                                />
                            </label>
                            <label style={t.label}>
                                Twilio Phone Number
                                <input
                                    value={twilioDraft.phone_number ?? ""}
                                    onChange={(event) => setTwilioDraft((current) => current ? { ...current, phone_number: event.target.value } : current)}
                                    placeholder="+15555550123"
                                    style={{ ...t.input, marginTop: "4px" }}
                                />
                            </label>
                        </div>

                        <label style={t.label}>
                            Twilio Auth Token
                            <input
                                type={showTwilioToken ? "text" : "password"}
                                value={twilioAuthToken}
                                onChange={(event) => setTwilioAuthToken(event.target.value)}
                                placeholder={twilioDraft.twilio_auth_token_set ? "Stored securely - enter a new token to replace it" : "Enter Twilio auth token"}
                                style={{ ...t.input, marginTop: "4px" }}
                            />
                        </label>
                        <div style={{ ...t.formActionsRow, gap: "8px" }}>
                            <button type="button" style={t.secondaryBtn} onClick={() => setShowTwilioToken((current) => !current)}>
                                {showTwilioToken ? "Hide token" : "Show token"}
                            </button>
                            <span style={savedChip}>{twilioDraft.twilio_auth_token_set ? "Token stored" : "No token saved"}</span>
                            <span style={savedChip}>{twilioDraft.configured ? "Configured" : "Not configured"}</span>
                        </div>

                        <label style={t.label}>
                            Public webhook base URL
                            <input
                                value={twilioDraft.public_webhook_base_url ?? ""}
                                onChange={(event) => setTwilioDraft((current) => current ? { ...current, public_webhook_base_url: event.target.value } : current)}
                                placeholder="https://your-tunnel-url.ngrok.app"
                                style={{ ...t.input, marginTop: "4px" }}
                            />
                        </label>

                        <label style={t.label}>
                            Voicemail greeting
                            <textarea
                                value={twilioDraft.voicemail_greeting ?? ""}
                                onChange={(event) => setTwilioDraft((current) => current ? { ...current, voicemail_greeting: event.target.value } : current)}
                                placeholder="Thank you for calling Tech Restore..."
                                style={{ ...t.input, marginTop: "4px", minHeight: "90px" }}
                            />
                        </label>

                        <label style={t.label}>
                            Greeting audio URL (optional)
                            <input
                                value={twilioDraft.voicemail_greeting_audio_url ?? ""}
                                onChange={(event) => setTwilioDraft((current) => current ? { ...current, voicemail_greeting_audio_url: event.target.value } : current)}
                                placeholder="https://.../greeting.mp3"
                                style={{ ...t.input, marginTop: "4px" }}
                            />
                            <span style={t.meta}>If set, Twilio will play this audio file instead of text-to-speech.</span>
                        </label>

                        {!twilioDraft.public_webhook_base_url ? (
                            <div style={constraintChip}>
                                Warning: Twilio cannot reach localhost directly. Use ngrok, Cloudflare Tunnel, or another public URL for testing.
                            </div>
                        ) : null}

                        <div style={{ ...t.subCard, display: "grid", gap: "8px" }}>
                            <strong>Twilio setup steps</strong>
                            <div style={t.meta}>1. In Twilio Console, open the phone number.</div>
                            <div style={t.meta}>2. Under Voice configuration, set the incoming call webhook to:</div>
                            <div style={{ ...t.meta, wordBreak: "break-word" }}>
                                {twilioDraft.public_webhook_base_url ? `${twilioDraft.public_webhook_base_url.replace(/\/$/, "")}/api/twilio/voice` : "[publicWebhookBaseUrl]/api/twilio/voice"}
                            </div>
                            <div style={t.meta}>3. Use HTTP POST and save the phone number settings.</div>
                            <div style={t.meta}>4. Twilio will send unanswered calls to voicemail and Tech Restore will capture the recording callback.</div>
                        </div>

                        <div style={{ ...t.subCard, display: "grid", gap: "8px" }}>
                            <strong>Test setup status</strong>
                            {twilioSetupStatus ? (
                                <>
                                    <div style={t.meta}>Twilio credentials configured: {twilioSetupStatus.twilio_credentials_configured ? "OK" : "Missing"}</div>
                                    <div style={t.meta}>Public webhook base URL configured: {twilioSetupStatus.public_webhook_base_url_configured ? "OK" : "Missing"}</div>
                                    <div style={{ ...t.meta, wordBreak: "break-word" }}>Voice webhook URL to paste: {twilioSetupStatus.voice_webhook_url}</div>
                                    <div style={t.meta}>Recording callback route active: {twilioSetupStatus.recording_callback_route_active ? "OK" : "Missing"}</div>
                                    <div style={{ ...t.meta, wordBreak: "break-word" }}>Recording callback URL: {twilioSetupStatus.recording_callback_url}</div>
                                    <div style={t.meta}>
                                        Last voicemail received: {twilioSetupStatus.last_voicemail ? new Date(twilioSetupStatus.last_voicemail.created_at).toLocaleString() : "None yet"}
                                    </div>
                                </>
                            ) : (
                                <div style={t.meta}>Loading setup status…</div>
                            )}
                            {twilioSetupStatusError ? <div style={{ ...t.meta, color: "#9b2c2c" }}>{twilioSetupStatusError}</div> : null}
                            {twilioSetupStatus?.voice_webhook_url ? (
                                <button
                                    type="button"
                                    style={{ ...t.miniBtn, justifySelf: "start" }}
                                    onClick={() => {
                                        void navigator.clipboard?.writeText(twilioSetupStatus.voice_webhook_url);
                                        setTwilioMessage("Voice webhook URL copied.");
                                    }}
                                >
                                    Copy voice webhook URL
                                </button>
                            ) : null}
                        </div>

                        {twilioError ? <div style={t.errorBanner}>{twilioError}</div> : null}
                        {twilioMessage ? <div style={{ ...constraintChip, background: "#d1fae5", color: "#065f46", borderColor: "#a7f3d0" }}>{twilioMessage}</div> : null}

                        <div style={t.formActionsRow}>
                            <button type="submit" style={t.primaryBtn}>Save Twilio settings</button>
                            <button type="button" style={t.secondaryBtn} onClick={handleClearTwilioSettings}>Clear credentials</button>
                            <a href="/voicemail" style={{ ...t.secondaryBtn, textDecoration: "none", display: "inline-flex", alignItems: "center" }}>
                                Open voicemail inbox
                            </a>
                        </div>
                    </form>
                ) : (
                    <p style={t.copy}>Loading Twilio settings…</p>
                )}
            </div> : null}

            {/* ── Technician Roster ── */}
            {showSection("business") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Technician roster</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    These names will appear in Queue assignment in a future phase.
                </p>
                <div style={{ ...t.formActionsRow, gap: "8px", marginBottom: "14px" }}>
                    {roster.map((name) => (
                        <span key={name} style={techChip}>
                            {name}
                            <button
                                type="button"
                                onClick={() => handleRemoveTech(name)}
                                style={removeBtnStyle}
                                aria-label={`Remove ${name}`}
                            >x</button>
                        </span>
                    ))}
                    {roster.length === 0 && <span style={{ ...t.copy, fontSize: "0.88rem", fontStyle: "italic" }}>No technicians added yet.</span>}
                </div>
                <form onSubmit={handleAddTech} style={{ ...t.formActionsRow, gap: "8px" }}>
                    <input
                        value={newTech}
                        onChange={(e) => setNewTech(e.target.value)}
                        placeholder="Add technician name"
                        style={{ ...t.input, flex: "1 1 260px", minWidth: 0, maxWidth: "420px" }}
                    />
                    <button type="submit" style={t.secondaryBtn} disabled={!newTech.trim()}>Add</button>
                    {rosterSaved && <span style={savedChip}>Saved!</span>}
                </form>
            </div> : null}

            {showSection("workflow") ? <div id="settings-workflow" style={sectionLabelStyle}>Ticket Workflow</div> : null}

            {showSection("workflow") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Pricing management moved</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    Pricing defaults, brands, models, issue types, repair types, and rule catalog editing now live in the dedicated Pricing page.
                </p>
                <div style={t.formActionsRow}>
                    <Link to="/pricing" style={{ ...t.primaryBtn, textDecoration: "none" }}>Open Pricing page</Link>
                </div>
            </div> : null}

            {/* ── Phase constraints ── */}
            {showSection("workflow") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Phase 1 service constraints</h3>
                <div style={{ ...t.formActionsRow, gap: "8px" }}>
                    <span style={constraintChip}>No soldering-based charging-port repair in standard v1</span>
                    <span style={constraintChip}>No soldering-based microphone repair in standard v1</span>
                </div>
            </div> : null}

            {showSection("system") ? <div id="settings-system" style={sectionLabelStyle}>System / Backup</div> : null}

            {showSection("system") ? (
                <div style={panelStyle}>
                    <h3 style={{ marginTop: 0 }}>System status</h3>
                    <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                        Quick diagnostics for persistence, deployment version, API base URL, and Twilio readiness.
                    </p>
                    {runtimeDiagnostics ? (
                        <div style={t.detailGrid}>
                            <div style={t.subCard}><strong>Backend</strong><div style={t.meta}>Online: {runtimeDiagnostics.backend_online ? "Yes" : "No"}</div><div style={t.meta}>Version: {runtimeDiagnostics.backend_version ?? "Unknown"}</div><div style={t.meta}>Commit: {runtimeDiagnostics.backend_commit ?? "Unknown"}</div></div>
                            <div style={t.subCard}><strong>Frontend</strong><div style={t.meta}>Commit: {runtimeDiagnostics.frontend_commit ?? "Unknown"}</div><div style={t.meta}>Environment: {runtimeDiagnostics.environment ?? "Unknown"}</div><div style={{ ...t.meta, wordBreak: "break-word" }}>API URL: {runtimeDiagnostics.api_base_url ?? "Unknown"}</div></div>
                            <div style={t.subCard}><strong>Database</strong><div style={t.meta}>Type: {runtimeDiagnostics.database_type}</div><div style={t.meta}>Persistence: {runtimeDiagnostics.persistence_status === "persistent_disk" ? "Persistent disk" : "Ephemeral or unknown"}</div><div style={{ ...t.meta, wordBreak: "break-word" }}>Path: {runtimeDiagnostics.database_path ?? "Unknown"}</div></div>
                            <div style={t.subCard}><strong>Twilio</strong><div style={t.meta}>Configured: {runtimeDiagnostics.twilio_configured ? "Yes" : "No"}</div><div style={t.meta}>Webhook ready: {twilioReady ? "Yes" : "No"}</div></div>
                        </div>
                    ) : (
                        <p style={t.copy}>Loading runtime diagnostics...</p>
                    )}
                    {runtimeDiagnostics?.warning ? <div style={{ ...constraintChip, marginTop: "10px" }}>{runtimeDiagnostics.warning}</div> : null}
                    {runtimeDiagnosticsError ? <p style={{ ...t.copy, color: "#9b2c2c", marginTop: "10px" }}>{runtimeDiagnosticsError}</p> : null}
                </div>
            ) : null}

            {showSection("system") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Backup & export</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    Create a local SQLite backup or export the current database snapshot as JSON.
                </p>
                <div style={t.formActionsRow}>
                    <button type="button" style={t.primaryBtn} onClick={handleCreateBackup} disabled={systemBusy !== null}>
                        {systemBusy === "backup" ? "Creating backup..." : "Create backup"}
                    </button>
                    <button type="button" style={t.secondaryBtn} onClick={handleExportData} disabled={systemBusy !== null}>
                        {systemBusy === "export" ? "Preparing export..." : "Export JSON snapshot"}
                    </button>
                </div>
                {systemMessage ? <p style={{ ...t.copy, color: "#065f46", marginTop: "12px" }}>{systemMessage}</p> : null}
                {systemError ? <p style={{ ...t.copy, color: "#9b2c2c", marginTop: "12px" }}>{systemError}</p> : null}
                <div style={{ marginTop: "18px" }}>
                    <h4 style={{ margin: 0, marginBottom: "10px", color: "#173f37" }}>Recent system activity</h4>
                    {systemHistoryError ? <p style={{ ...t.copy, color: "#9b2c2c" }}>{systemHistoryError}</p> : null}
                    {systemHistory.length === 0 ? (
                        <p style={t.copy}>No backups or exports recorded yet.</p>
                    ) : (
                        <div style={{ ...t.formStack, gap: "10px" }}>
                            {systemHistory.map((item) => (
                                <div key={`${item.activity_type}-${item.created_at}-${item.file_name}`} style={t.subCard}>
                                    <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
                                        <strong>{item.file_name}</strong>
                                        <span style={t.meta}>{item.activity_type === "backup" ? "Backup" : "Export"}</span>
                                    </div>
                                    <div style={{ ...t.meta, marginTop: "6px" }}>
                                        {new Date(item.created_at).toLocaleString()} · {(item.file_size_bytes / 1024).toFixed(1)} KB
                                    </div>
                                    {item.file_path ? <div style={{ marginTop: "8px", wordBreak: "break-word" }}>{item.file_path}</div> : null}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div> : null}

            {showSection("workflow") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Pricing catalog ownership</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    This settings page keeps workflow rules and communications. Pricing catalog administration is centralized under Pricing to avoid split ownership.
                </p>
                <div style={t.formActionsRow}>
                    <Link to="/pricing" style={{ ...t.secondaryBtn, textDecoration: "none" }}>Go to Pricing catalog</Link>
                </div>
            </div> : null}

            {showSection("workflow") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Status workflow editor</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    Configure allowed status transitions and enforcement guardrails used by ticket updates.
                </p>
                <form onSubmit={handleSaveWorkflowRules} style={t.formStack}>
                    {Object.keys(workflowTransitionsDraft).map((fromStatus) => (
                        <label key={fromStatus} style={t.label}>
                            {fromStatus} → allowed next statuses (comma-separated)
                            <input
                                value={workflowTransitionsDraft[fromStatus] ?? ""}
                                onChange={(event) =>
                                    setWorkflowTransitionsDraft((current) => ({
                                        ...current,
                                        [fromStatus]: event.target.value,
                                    }))
                                }
                                style={{ ...t.input, marginTop: "4px" }}
                            />
                        </label>
                    ))}
                    {workflowGuardrailsDraft ? (
                        <div style={{ ...t.subCard, display: "grid", gap: "8px" }}>
                            <label style={{ ...t.label, display: "inline-flex", alignItems: "center", gap: "8px" }}>
                                <input
                                    type="checkbox"
                                    checked={workflowGuardrailsDraft.enforce_no_active_loaner_for_ready_for_pickup}
                                    onChange={(event) =>
                                        setWorkflowGuardrailsDraft((current) =>
                                            current
                                                ? {
                                                    ...current,
                                                    enforce_no_active_loaner_for_ready_for_pickup: event.target.checked,
                                                }
                                                : current
                                        )
                                    }
                                />
                                Block Ready for Pickup while loaner is still checked out
                            </label>
                            <label style={{ ...t.label, display: "inline-flex", alignItems: "center", gap: "8px" }}>
                                <input
                                    type="checkbox"
                                    checked={workflowGuardrailsDraft.enforce_no_active_loaner_for_closed_statuses}
                                    onChange={(event) =>
                                        setWorkflowGuardrailsDraft((current) =>
                                            current
                                                ? {
                                                    ...current,
                                                    enforce_no_active_loaner_for_closed_statuses: event.target.checked,
                                                }
                                                : current
                                        )
                                    }
                                />
                                Block closed statuses while loaner is still checked out
                            </label>
                            <label style={{ ...t.label, display: "inline-flex", alignItems: "center", gap: "8px" }}>
                                <input
                                    type="checkbox"
                                    checked={workflowGuardrailsDraft.enforce_final_price_for_ready_for_pickup}
                                    onChange={(event) =>
                                        setWorkflowGuardrailsDraft((current) =>
                                            current
                                                ? {
                                                    ...current,
                                                    enforce_final_price_for_ready_for_pickup: event.target.checked,
                                                }
                                                : current
                                        )
                                    }
                                />
                                Require final price before Ready for Pickup
                            </label>
                            <label style={{ ...t.label, display: "inline-flex", alignItems: "center", gap: "8px" }}>
                                <input
                                    type="checkbox"
                                    checked={workflowGuardrailsDraft.enforce_final_price_for_closed_paid_statuses}
                                    onChange={(event) =>
                                        setWorkflowGuardrailsDraft((current) =>
                                            current
                                                ? {
                                                    ...current,
                                                    enforce_final_price_for_closed_paid_statuses: event.target.checked,
                                                }
                                                : current
                                        )
                                    }
                                />
                                Require final price before paid close statuses
                            </label>
                        </div>
                    ) : null}
                    <div>
                        <button type="submit" style={t.primaryBtn}>Save workflow rules</button>
                    </div>
                </form>
                {workflowError ? <p style={{ ...t.copy, color: "#9b2c2c", marginTop: "12px" }}>{workflowError}</p> : null}
                {workflowMessage ? <p style={{ ...t.copy, color: "#065f46", marginTop: "12px" }}>{workflowMessage}</p> : null}
            </div> : null}

            {showSection("communications") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Loaner agreement defaults</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    Edit default acknowledgement copy used by the printable loaner agreement page.
                </p>
                {loanerDefaultsDraft ? (
                    <form onSubmit={handleSaveLoanerAgreementDefaults} style={t.formStack}>
                        <label style={t.label}>
                            Responsibility text
                            <textarea
                                value={loanerDefaultsDraft.responsibility_text}
                                onChange={(event) =>
                                    setLoanerDefaultsDraft((current) =>
                                        current ? { ...current, responsibility_text: event.target.value } : current
                                    )
                                }
                                style={{ ...t.input, marginTop: "4px", minHeight: "74px" }}
                            />
                        </label>
                        <label style={t.label}>
                            Return policy text
                            <textarea
                                value={loanerDefaultsDraft.return_policy_text}
                                onChange={(event) =>
                                    setLoanerDefaultsDraft((current) =>
                                        current ? { ...current, return_policy_text: event.target.value } : current
                                    )
                                }
                                style={{ ...t.input, marginTop: "4px", minHeight: "74px" }}
                            />
                        </label>
                        <label style={t.label}>
                            Signature note text
                            <textarea
                                value={loanerDefaultsDraft.signature_note_text}
                                onChange={(event) =>
                                    setLoanerDefaultsDraft((current) =>
                                        current ? { ...current, signature_note_text: event.target.value } : current
                                    )
                                }
                                style={{ ...t.input, marginTop: "4px", minHeight: "74px" }}
                            />
                        </label>
                        <div>
                            <button type="submit" style={t.primaryBtn}>Save loaner agreement defaults</button>
                        </div>
                    </form>
                ) : (
                    <p style={t.copy}>Loading agreement defaults…</p>
                )}
                {loanerDefaultsError ? <p style={{ ...t.copy, color: "#9b2c2c", marginTop: "12px" }}>{loanerDefaultsError}</p> : null}
                {loanerDefaultsMessage ? <p style={{ ...t.copy, color: "#065f46", marginTop: "12px" }}>{loanerDefaultsMessage}</p> : null}
            </div> : null}

            {showSection("communications") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Notification templates</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    Customize the message text sent to customers for various repair status updates.
                </p>
                {notificationTemplates.length > 0 ? (
                    <form onSubmit={handleSaveNotificationTemplates} style={{ ...t.formStack, gap: "16px" }}>
                        {notificationTemplates.map((template) => (
                            <fieldset key={template.template_key} style={{ border: "1px solid #e0e0e0", borderRadius: "4px", padding: "12px", margin: 0 }}>
                                <legend style={{ fontSize: "0.9rem", fontWeight: "600", padding: "0 4px" }}>
                                    {template.template_name}
                                </legend>
                                <p style={{ ...t.meta, marginTop: "4px" }}>
                                    {template.description}
                                </p>
                                <p style={{ ...t.meta, marginTop: "4px" }}>
                                    Placeholders: {template.placeholders.map((p) => `[${p}]`).join(", ")}
                                </p>
                                <textarea
                                    value={notificationTemplatesDraft[template.template_key] || ""}
                                    onChange={(event) =>
                                        setNotificationTemplatesDraft((current) => ({
                                            ...current,
                                            [template.template_key]: event.target.value,
                                        }))
                                    }
                                    style={{ ...t.input, marginTop: "8px", minHeight: "100px", width: "100%", fontFamily: "monospace", fontSize: "0.85rem" }}
                                />
                            </fieldset>
                        ))}
                        <div>
                            <button type="submit" style={t.primaryBtn}>Save notification templates</button>
                        </div>
                    </form>
                ) : (
                    <p style={t.copy}>Loading notification templates…</p>
                )}
                {notificationTemplatesError ? <p style={{ ...t.copy, color: "#9b2c2c", marginTop: "12px" }}>{notificationTemplatesError}</p> : null}
                {notificationTemplatesMessage ? <p style={{ ...t.copy, color: "#065f46", marginTop: "12px" }}>{notificationTemplatesMessage}</p> : null}
            </div> : null}

            {/* ── Roadmap ── */}
            {showSection("system") ? <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>Roadmap focus</h3>
                <p style={{ ...t.copy, marginBottom: "12px", fontSize: "0.88rem" }}>
                    Planned next improvements for Settings after MVP stabilization.
                </p>
                <div style={{ ...t.formActionsRow, gap: "8px" }}>
                    {["Role permissions", "Audit-focused approvals", "Scheduled backups", "Multi-location templates"].map((item) => (
                        <span key={item} style={roadmapChip}>{item}</span>
                    ))}
                </div>
            </div> : null}
        </section>
    );
}

// ─── styles ───
const panelStyle = t.panel;

const savedChip: React.CSSProperties = {
    display: "inline-block",
    padding: "4px 12px",
    borderRadius: "999px",
    background: "#d1fae5",
    color: "#065f46",
    fontWeight: 700,
    fontSize: "0.82rem",
    border: "1px solid #a7f3d0",
};

const techChip: React.CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    borderRadius: "999px",
    padding: "5px 12px 5px 14px",
    background: "linear-gradient(145deg, #e8f5f2 0%, #d4ece6 100%)",
    color: "#1f4a41",
    fontWeight: 600,
    fontSize: "0.88rem",
    border: "1px solid #b0d9d0",
};

const removeBtnStyle: React.CSSProperties = {
    background: "none",
    border: "none",
    cursor: "pointer",
    color: "#6b7280",
    fontSize: "0.8rem",
    padding: "0",
    fontWeight: 700,
    lineHeight: 1,
};

const constraintChip: React.CSSProperties = {
    display: "inline-block",
    borderRadius: "999px",
    padding: "7px 14px",
    background: "#fff1dd",
    color: "#8a4b00",
    border: "1px solid #f3c481",
    fontWeight: 600,
    fontSize: "0.88rem",
};

const roadmapChip: React.CSSProperties = {
    display: "inline-block",
    borderRadius: "999px",
    padding: "7px 14px",
    background: "#f3f4f6",
    color: "#374151",
    border: "1px solid #d1d5db",
    fontWeight: 500,
    fontSize: "0.88rem",
};

const sectionLabelStyle: React.CSSProperties = {
    fontSize: "0.78rem",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    fontWeight: 800,
    color: "#1b4f45",
};

const statusTileStyle: React.CSSProperties = {
    borderRadius: "12px",
    border: "1px solid rgba(29, 43, 40, 0.12)",
    background: "#ffffff",
    padding: "10px 12px",
    display: "grid",
    gap: "6px",
};

const statusTileLabelStyle: React.CSSProperties = {
    color: "#5a726c",
    fontSize: "0.78rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.06em",
};

const statusTileValueStyle: React.CSSProperties = {
    color: "#173f37",
    fontSize: "1rem",
    fontWeight: 800,
};
