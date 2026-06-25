import { FormEvent, useState } from "react";

import { createInvite, type AuthRole } from "../api/auth";
import * as t from "../styles/theme";

const INVITE_ROLES: AuthRole[] = ["viewer", "front_desk", "technician", "manager", "admin", "owner"];

export default function InviteCreatePage() {
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteName, setInviteName] = useState("");
    const [inviteRole, setInviteRole] = useState<AuthRole>("front_desk");
    const [creatingInvite, setCreatingInvite] = useState(false);
    const [actionError, setActionError] = useState<string | null>(null);
    const [actionMessage, setActionMessage] = useState<string | null>(null);

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
        } catch (requestError) {
            setActionError(requestError instanceof Error ? requestError.message : "Could not create invite");
        } finally {
            setCreatingInvite(false);
        }
    }

    return (
        <section style={t.pageWrap}>
            <div>
                <h2 style={{ margin: 0 }}>Create Invite</h2>
                <p style={{ ...t.copy, marginTop: "6px" }}>Invite a new staff member to Tech Restore Desk.</p>
            </div>

            <form style={{ ...t.panel, display: "grid", gap: "10px", maxWidth: "620px" }} onSubmit={handleCreateInvite}>
                <div style={{ display: "grid", gap: "6px" }}>
                    <label htmlFor="invite-name" style={t.meta}>Name (optional)</label>
                    <input
                        id="invite-name"
                        type="text"
                        style={t.input}
                        value={inviteName}
                        onChange={(event) => setInviteName(event.target.value)}
                        placeholder="Technician or staff name"
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
                        placeholder="user@tag.org"
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
                            <option key={role} value={role}>{role}</option>
                        ))}
                    </select>
                </div>
                <div style={t.formActionsRow}>
                    <button type="submit" style={t.primaryBtn} disabled={creatingInvite}>
                        {creatingInvite ? "Sending invite..." : "Send invite"}
                    </button>
                </div>
            </form>

            {actionError ? <div style={t.errorBanner}>{actionError}</div> : null}
            {actionMessage ? (
                <div style={{ ...t.subCard, borderColor: "#34d399", background: "#ecfdf5", color: "#065f46", maxWidth: "620px" }}>
                    {actionMessage}
                </div>
            ) : null}
        </section>
    );
}