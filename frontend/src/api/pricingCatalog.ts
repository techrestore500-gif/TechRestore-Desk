import { apiFetch, getJson } from "./client";

export type PricingBrand = {
    id: number;
    name: string;
    active: boolean;
    created_at: string;
    updated_at: string;
};

export type PricingModel = {
    id: number;
    brand_id: number;
    brand_name: string;
    name: string;
    active: boolean;
    created_at: string;
    updated_at: string;
};

export type PricingIssueType = {
    id: number;
    name: string;
    active: boolean;
    created_at: string;
    updated_at: string;
};

export type PricingRepairType = {
    id: number;
    name: string;
    active: boolean;
    created_at: string;
    updated_at: string;
};

export type PricingRule = {
    id: number;
    brand_id: number;
    brand_name: string;
    model_id: number;
    model_name: string;
    issue_type_id: number;
    issue_type_name: string;
    repair_type_id: number;
    repair_type_name: string;
    standard_price: number;
    estimated_part_cost: number;
    estimated_labor_minutes: number;
    active: boolean;
    customer_wording: string | null;
    internal_notes: string | null;
    created_at: string;
    updated_at: string;
};

export type PricingCatalog = {
    brands: PricingBrand[];
    models: PricingModel[];
    issue_types: PricingIssueType[];
    repair_types: PricingRepairType[];
    rules: PricingRule[];
};

export type PricingRuleSuggestion = {
    match_found: boolean;
    rule: PricingRule | null;
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

async function deleteRequest(path: string): Promise<void> {
    const response = await apiFetch(path, { method: "DELETE" });
    if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}));
        throw new Error(errorBody.detail ?? `Request failed: ${response.status}`);
    }
}

export async function fetchPricingCatalog(includeInactive = true): Promise<PricingCatalog> {
    const query = includeInactive ? "?include_inactive=true" : "?include_inactive=false";
    return getJson<PricingCatalog>(`/api/pricing/catalog${query}`);
}

export async function createPricingBrand(payload: { name: string }): Promise<PricingBrand> {
    return postJson<PricingBrand>("/api/pricing/catalog/brands", payload);
}

export async function updatePricingBrand(brandId: number, payload: { name?: string; active?: boolean }): Promise<PricingBrand> {
    return patchJson<PricingBrand>(`/api/pricing/catalog/brands/${brandId}`, payload);
}

export async function createPricingModel(payload: { brand_id: number; name: string }): Promise<PricingModel> {
    return postJson<PricingModel>("/api/pricing/catalog/models", payload);
}

export async function updatePricingModel(modelId: number, payload: { brand_id?: number; name?: string; active?: boolean }): Promise<PricingModel> {
    return patchJson<PricingModel>(`/api/pricing/catalog/models/${modelId}`, payload);
}

export async function createPricingIssueType(payload: { name: string }): Promise<PricingIssueType> {
    return postJson<PricingIssueType>("/api/pricing/catalog/issue-types", payload);
}

export async function updatePricingIssueType(issueTypeId: number, payload: { name?: string; active?: boolean }): Promise<PricingIssueType> {
    return patchJson<PricingIssueType>(`/api/pricing/catalog/issue-types/${issueTypeId}`, payload);
}

export async function createPricingRepairType(payload: { name: string }): Promise<PricingRepairType> {
    return postJson<PricingRepairType>("/api/pricing/catalog/repair-types", payload);
}

export async function updatePricingRepairType(repairTypeId: number, payload: { name?: string; active?: boolean }): Promise<PricingRepairType> {
    return patchJson<PricingRepairType>(`/api/pricing/catalog/repair-types/${repairTypeId}`, payload);
}

export async function createPricingRule(payload: {
    brand_id: number;
    model_id: number;
    issue_type_id: number;
    repair_type_id: number;
    standard_price: number;
    estimated_part_cost: number;
    estimated_labor_minutes: number;
    customer_wording?: string | null;
    internal_notes?: string | null;
    active?: boolean;
}): Promise<PricingRule> {
    return postJson<PricingRule>("/api/pricing/catalog/rules", payload);
}

export async function updatePricingRule(ruleId: number, payload: {
    brand_id?: number;
    model_id?: number;
    issue_type_id?: number;
    repair_type_id?: number;
    standard_price?: number;
    estimated_part_cost?: number;
    estimated_labor_minutes?: number;
    customer_wording?: string | null;
    internal_notes?: string | null;
    active?: boolean;
}): Promise<PricingRule> {
    return patchJson<PricingRule>(`/api/pricing/catalog/rules/${ruleId}`, payload);
}

export async function deletePricingRule(ruleId: number): Promise<void> {
    return deleteRequest(`/api/pricing/catalog/rules/${ruleId}`);
}

export async function fetchPricingCatalogSuggestion(brand: string, model: string, issueType: string): Promise<PricingRuleSuggestion> {
    const params = new URLSearchParams({ brand, model, issue_type: issueType });
    return getJson<PricingRuleSuggestion>(`/api/pricing/catalog/suggest?${params.toString()}`);
}
