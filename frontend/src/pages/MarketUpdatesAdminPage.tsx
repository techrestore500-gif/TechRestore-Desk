import { useMemo, useState } from "react";

import {
    approveMarketInviteRequest,
    denyMarketInviteRequest,
    disableMarketAllowlist,
    fetchMarketAllowlist,
    fetchMarketFeedback,
    fetchMarketInviteRequests,
    upsertMarketAllowlist,
    type MarketAllowlistEntry,
    type MarketFeedbackEntry,
    type MarketInviteRequest,
} from "../api/marketUpdatesAdmin";
import { InlineState, PageHeader, SectionCard } from "../components/PageChrome";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

function prettyDate(value: string | null | undefined): string {
    if (!value) return "n/a";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

export default function MarketUpdatesAdminPage() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [statusMessage, setStatusMessage] = useState<string | null>(null);
    const [statusError, setStatusError] = useState<string | null>(null);
    const [phoneNumber, setPhoneNumber] = useState("");
    const [label, setLabel] = useState("");
    const [requestFilter, setRequestFilter] = useState<"pending" | "approved" | "denied">("pending");

    const allowlistState = useAsyncData<MarketAllowlistEntry[]>(() => fetchMarketAllowlist(), [refreshKey]);
    const inviteState = useAsyncData<MarketInviteRequest[]>(() => fetchMarketInviteRequests(requestFilter), [refreshKey, requestFilter]);
    const feedbackState = useAsyncData<MarketFeedbackEntry[]>(() => fetchMarketFeedback(200), [refreshKey]);

    const activeAllowlistCount = useMemo(
        () => (allowlistState.data ?? []).filter((entry) => Number(entry.enabled) === 1).length,
        [allowlistState.data]
    );

    async function handleAddAllowlist(e: React.FormEvent) {
        e.preventDefault();
        setStatusError(null);
        setStatusMessage(null);
        try {
            await upsertMarketAllowlist({
                phone_number: phoneNumber,
                label: label.trim() || undefined,
                enabled: true,
            });
            setStatusMessage("Allowlist entry saved.");
            setPhoneNumber("");
            setLabel("");
            setRefreshKey((v) => v + 1);
        } catch (error) {
            setStatusError(error instanceof Error ? error.message : "Could not save allowlist entry");
        }
    }

    async function handleDisable(phone: string) {
        setStatusError(null);
        setStatusMessage(null);
        try {
            await disableMarketAllowlist(phone);
            setStatusMessage("Allowlist entry disabled.");
            setRefreshKey((v) => v + 1);
        } catch (error) {
            setStatusError(error instanceof Error ? error.message : "Could not disable allowlist entry");
        }
    }

    async function handleApproveRequest(requestId: number) {
        setStatusError(null);
        setStatusMessage(null);
        try {
            await approveMarketInviteRequest(requestId);
            setStatusMessage("Invite request approved and number added to allowlist.");
            setRefreshKey((v) => v + 1);
        } catch (error) {
            setStatusError(error instanceof Error ? error.message : "Could not approve invite request");
        }
    }

    async function handleDenyRequest(requestId: number) {
        setStatusError(null);
        setStatusMessage(null);
        try {
            await denyMarketInviteRequest(requestId);
            setStatusMessage("Invite request denied.");
            setRefreshKey((v) => v + 1);
        } catch (error) {
            setStatusError(error instanceof Error ? error.message : "Could not deny invite request");
        }
    }

    return (
        <div style={t.pageWrap}>
            <PageHeader
                kicker="Market SMS"
                title="Market Updates Admin"
                description="Manage allowed numbers, review invite requests, and monitor submitted feedback."
            />

            {statusMessage ? <InlineState tone="success">{statusMessage}</InlineState> : null}
            {statusError ? <InlineState tone="error">{statusError}</InlineState> : null}

            <SectionCard title="Allowlist" description={`Active numbers: ${activeAllowlistCount}`} tone="soft">
                <form style={t.fieldGridTwo} onSubmit={handleAddAllowlist}>
                    <label style={t.label}>
                        Phone number
                        <input
                            style={t.input}
                            value={phoneNumber}
                            onChange={(event) => setPhoneNumber(event.target.value)}
                            placeholder="+15551234567"
                            required
                        />
                    </label>
                    <label style={t.label}>
                        Label (optional)
                        <input
                            style={t.input}
                            value={label}
                            onChange={(event) => setLabel(event.target.value)}
                            placeholder="VIP client"
                        />
                    </label>
                    <div style={t.formActionsRow}>
                        <button type="submit" style={t.primaryBtn}>Add to allowlist</button>
                        <button type="button" style={t.secondaryBtn} onClick={() => setRefreshKey((v) => v + 1)}>Refresh</button>
                    </div>
                </form>

                {allowlistState.loading ? <InlineState tone="info">Loading allowlist...</InlineState> : null}
                {allowlistState.error ? <InlineState tone="error">{allowlistState.error}</InlineState> : null}

                <div style={{ display: "grid", gap: "8px" }}>
                    {(allowlistState.data ?? []).map((entry) => (
                        <div key={entry.id} style={t.subCard}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: "12px", flexWrap: "wrap" }}>
                                <div>
                                    <div><strong>{entry.phone_number}</strong> {entry.label ? `- ${entry.label}` : ""}</div>
                                    <div style={t.meta}>Status: {Number(entry.enabled) === 1 ? "active" : "disabled"} | Updated: {prettyDate(entry.updated_at)}</div>
                                </div>
                                {Number(entry.enabled) === 1 ? (
                                    <button style={t.secondaryBtn} onClick={() => handleDisable(entry.phone_number)}>
                                        Disable
                                    </button>
                                ) : null}
                            </div>
                        </div>
                    ))}
                </div>
            </SectionCard>

            <SectionCard title="Invite Requests" description="Approve or deny SMS access requests." tone="soft">
                <div style={t.formActionsRow}>
                    <button
                        style={requestFilter === "pending" ? t.primaryBtn : t.secondaryBtn}
                        onClick={() => setRequestFilter("pending")}
                        type="button"
                    >
                        Pending
                    </button>
                    <button
                        style={requestFilter === "approved" ? t.primaryBtn : t.secondaryBtn}
                        onClick={() => setRequestFilter("approved")}
                        type="button"
                    >
                        Approved
                    </button>
                    <button
                        style={requestFilter === "denied" ? t.primaryBtn : t.secondaryBtn}
                        onClick={() => setRequestFilter("denied")}
                        type="button"
                    >
                        Denied
                    </button>
                </div>

                {inviteState.loading ? <InlineState tone="info">Loading invite requests...</InlineState> : null}
                {inviteState.error ? <InlineState tone="error">{inviteState.error}</InlineState> : null}

                <div style={{ display: "grid", gap: "8px" }}>
                    {(inviteState.data ?? []).map((request) => (
                        <div key={request.id} style={t.subCard}>
                            <div style={{ display: "grid", gap: "6px" }}>
                                <div><strong>{request.phone_number}</strong> {request.requested_label ? `- ${request.requested_label}` : ""}</div>
                                <div style={t.meta}>Status: {request.status} | Updated: {prettyDate(request.updated_at)}</div>
                                {request.message_text ? <div style={t.copy}>{request.message_text}</div> : null}
                                {request.status === "pending" ? (
                                    <div style={t.formActionsRow}>
                                        <button style={t.primaryBtn} onClick={() => handleApproveRequest(request.id)} type="button">Approve</button>
                                        <button style={t.secondaryBtn} onClick={() => handleDenyRequest(request.id)} type="button">Deny</button>
                                    </div>
                                ) : null}
                            </div>
                        </div>
                    ))}
                    {(inviteState.data ?? []).length === 0 ? <InlineState tone="info">No {requestFilter} invite requests.</InlineState> : null}
                </div>
            </SectionCard>

            <SectionCard title="Feedback Feed" description="Recent FEEDBACK submissions and portal entries." tone="soft">
                {feedbackState.loading ? <InlineState tone="info">Loading feedback...</InlineState> : null}
                {feedbackState.error ? <InlineState tone="error">{feedbackState.error}</InlineState> : null}

                <div style={{ display: "grid", gap: "8px" }}>
                    {(feedbackState.data ?? []).map((entry) => (
                        <div key={entry.id} style={t.subCard}>
                            <div style={{ display: "grid", gap: "4px" }}>
                                <div><strong>{entry.source}</strong> {entry.phone_number ? `- ${entry.phone_number}` : ""}</div>
                                <div style={t.meta}>{prettyDate(entry.created_at)}</div>
                                <div style={t.copy}>{entry.feedback_text}</div>
                            </div>
                        </div>
                    ))}
                    {(feedbackState.data ?? []).length === 0 ? <InlineState tone="info">No feedback entries yet.</InlineState> : null}
                </div>
            </SectionCard>
        </div>
    );
}
