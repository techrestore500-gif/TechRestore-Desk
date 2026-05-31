import { FormEvent, useState } from "react";

import { createInvite, fetchInvites, resendInvite, revokeInvite, type AuthInvite, type AuthRole } from "../api/auth";
import { useAsyncData } from "../hooks/useAsyncData";
import * as t from "../styles/theme";

const INVITE_ROLES: AuthRole[] = ["viewer", "front_desk", "technician", "admin", "owner"];

export default function AccessRequestsPage() {
    const [refreshKey, setRefreshKey] = useState(0);
    const [actionError, setActionError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);
    const [busyInviteId, setBusyInviteId] = useState<number | null>(null);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteName, setInviteName] = useState("");
    const [inviteRole, setInviteRole] = useState<AuthRole>("front_desk");
    const [creatingInvite, setCreatingInvite] = useState(false);
    const [statusFilter, setStatusFilter] = useState<"all" | "active" | "pending" | "expired">("all");

    const { data: invites = [], error } = useAsyncData<AuthInvite[]>(() => fetchInvites(), [refreshKey]);

    const filteredInvites = invites.filter((invite) => {
        if (statusFilter === "all") {
            return true;
        }
        if (statusFilter === "active") {
            return invite.status === "accepted";
        }
        if (statusFilter === "pending") {
            return invite.status === "pending";
        }
        return invite.status === "expired";
    });

    async function handleCreateInvite(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!inviteEmail.trim()) {
            setActionError("Invite email is required.");
            return;
        }

        setCreatingInvite(true);
        setActionError(null);
        setActionMessage(null);
        try {
            const invite = await createInvite(inviteEmail, inviteRole, inviteName || undefined);
            setActionMessage(`Invite sent to ${invite.email}.`);
            setInviteEmail("");
            setInviteName("");
            setInviteRole("front_desk");
            setRefreshKey((current) => current + 1);
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not create invite");
        } finally {
            setCreatingInvite(false);
        }
    }

    async function handleRevoke(invite: AuthInvite) {
        if (!window.confirm(`Revoke invite for ${invite.email}? They will no longer be able to accept this invite.`)) {
            return;
        }
        setBusyInviteId(invite.id);
        setActionError(null);
        setActionMessage(null);
        try {
            await revokeInvite(invite.id);
            setActionMessage(`Revoked invite for ${invite.email}.`);
            setRefreshKey((current) => current + 1);
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not revoke invite");
        } finally {
            setBusyInviteId(null);
        }
    }

    async function handleResend(invite: AuthInvite) {
        setBusyInviteId(invite.id);
        setActionError(null);
        setActionMessage(null);
        try {
            await resendInvite(invite.id);
            setActionMessage(`Invite re-sent to ${invite.email}.`);
            setRefreshKey((current) => current + 1);
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not resend invite");
        } finally {
            setBusyInviteId(null);
        }
    }

    return (
        <section style={t.pageWrap}>
            <div>
                <h2 style={{ margin: 0 }}>Team Access</h2>
                <p style={{ ...t.copy, marginTop: "6px" }}>Send invites and manage who can access the repair desk app.</p>
            </div>

            <div style={{ ...t.formActionsRow, gap: "8px" }}>
                <button type="button" style={statusFilter === "all" ? t.primaryBtn : t.miniBtn} onClick={() => setStatusFilter("all")}>All</button>
                <button type="button" style={statusFilter === "active" ? t.primaryBtn : t.miniBtn} onClick={() => setStatusFilter("active")}>Active users</button>
                <button type="button" style={statusFilter === "pending" ? t.primaryBtn : t.miniBtn} onClick={() => setStatusFilter("pending")}>Pending invites</button>
                <button type="button" style={statusFilter === "expired" ? t.primaryBtn : t.miniBtn} onClick={() => setStatusFilter("expired")}>Expired invites</button>
            </div>

            <form style={{ ...t.panel, display: "grid", gap: "10px" }} onSubmit={handleCreateInvite}>
                <div style={{ display: "grid", gap: "6px" }}>
                    <label htmlFor="invite-name" style={t.meta}>Name (optional)</label>
                    <input
                        id="invite-name"
                        type="text"
                        style={t.input}
                        value={inviteName}
                        onChange={(event) => setInviteName(event.target.value)}
                        placeholder="Tech name"
                        disabled={creatingInvite}
                    />
                </div>
                <div style={{ display: "grid", gap: "6px" }}>
                    <label htmlFor="invite-email" style={t.meta}>Email</label>
                    <input
                        id="invite-email"
                        type="email"
                        style={t.input}
                        value={inviteEmail}
                        onChange={(event) => setInviteEmail(event.target.value)}
                        placeholder="user@techrestoredesk.com"
                        disabled={creatingInvite}
                    />
                </div>
                <div style={{ display: "grid", gap: "6px" }}>
                    <label htmlFor="invite-role" style={t.meta}>Role</label>
                    <select
                        id="invite-role"
                        value={inviteRole}
                        onChange={(event) => setInviteRole(event.target.value as AuthRole)}
                        style={t.input}
                        disabled={creatingInvite}
                    >
                        {INVITE_ROLES.map((role) => (
                            <option key={role} value={role}>
                                {role}
                            </option>
                        ))}
                    </select>
                </div>
                <div style={t.formActionsRow}>
                    <button type="submit" style={t.primaryBtn} disabled={creatingInvite}>
                        {creatingInvite ? "Sending invite..." : "Send invite"}
                    </button>
                </div>
            </form>

            {error ? <div style={t.errorBanner}>{error}</div> : null}
            {actionError ? <div style={t.errorBanner}>{actionError}</div> : null}
            {actionMessage ? (
                <div style={{ ...t.subCard, borderColor: "#34d399", background: "#ecfdf5", color: "#065f46" }}>
                    {actionMessage}
                </div>
            ) : null}

            {filteredInvites.length === 0 ? (
                <div style={t.panel}>No records for this filter.</div>
            ) : (
                <div style={{ ...t.panel, display: "grid", gap: "10px" }}>
                    {filteredInvites.map((invite) => (
                        <article key={invite.id} style={{ ...t.subCard, display: "grid", gap: "8px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", flexWrap: "wrap" }}>
                                <strong>{invite.name || invite.email}</strong>
                                <span style={t.meta}>{new Date(invite.created_at).toLocaleString()}</span>
                            </div>
                            <div style={t.meta}>{invite.email}</div>
                            <div style={t.meta}>Role: {invite.role}</div>
                            <div style={t.meta}>Status: {invite.status}</div>
                            <div style={t.meta}>Expires: {new Date(invite.expires_at).toLocaleString()}</div>
                            {invite.accepted_at ? <div style={t.meta}>Accepted: {new Date(invite.accepted_at).toLocaleString()}</div> : null}
                            <div style={{ ...t.formActionsRow, gap: "8px", flexWrap: "wrap" }}>
                                <button
                                    type="button"
                                    style={t.secondaryBtn}
                                    onClick={() => handleResend(invite)}
                                    disabled={(invite.status !== "pending" && invite.status !== "expired") || busyInviteId === invite.id}
                                >
                                    {busyInviteId === invite.id ? "Sending..." : "Resend"}
                                </button>
                                <button
                                    type="button"
                                    style={t.primaryBtn}
                                    onClick={() => handleRevoke(invite)}
                                    disabled={invite.status !== "pending" || busyInviteId === invite.id}
                                >
                                    {busyInviteId === invite.id ? "Revoking..." : "Revoke"}
                                </button>
                            </div>
                        </article>
                    ))}
                </div>
            )}
        </section>
    );
}
