import { apiFetch } from "./client";

export type MarketAllowlistEntry = {
    id: number;
    phone_number: string;
    label: string | null;
    enabled: number;
    created_at: string;
    updated_at: string;
};

export type MarketInviteRequest = {
    id: number;
    phone_number: string;
    requested_label: string | null;
    message_text: string | null;
    status: "pending" | "approved" | "denied";
    created_at: string;
    updated_at: string;
};

export type MarketFeedbackEntry = {
    id: number;
    phone_number: string;
    feedback_text: string;
    source: string;
    created_at: string;
};

async function expectJson<T>(response: Response, fallbackError: string): Promise<T> {
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? fallbackError);
    }
    return response.json() as Promise<T>;
}

export async function fetchMarketAllowlist(): Promise<MarketAllowlistEntry[]> {
    const response = await apiFetch("/api/market-updates/admin/allowlist");
    return expectJson<MarketAllowlistEntry[]>(response, "Could not load allowlist");
}

export async function upsertMarketAllowlist(payload: {
    phone_number: string;
    label?: string;
    enabled?: boolean;
}): Promise<MarketAllowlistEntry> {
    const response = await apiFetch("/api/market-updates/admin/allowlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });
    return expectJson<MarketAllowlistEntry>(response, "Could not save allowlist entry");
}

export async function disableMarketAllowlist(phoneNumber: string): Promise<{ removed: boolean }> {
    const response = await apiFetch(`/api/market-updates/admin/allowlist/${encodeURIComponent(phoneNumber)}`, {
        method: "DELETE",
    });
    return expectJson<{ removed: boolean }>(response, "Could not disable allowlist entry");
}

export async function fetchMarketInviteRequests(status: string = "pending"): Promise<MarketInviteRequest[]> {
    const query = new URLSearchParams({ status }).toString();
    const response = await apiFetch(`/api/market-updates/admin/invite-requests?${query}`);
    return expectJson<MarketInviteRequest[]>(response, "Could not load invite requests");
}

export async function approveMarketInviteRequest(requestId: number): Promise<MarketInviteRequest> {
    const response = await apiFetch(`/api/market-updates/admin/invite-requests/${requestId}/approve`, {
        method: "POST",
    });
    return expectJson<MarketInviteRequest>(response, "Could not approve invite request");
}

export async function denyMarketInviteRequest(requestId: number): Promise<MarketInviteRequest> {
    const response = await apiFetch(`/api/market-updates/admin/invite-requests/${requestId}/deny`, {
        method: "POST",
    });
    return expectJson<MarketInviteRequest>(response, "Could not deny invite request");
}

export async function fetchMarketFeedback(limit: number = 200): Promise<MarketFeedbackEntry[]> {
    const query = new URLSearchParams({ limit: String(limit) }).toString();
    const response = await apiFetch(`/api/market-updates/admin/feedback?${query}`);
    return expectJson<MarketFeedbackEntry[]>(response, "Could not load feedback entries");
}
