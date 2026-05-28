import { FormEvent, useState } from "react";

import { createInvite, fetchInvites, revokeInvite, type AuthInvite, type AuthRole } from "../api/auth";
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

    const { data: invites = [], error } = useAsyncData<AuthInvite[]>(() => fetchInvites(), [refreshKey]);

    function inviteLinkFor(invite: AuthInvite): string {
        if (invite.invite_link) {
            return invite.invite_link;
        }
        const base = window.location.origin.replace(/\/$/, "");
        return `${base}/invite/unavailable`;
    }

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
            const link = inviteLinkFor(invite);
            await navigator.clipboard.writeText(link).catch(() => undefined);
            setActionMessage(`Invite created for ${invite.email}. Invite link copied to clipboard.`);
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

    async function handleCopyInvite(invite: AuthInvite) {
        const link = inviteLinkFor(invite);
        try {
            await navigator.clipboard.writeText(link);
            setActionMessage(`Copied invite link for ${invite.email}.`);
        } catch {
            setActionError("Could not copy invite link. Copy it manually from the invite row.");
        }
    }

    return (
        <section style={t.pageWrap}>
            <div>
                <h2 style={{ margin: 0 }}>Users and Invites</h2>
                <p style={{ ...t.copy, marginTop: "6px" }}>Create email invites and manage account onboarding.</p>
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
                        {creatingInvite ? "Creating invite..." : "Create invite"}
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

            {invites.length === 0 ? (
                <div style={t.panel}>No invites yet.</div>
            ) : (
                <div style={{ ...t.panel, display: "grid", gap: "10px" }}>
                    {invites.map((invite) => (
                        <article key={invite.id} style={{ ...t.subCard, display: "grid", gap: "8px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", gap: "10px", flexWrap: "wrap" }}>
                                <strong>{invite.name || invite.email}</strong>
                                <span style={t.meta}>{new Date(invite.created_at).toLocaleString()}</span>
                            </div>
                            <div style={t.meta}>{invite.email}</div>
                            <div style={t.meta}>Role: {invite.role}</div>
                            <div style={t.meta}>Status: {invite.status}</div>
                            <div style={t.meta}>Expires: {new Date(invite.expires_at).toLocaleString()}</div>
                            {invite.status === "pending" ? <div style={t.meta}>Invite link: {inviteLinkFor(invite)}</div> : null}
                            <div style={{ ...t.formActionsRow, gap: "8px", flexWrap: "wrap" }}>
                                <button
                                    type="button"
                                    style={t.secondaryBtn}
                                    onClick={() => handleCopyInvite(invite)}
                                    disabled={invite.status !== "pending"}
                                >
                                    Copy Link
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
