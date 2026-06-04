import { useMemo, useState } from "react";

import {
    createPricingBrand,
    createPricingIssueType,
    createPricingModel,
    createPricingRepairType,
    createPricingRule,
    deletePricingRule,
    fetchPricingCatalog,
    updatePricingBrand,
    updatePricingIssueType,
    updatePricingModel,
    updatePricingRepairType,
    updatePricingRule,
    type PricingBrand,
    type PricingCatalog,
    type PricingIssueType,
    type PricingModel,
    type PricingRepairType,
    type PricingRule,
} from "../api/pricingCatalog";
import { MetricTile, PageHeader, SectionCard } from "../components/PageChrome";
import { useAuth } from "../auth/AuthProvider";
import { canEditPricing } from "../auth/roles";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

const initialRuleForm = {
    brand_id: "",
    model_id: "",
    issue_type_id: "",
    repair_type_id: "",
    standard_price: "",
    estimated_part_cost: "",
    estimated_labor_minutes: "",
    customer_wording: "",
    internal_notes: "",
};

export default function PricingPage() {
    const { user } = useAuth();
    const isReadOnly = !canEditPricing(user);
    const [refreshKey, setRefreshKey] = useState(0);
    const [search, setSearch] = useState("");
    const [showInactive, setShowInactive] = useState(true);

    const [brandName, setBrandName] = useState("");
    const [modelName, setModelName] = useState("");
    const [modelBrandId, setModelBrandId] = useState("");
    const [issueTypeName, setIssueTypeName] = useState("");
    const [repairTypeName, setRepairTypeName] = useState("");
    const [ruleForm, setRuleForm] = useState(initialRuleForm);
    const [editingRuleId, setEditingRuleId] = useState<number | null>(null);

    const [message, setMessage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState<string | null>(null);

    const { data: catalog, error: catalogError } = useAsyncData<PricingCatalog>(() => fetchPricingCatalog(true), [refreshKey]);

    const brands = catalog?.brands ?? [];
    const models = catalog?.models ?? [];
    const issueTypes = catalog?.issue_types ?? [];
    const repairTypes = catalog?.repair_types ?? [];
    const allRules = catalog?.rules ?? [];

    const filteredRules = useMemo(() => {
        const q = search.trim().toLowerCase();
        return allRules.filter((rule) => {
            if (!showInactive && !rule.active) {
                return false;
            }
            if (!q) {
                return true;
            }
            const haystack = [
                rule.brand_name,
                rule.model_name,
                rule.issue_type_name,
                rule.repair_type_name,
                rule.customer_wording ?? "",
                rule.internal_notes ?? "",
            ].join(" ").toLowerCase();
            return haystack.includes(q);
        });
    }, [allRules, search, showInactive]);

    const modelsForSelectedBrand = useMemo(() => {
        if (!ruleForm.brand_id) {
            return models;
        }
        const brandId = Number(ruleForm.brand_id);
        return models.filter((model) => model.brand_id === brandId);
    }, [models, ruleForm.brand_id]);

    async function runAction(action: string, fn: () => Promise<void>) {
        try {
            setBusy(action);
            setError(null);
            setMessage(null);
            await fn();
            setRefreshKey((current) => current + 1);
        } catch (requestError) {
            setError(requestError instanceof Error ? requestError.message : "Request failed");
        } finally {
            setBusy(null);
        }
    }

    function hydrateRuleForm(rule: PricingRule) {
        setEditingRuleId(rule.id);
        setRuleForm({
            brand_id: String(rule.brand_id),
            model_id: String(rule.model_id),
            issue_type_id: String(rule.issue_type_id),
            repair_type_id: String(rule.repair_type_id),
            standard_price: String(rule.standard_price),
            estimated_part_cost: String(rule.estimated_part_cost),
            estimated_labor_minutes: String(rule.estimated_labor_minutes),
            customer_wording: rule.customer_wording ?? "",
            internal_notes: rule.internal_notes ?? "",
        });
    }

    function resetRuleForm() {
        setEditingRuleId(null);
        setRuleForm(initialRuleForm);
    }

    async function handleSubmitRule(event: React.FormEvent) {
        event.preventDefault();
        if (isReadOnly) {
            setError("Your role can view pricing but cannot change catalog data.");
            return;
        }
        const payload = {
            brand_id: Number(ruleForm.brand_id),
            model_id: Number(ruleForm.model_id),
            issue_type_id: Number(ruleForm.issue_type_id),
            repair_type_id: Number(ruleForm.repair_type_id),
            standard_price: Number(ruleForm.standard_price),
            estimated_part_cost: Number(ruleForm.estimated_part_cost || 0),
            estimated_labor_minutes: Number(ruleForm.estimated_labor_minutes || 0),
            customer_wording: ruleForm.customer_wording.trim() || null,
            internal_notes: ruleForm.internal_notes.trim() || null,
        };

        if (Object.values(payload).some((value) => typeof value === "number" && Number.isNaN(value))) {
            setError("Pricing rule fields must use valid numeric values.");
            return;
        }

        if (editingRuleId !== null) {
            await runAction("rule-save", async () => {
                await updatePricingRule(editingRuleId, payload);
                setMessage("Pricing rule updated.");
                resetRuleForm();
            });
            return;
        }

        await runAction("rule-save", async () => {
            await createPricingRule(payload);
            setMessage("Pricing rule created.");
            resetRuleForm();
        });
    }

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Catalog"
                title="Pricing"
                description="Manage brands, models, issue types, repair types, and rule pricing in one place."
                actions={
                    <div style={t.formActionsRow}>
                        <label style={{ ...t.label, fontSize: "0.85rem" }}>
                            <span>Search</span>
                            <input
                                value={search}
                                onChange={(event) => setSearch(event.target.value)}
                                placeholder="Brand, model, issue, notes"
                                style={{ ...t.input, minWidth: 0, width: "min(100%, 240px)" }}
                            />
                        </label>
                        <label style={{ ...t.label, display: "inline-flex", alignItems: "center", gap: "8px", marginTop: "24px" }}>
                            <input
                                type="checkbox"
                                checked={showInactive}
                                onChange={(event) => setShowInactive(event.target.checked)}
                            />
                            Include inactive
                        </label>
                    </div>
                }
            />

            <div style={t.detailGrid}>
                <MetricTile label="Brands" value={String(brands.length)} />
                <MetricTile label="Models" value={String(models.length)} />
                <MetricTile label="Issue Types" value={String(issueTypes.length)} />
                <MetricTile label="Rules" value={String(allRules.length)} hint={`${filteredRules.length} shown`} />
            </div>

            {catalogError ? <div style={t.errorBanner}>{catalogError}</div> : null}
            {error ? <div style={t.errorBanner}>{error}</div> : null}
            {message ? <div style={successStyle}>{message}</div> : null}
            {isReadOnly ? (
                <div style={{ ...successStyle, borderColor: "#cbd5e1", background: "#f8fafc", color: "#334155" }}>
                    Read-only mode: only owner/admin can edit pricing configuration.
                </div>
            ) : null}

            <SectionCard title="Add Catalog Values" description="Quick-add dimensions for pricing rules." tone="soft">
                <div style={t.fieldGridTwo}>
                    <form
                        onSubmit={(event) => {
                            event.preventDefault();
                            if (isReadOnly) {
                                setError("Your role can view pricing but cannot add catalog values.");
                                return;
                            }
                            if (!brandName.trim()) {
                                setError("Brand name is required.");
                                return;
                            }
                            void runAction("brand-create", async () => {
                                await createPricingBrand({ name: brandName.trim() });
                                setBrandName("");
                                setMessage("Brand created.");
                            });
                        }}
                        style={t.formStack}
                    >
                        <strong>Brand</strong>
                        <input value={brandName} onChange={(event) => setBrandName(event.target.value)} style={t.input} placeholder="Kyocera" disabled={isReadOnly} />
                        <button style={t.primaryBtn} type="submit" disabled={isReadOnly || busy === "brand-create"}>Add brand</button>
                    </form>

                    <form
                        onSubmit={(event) => {
                            event.preventDefault();
                            if (isReadOnly) {
                                setError("Your role can view pricing but cannot add catalog values.");
                                return;
                            }
                            if (!modelName.trim() || !modelBrandId) {
                                setError("Select a brand and enter model name.");
                                return;
                            }
                            void runAction("model-create", async () => {
                                await createPricingModel({ brand_id: Number(modelBrandId), name: modelName.trim() });
                                setModelName("");
                                setMessage("Model created.");
                            });
                        }}
                        style={t.formStack}
                    >
                        <strong>Model</strong>
                        <select value={modelBrandId} onChange={(event) => setModelBrandId(event.target.value)} style={t.input} disabled={isReadOnly}>
                            <option value="">Select brand</option>
                            {brands.map((brand) => (
                                <option key={brand.id} value={brand.id}>{brand.name}</option>
                            ))}
                        </select>
                        <input value={modelName} onChange={(event) => setModelName(event.target.value)} style={t.input} placeholder="E4810" disabled={isReadOnly} />
                        <button style={t.primaryBtn} type="submit" disabled={isReadOnly || busy === "model-create"}>Add model</button>
                    </form>

                    <form
                        onSubmit={(event) => {
                            event.preventDefault();
                            if (isReadOnly) {
                                setError("Your role can view pricing but cannot add catalog values.");
                                return;
                            }
                            if (!issueTypeName.trim()) {
                                setError("Issue type name is required.");
                                return;
                            }
                            void runAction("issue-create", async () => {
                                await createPricingIssueType({ name: issueTypeName.trim() });
                                setIssueTypeName("");
                                setMessage("Issue type created.");
                            });
                        }}
                        style={t.formStack}
                    >
                        <strong>Issue Type</strong>
                        <input value={issueTypeName} onChange={(event) => setIssueTypeName(event.target.value)} style={t.input} placeholder="Screen/LCD" disabled={isReadOnly} />
                        <button style={t.primaryBtn} type="submit" disabled={isReadOnly || busy === "issue-create"}>Add issue type</button>
                    </form>

                    <form
                        onSubmit={(event) => {
                            event.preventDefault();
                            if (isReadOnly) {
                                setError("Your role can view pricing but cannot add catalog values.");
                                return;
                            }
                            if (!repairTypeName.trim()) {
                                setError("Repair type name is required.");
                                return;
                            }
                            void runAction("repair-create", async () => {
                                await createPricingRepairType({ name: repairTypeName.trim() });
                                setRepairTypeName("");
                                setMessage("Repair type created.");
                            });
                        }}
                        style={t.formStack}
                    >
                        <strong>Repair Type</strong>
                        <input value={repairTypeName} onChange={(event) => setRepairTypeName(event.target.value)} style={t.input} placeholder="Estimate" disabled={isReadOnly} />
                        <button style={t.primaryBtn} type="submit" disabled={isReadOnly || busy === "repair-create"}>Add repair type</button>
                    </form>
                </div>
            </SectionCard>

            <SectionCard title={editingRuleId ? `Edit Rule #${editingRuleId}` : "Create Pricing Rule"} tone="accent">
                <form onSubmit={(event) => void handleSubmitRule(event)} style={t.formStack}>
                    <div style={t.fieldGridTwo}>
                        <label style={t.label}>
                            Brand
                            <select
                                value={ruleForm.brand_id}
                                onChange={(event) => setRuleForm((current) => ({ ...current, brand_id: event.target.value, model_id: "" }))}
                                style={t.input}
                                disabled={isReadOnly}
                                required
                            >
                                <option value="">Select brand</option>
                                {brands.filter((brand) => brand.active || showInactive).map((brand) => (
                                    <option key={brand.id} value={brand.id}>{brand.name}</option>
                                ))}
                            </select>
                        </label>
                        <label style={t.label}>
                            Model
                            <select
                                value={ruleForm.model_id}
                                onChange={(event) => setRuleForm((current) => ({ ...current, model_id: event.target.value }))}
                                style={t.input}
                                disabled={isReadOnly}
                                required
                            >
                                <option value="">Select model</option>
                                {modelsForSelectedBrand.filter((model) => model.active || showInactive).map((model) => (
                                    <option key={model.id} value={model.id}>{model.brand_name} {model.name}</option>
                                ))}
                            </select>
                        </label>
                        <label style={t.label}>
                            Issue type
                            <select
                                value={ruleForm.issue_type_id}
                                onChange={(event) => setRuleForm((current) => ({ ...current, issue_type_id: event.target.value }))}
                                style={t.input}
                                disabled={isReadOnly}
                                required
                            >
                                <option value="">Select issue type</option>
                                {issueTypes.filter((item) => item.active || showInactive).map((item) => (
                                    <option key={item.id} value={item.id}>{item.name}</option>
                                ))}
                            </select>
                        </label>
                        <label style={t.label}>
                            Repair type
                            <select
                                value={ruleForm.repair_type_id}
                                onChange={(event) => setRuleForm((current) => ({ ...current, repair_type_id: event.target.value }))}
                                style={t.input}
                                disabled={isReadOnly}
                                required
                            >
                                <option value="">Select repair type</option>
                                {repairTypes.filter((item) => item.active || showInactive).map((item) => (
                                    <option key={item.id} value={item.id}>{item.name}</option>
                                ))}
                            </select>
                        </label>
                        <label style={t.label}>
                            Standard price ($)
                            <input type="number" min="0" step="1" value={ruleForm.standard_price} onChange={(event) => setRuleForm((current) => ({ ...current, standard_price: event.target.value }))} style={t.input} disabled={isReadOnly} required />
                        </label>
                        <label style={t.label}>
                            Estimated part cost ($)
                            <input type="number" min="0" step="1" value={ruleForm.estimated_part_cost} onChange={(event) => setRuleForm((current) => ({ ...current, estimated_part_cost: event.target.value }))} style={t.input} disabled={isReadOnly} />
                        </label>
                        <label style={t.label}>
                            Estimated labor minutes
                            <input type="number" min="0" step="5" value={ruleForm.estimated_labor_minutes} onChange={(event) => setRuleForm((current) => ({ ...current, estimated_labor_minutes: event.target.value }))} style={t.input} disabled={isReadOnly} />
                        </label>
                        <label style={t.label}>
                            Customer wording
                            <input value={ruleForm.customer_wording} onChange={(event) => setRuleForm((current) => ({ ...current, customer_wording: event.target.value }))} style={t.input} placeholder="What front desk says to customer" disabled={isReadOnly} />
                        </label>
                    </div>

                    <label style={t.label}>
                        Internal notes
                        <textarea value={ruleForm.internal_notes} onChange={(event) => setRuleForm((current) => ({ ...current, internal_notes: event.target.value }))} style={{ ...t.input, minHeight: "80px" }} disabled={isReadOnly} />
                    </label>

                    <div style={t.formActionsRow}>
                        <button style={t.primaryBtn} type="submit" disabled={isReadOnly || busy === "rule-save"}>{editingRuleId ? "Update rule" : "Create rule"}</button>
                        {editingRuleId ? (
                            <button type="button" style={t.secondaryBtn} onClick={resetRuleForm} disabled={isReadOnly}>Cancel edit</button>
                        ) : null}
                    </div>
                </form>
            </SectionCard>

            <SectionCard title="Rule Catalog" description="Compact view with quick edit, activate/deactivate, and delete.">
                <div style={{ overflowX: "auto" }}>
                    <table style={t.tableShell}>
                        <thead>
                            <tr style={{ background: "#173f37", color: "#f4f8f2" }}>
                                <th style={t.tableHeaderCell}>Brand</th>
                                <th style={t.tableHeaderCell}>Model</th>
                                <th style={t.tableHeaderCell}>Issue</th>
                                <th style={t.tableHeaderCell}>Type</th>
                                <th style={t.tableHeaderCell}>Price</th>
                                <th style={t.tableHeaderCell}>Part</th>
                                <th style={t.tableHeaderCell}>Labor</th>
                                <th style={t.tableHeaderCell}>Status</th>
                                <th style={t.tableHeaderCell}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredRules.map((rule) => (
                                <tr key={rule.id} style={{ borderBottom: "1px solid rgba(0, 0, 0, 0.06)" }}>
                                    <td style={t.tableCell}>{rule.brand_name}</td>
                                    <td style={t.tableCell}>{rule.model_name}</td>
                                    <td style={t.tableCell}>{rule.issue_type_name}</td>
                                    <td style={t.tableCell}>{rule.repair_type_name}</td>
                                    <td style={t.tableCell}>${rule.standard_price.toFixed(2)}</td>
                                    <td style={t.tableCell}>${rule.estimated_part_cost.toFixed(2)}</td>
                                    <td style={t.tableCell}>{rule.estimated_labor_minutes}m</td>
                                    <td style={t.tableCell}>{rule.active ? "Active" : "Inactive"}</td>
                                    <td style={t.tableCell}>
                                        <div style={t.formActionsRow}>
                                            <button type="button" style={t.miniBtn} onClick={() => hydrateRuleForm(rule)} disabled={isReadOnly}>Edit</button>
                                            <button
                                                type="button"
                                                style={t.miniBtn}
                                                disabled={isReadOnly}
                                                onClick={() => {
                                                    void runAction("rule-toggle", async () => {
                                                        await updatePricingRule(rule.id, { active: !rule.active });
                                                        setMessage(`Rule ${rule.id} ${rule.active ? "deactivated" : "activated"}.`);
                                                    });
                                                }}
                                            >
                                                {rule.active ? "Deactivate" : "Activate"}
                                            </button>
                                            <button
                                                type="button"
                                                style={{ ...t.miniBtn, borderColor: "#c67d74", color: "#8f2f24" }}
                                                disabled={isReadOnly}
                                                onClick={() => {
                                                    void runAction("rule-delete", async () => {
                                                        await deletePricingRule(rule.id);
                                                        setMessage(`Rule ${rule.id} deleted.`);
                                                        if (editingRuleId === rule.id) {
                                                            resetRuleForm();
                                                        }
                                                    });
                                                }}
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
                {filteredRules.length === 0 ? <p style={t.copy}>No pricing rules match the current filter.</p> : null}
            </SectionCard>

            <SectionCard title="Dimensions" description="Toggle active/inactive for brands, models, issue types, and repair types." compact>
                <div style={t.detailGrid}>
                    <DimensionList
                        title="Brands"
                        items={brands}
                        renderLabel={(item) => item.name}
                        onToggle={(item) => updatePricingBrand(item.id, { active: !item.active })}
                        onRename={(item, nextName) => updatePricingBrand(item.id, { name: nextName })}
                        readOnly={isReadOnly}
                        runAction={runAction}
                    />
                    <DimensionList
                        title="Models"
                        items={models}
                        renderLabel={(item) => `${item.brand_name} ${item.name}`}
                        onToggle={(item) => updatePricingModel(item.id, { active: !item.active })}
                        onRename={(item, nextName) => updatePricingModel(item.id, { name: nextName })}
                        readOnly={isReadOnly}
                        runAction={runAction}
                    />
                    <DimensionList
                        title="Issue Types"
                        items={issueTypes}
                        renderLabel={(item) => item.name}
                        onToggle={(item) => updatePricingIssueType(item.id, { active: !item.active })}
                        onRename={(item, nextName) => updatePricingIssueType(item.id, { name: nextName })}
                        readOnly={isReadOnly}
                        runAction={runAction}
                    />
                    <DimensionList
                        title="Repair Types"
                        items={repairTypes}
                        renderLabel={(item) => item.name}
                        onToggle={(item) => updatePricingRepairType(item.id, { active: !item.active })}
                        onRename={(item, nextName) => updatePricingRepairType(item.id, { name: nextName })}
                        readOnly={isReadOnly}
                        runAction={runAction}
                    />
                </div>
            </SectionCard>
        </section>
    );
}

function DimensionList<T extends { id: number; active: boolean }>({
    title,
    items,
    renderLabel,
    onToggle,
    onRename,
    readOnly,
    runAction,
}: {
    title: string;
    items: T[];
    renderLabel: (item: T) => string;
    onToggle: (item: T) => Promise<unknown>;
    onRename: (item: T, nextName: string) => Promise<unknown>;
    readOnly: boolean;
    runAction: (action: string, fn: () => Promise<void>) => Promise<void>;
}) {
    const [draftById, setDraftById] = useState<Record<number, string>>({});

    return (
        <div style={t.subCard}>
            <strong>{title}</strong>
            <div style={{ ...t.formStack, gap: "8px", marginTop: "10px" }}>
                {items.map((item) => {
                    const label = renderLabel(item);
                    const draft = draftById[item.id] ?? label;
                    return (
                        <div key={item.id} style={{ ...t.formStack, gap: "6px", borderBottom: "1px solid rgba(0,0,0,0.06)", paddingBottom: "8px" }}>
                            <input
                                value={draft}
                                onChange={(event) => {
                                    const value = event.target.value;
                                    setDraftById((current) => ({ ...current, [item.id]: value }));
                                }}
                                style={t.input}
                                disabled={readOnly}
                            />
                            <div style={t.formActionsRow}>
                                <button
                                    type="button"
                                    style={t.miniBtn}
                                    disabled={readOnly}
                                    onClick={() => {
                                        const nextName = draft.trim();
                                        if (!nextName || nextName === label) {
                                            return;
                                        }
                                        void runAction("dimension-rename", async () => {
                                            await onRename(item, nextName);
                                        });
                                    }}
                                >
                                    Rename
                                </button>
                                <button
                                    type="button"
                                    style={t.miniBtn}
                                    disabled={readOnly}
                                    onClick={() => {
                                        void runAction("dimension-toggle", async () => {
                                            await onToggle(item);
                                        });
                                    }}
                                >
                                    {item.active ? "Deactivate" : "Activate"}
                                </button>
                                <span style={statusChipStyle(item.active)}>{item.active ? "Active" : "Inactive"}</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function statusChipStyle(active: boolean) {
    return {
        borderRadius: "999px",
        padding: "3px 9px",
        fontSize: "0.76rem",
        fontWeight: 700,
        color: active ? "#245544" : "#7a3f38",
        background: active ? "#e6f5ee" : "#f9e9e6",
        border: active ? "1px solid #bbdfcf" : "1px solid #e4beb7",
    };
}

const successStyle = {
    padding: "10px 12px",
    borderRadius: "12px",
    border: "1px solid #bdd9c6",
    background: "#edf8f1",
    color: "#1d5d3d",
};
