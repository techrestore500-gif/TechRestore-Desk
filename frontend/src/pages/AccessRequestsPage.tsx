import { useState } from "react";

import { approveAccessRequest, denyAccessRequest, fetchAccessRequests, type AccessRequest, type AuthRole } from "../api/auth";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

const APPROVAL_ROLES: AuthRole[] = ["viewer", "front_desk", "technician", "admin", "owner"];

export default function AccessRequestsPage() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [actionError, setActionError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);
    const [busyUserId, setBusyUserId] = useState<number | null>(null);
    const [selectedRoles, setSelectedRoles] = useState<Record<number, AuthRole>>({});

    const { data: requests = [], error } = useAsyncData<AccessRequest[]>(() => fetchAccessRequests(), [refreshKey]);

    function roleForRequest(request: AccessRequest): AuthRole {
        return selectedRoles[request.id] ?? "front_desk";
    }

    async function handleApprove(request: AccessRequest) {
        const selectedRole = roleForRequest(request);
        setBusyUserId(request.id);
        setActionError(null);
        setActionMessage(null);
        try {
            await approveAccessRequest(request.id, selectedRole);
            setActionMessage(`Approved ${request.email} as ${selectedRole}.`);
            setRefreshKey((current) => current + 1);
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not approve request");
        } finally {
            setBusyUserId(null);
        }
    }

    async function handleDeny(request: AccessRequest) {
        setBusyUserId(request.id);
        setActionError(null);
        setActionMessage(null);
        try {
            await denyAccessRequest(request.id);
            setActionMessage(`Denied access request for ${request.email}.`);
            setRefreshKey((current) => current + 1);
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not deny request");
        } finally {
            setBusyUserId(null);
        }
    }

    return (
        <section style={t.pageWrap}>
            <div>
                <h2 style={{ margin: 0 }}>Access Requests</h2>
                <p style={{ ...t.copy, marginTop: "6px" }}>Review pending signups and assign roles during approval.</p>
            </div>

            {error ? <div style={t.errorBanner}>{error}</div> : null}
            {actionError ? <div style={t.errorBanner}>{actionError}</div> : null}
            {actionMessage ? (
                <div style={{ ...t.subCard, borderColor: "#34d399", background: "#ecfdf5", color: "#065f46" }}>
                    {actionMessage}
                </div>
            ) : null}

            {requests.length === 0 ? (
                <div style={t.panel}>No pending access requests.</div>
            ) : (
                <div style={{ ...t.panel, display: "grid", gap: "10px" }}>
                    {requests.map((request) => (
                        <article key={request.id} style={{ ...t.subCard, display: "grid", gap: "8px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", flexWrap: "wrap" }}>
                                <strong>{request.name}</strong>
                                <span style={t.meta}>{new Date(request.created_at).toLocaleString()}</span>
                            </div>
                            <div style={t.meta}>{request.email}</div>
                            <div style={t.meta}>Status: {request.status}</div>
                            <div style={{ ...t.formActionsRow, gap: "8px", flexWrap: "wrap" }}>
                                <select
                                    value={roleForRequest(request)}
                                    onChange={(event) =>
                                        setSelectedRoles((current) => ({
                                            ...current,
                                            [request.id]: event.target.value as AuthRole,
                                        }))
                                    }
                                    style={{ ...t.input, width: "180px" }}
                                    disabled={busyUserId === request.id}
                                >
                                    {APPROVAL_ROLES.map((role) => (
                                        <option key={role} value={role}>
                                            {role}
                                        </option>
                                    ))}
                                </select>
                                <button
                                    type="button"
                                    style={t.primaryBtn}
                                    onClick={() => handleApprove(request)}
                                    disabled={busyUserId === request.id}
                                >
                                    Approve
                                </button>
                                <button
                                    type="button"
                                    style={t.secondaryBtn}
                                    onClick={() => handleDeny(request)}
                                    disabled={busyUserId === request.id}
                                >
                                    Deny
                                </button>
                            </div>
                        </article>
                    ))}
                </div>
            )}
        </section>
    );
}
