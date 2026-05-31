import { FormEvent, useState } from "react";

import { changePassword } from "../api/auth";
import { useAuth } from "../auth/AuthProvider";
import { PageHeader, SectionCard } from "../components/PageChrome";
import * as t from "../styles/theme";

export default function AccountPage() {
    const { user, logout } = useAuth();
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [message, setMessage] = useState<string | null>(null);

    async function handleChangePassword(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (!currentPassword.trim()) {
            setError("Current password is required.");
            return;
        }
        if (!newPassword.trim()) {
            setError("New password is required.");
            return;
        }
        if (newPassword !== confirmPassword) {
            setError("New password and confirm password must match.");
            return;
        }

        setBusy(true);
        setError(null);
        setMessage(null);
        try {
            const response = await changePassword(currentPassword, newPassword, confirmPassword);
            setCurrentPassword("");
            setNewPassword("");
            setConfirmPassword("");
            setMessage(response.message);
            logout("Password changed successfully. Please sign in again.");
        } catch (requestError) {
            setError(requestError instanceof Error ? requestError.message : "Unable to change password");
        } finally {
            setBusy(false);
        }
    }

    return (
        <section style={t.pageWrap}>
            <PageHeader
                kicker="Profile"
                title="Account"
                description="Review your profile, access details, and password controls."
                actions={<button type="button" style={t.secondaryBtn} onClick={() => logout("You have been signed out.")}>Logout</button>}
            />

            <SectionCard title="Profile details" compact>
                <div style={{ display: "grid", gap: "6px" }}>
                    <div><strong>Name:</strong> {user?.name ?? "-"}</div>
                    <div><strong>Email:</strong> {user?.email ?? "-"}</div>
                    <div><strong>Role:</strong> {user?.role ?? "-"}</div>
                </div>
            </SectionCard>

            <SectionCard title="Change Password" description="Use your current password, then set a new password.">
                <form style={{ display: "grid", gap: "12px" }} onSubmit={handleChangePassword}>

                <label style={t.label} htmlFor="account-current-password">
                    Current password
                    <input
                        id="account-current-password"
                        type="password"
                        autoComplete="current-password"
                        style={t.input}
                        value={currentPassword}
                        onChange={(event) => setCurrentPassword(event.target.value)}
                        disabled={busy}
                    />
                </label>

                <label style={t.label} htmlFor="account-new-password">
                    New password
                    <input
                        id="account-new-password"
                        type="password"
                        autoComplete="new-password"
                        style={t.input}
                        value={newPassword}
                        onChange={(event) => setNewPassword(event.target.value)}
                        disabled={busy}
                    />
                </label>

                <label style={t.label} htmlFor="account-confirm-password">
                    Confirm new password
                    <input
                        id="account-confirm-password"
                        type="password"
                        autoComplete="new-password"
                        style={t.input}
                        value={confirmPassword}
                        onChange={(event) => setConfirmPassword(event.target.value)}
                        disabled={busy}
                    />
                </label>

                {error ? <div style={t.errorBanner}>{error}</div> : null}
                {message ? (
                    <div style={{ ...t.subCard, borderColor: "#34d399", background: "#ecfdf5", color: "#065f46" }}>
                        {message}
                    </div>
                ) : null}

                    <div style={t.formActionsRow}>
                        <button type="submit" style={t.primaryBtn} disabled={busy}>
                            {busy ? "Updating password..." : "Change password"}
                        </button>
                    </div>
                </form>
            </SectionCard>
        </section>
    );
}
