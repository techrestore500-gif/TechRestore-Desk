import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { acceptInvite, resolveInvite } from "../api/auth";
import { useAuth } from "../auth/AuthProvider";

const S = {
    page: {
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: "16px",
        background: "radial-gradient(circle at 10% 10%, #f8f2e2 0%, #eadcc2 45%, #ddc7a8 100%)",
        fontFamily: '"Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif',
    },
    card: {
        width: "min(460px, 100%)",
        borderRadius: "18px",
        border: "1px solid rgba(22, 52, 45, 0.18)",
        background: "rgba(255,255,255,0.84)",
        boxShadow: "0 20px 44px rgba(19, 47, 41, 0.22)",
        padding: "26px 24px",
        display: "grid",
        gap: "12px",
    },
    title: {
        margin: 0,
        fontSize: "1.4rem",
        color: "#16322c",
    },
    copy: {
        margin: 0,
        color: "#365a52",
        lineHeight: 1.4,
    },
    label: {
        fontSize: "0.85rem",
        color: "#26463f",
        fontWeight: 700,
    },
    input: {
        border: "1px solid #9fb2ac",
        borderRadius: "10px",
        padding: "10px 12px",
        fontSize: "1rem",
        background: "#ffffff",
        width: "100%",
    },
    button: {
        border: "none",
        borderRadius: "10px",
        padding: "11px 12px",
        background: "linear-gradient(145deg, #1d6557 0%, #18493f 100%)",
        color: "#f7f2e8",
        fontSize: "0.95rem",
        fontWeight: 700,
        cursor: "pointer",
    },
    passwordWrap: {
        position: "relative" as const,
        display: "flex",
        alignItems: "center",
    },
    passwordInput: {
        border: "1px solid #9fb2ac",
        borderRadius: "10px",
        padding: "10px 40px 10px 12px",
        fontSize: "1rem",
        background: "#ffffff",
        width: "100%",
    },
    eyeButton: {
        position: "absolute" as const,
        right: "8px",
        border: "none",
        background: "transparent",
        padding: "4px",
        margin: 0,
        color: "#35574f",
        cursor: "pointer",
        lineHeight: 0,
    },
    error: {
        margin: 0,
        color: "#922f1f",
        fontSize: "0.9rem",
    },
    success: {
        margin: 0,
        color: "#065f46",
        fontSize: "0.9rem",
    },
};

function EyeIcon({ hidden }: { hidden: boolean }) {
    if (hidden) {
        return (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                <path d="M3 3L21 21" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                <path
                    d="M10.58 10.58C10.21 10.95 10 11.46 10 12C10 13.1 10.9 14 12 14C12.54 14 13.05 13.79 13.42 13.42"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                />
                <path
                    d="M9.88 5.09C10.56 4.9 11.27 4.8 12 4.8C16.8 4.8 20.74 8.41 22 12C21.48 13.48 20.58 14.8 19.4 15.84"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                />
                <path
                    d="M14.12 18.91C13.44 19.1 12.73 19.2 12 19.2C7.2 19.2 3.26 15.59 2 12C2.52 10.52 3.42 9.2 4.6 8.16"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                />
            </svg>
        );
    }

    return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <path
                d="M2 12C3.26 8.41 7.2 4.8 12 4.8C16.8 4.8 20.74 8.41 22 12C20.74 15.59 16.8 19.2 12 19.2C7.2 19.2 3.26 15.59 2 12Z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
            />
            <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.8" />
        </svg>
    );
}

export default function InviteAcceptPage() {
    const { token = "" } = useParams();
    const { isAuthenticated, user, logout } = useAuth();
    const [inviteError, setInviteError] = useState<string | null>(null);
    const [inviteEmail, setInviteEmail] = useState("");
    const [inviteRole, setInviteRole] = useState("");
    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [busy, setBusy] = useState(false);
    const [success, setSuccess] = useState<string | null>(null);
    const tokenMissing = useMemo(() => !token.trim(), [token]);

    useEffect(() => {
        if (isAuthenticated) {
            return;
        }
        if (tokenMissing) {
            setInviteError("Invite token is missing.");
            return;
        }

        let active = true;
        resolveInvite(token)
            .then((payload) => {
                if (!active) {
                    return;
                }
                setInviteEmail(payload.email);
                setInviteRole(payload.role);
                setInviteError(null);
            })
            .catch((error: unknown) => {
                if (!active) {
                    return;
                }
                setInviteError(error instanceof Error ? error.message : "Invite is not available.");
            });

        return () => {
            active = false;
        };
    }, [isAuthenticated, token, tokenMissing]);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        if (tokenMissing) {
            setInviteError("Invite token is missing.");
            return;
        }
        if (!password.trim()) {
            setInviteError("Password is required.");
            return;
        }
        if (password !== confirmPassword) {
            setInviteError("Passwords do not match.");
            return;
        }

        setBusy(true);
        setInviteError(null);
        setSuccess(null);
        try {
            const response = await acceptInvite(token, password);
            setSuccess(response.message + " You can now sign in.");
            setPassword("");
            setConfirmPassword("");
        } catch (error: unknown) {
            setInviteError(error instanceof Error ? error.message : "Could not accept invite.");
        } finally {
            setBusy(false);
        }
    }

    return (
        <main style={S.page}>
            <section style={S.card}>
                {isAuthenticated ? (
                    <>
                        <h1 style={S.title}>You are already signed in</h1>
                        <p style={S.copy}>
                            Signed in as {user?.name || "Tech Restore user"} ({user?.email || "no-email"}).
                        </p>
                        <p style={S.copy}>
                            To accept an invite for a different account, sign out first and open the invite link again.
                        </p>
                        <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                            <Link to="/" style={{ color: "#174d43", fontWeight: 700 }}>
                                Go to dashboard
                            </Link>
                            <button type="button" style={S.button} onClick={() => logout("You have been signed out.")}>Sign out</button>
                        </div>
                    </>
                ) : (
                    <>
                        <h1 style={S.title}>Accept Invite</h1>
                        <p style={S.copy}>Set your password to activate your Tech Restore Desk account.</p>
                        {inviteEmail ? (
                            <div style={{ display: "grid", gap: "6px" }}>
                                <label htmlFor="invite-email" style={S.label}>Invited Email</label>
                                <input id="invite-email" type="email" style={S.input} value={inviteEmail} readOnly disabled />
                            </div>
                        ) : null}
                        {inviteRole ? <p style={S.copy}>Role: {inviteRole}</p> : null}
                        {inviteError ? <p style={S.error}>{inviteError}</p> : null}
                        {success ? <p style={S.success}>{success}</p> : null}

                        {!inviteError || success ? (
                            <form onSubmit={handleSubmit} style={{ display: "grid", gap: "10px" }}>
                                <label htmlFor="password" style={S.label}>Password</label>
                                <div style={S.passwordWrap}>
                                    <input
                                        id="password"
                                        type={showPassword ? "text" : "password"}
                                        autoComplete="new-password"
                                        value={password}
                                        onChange={(event) => setPassword(event.target.value)}
                                        style={S.passwordInput}
                                        disabled={busy}
                                    />
                                    <button
                                        type="button"
                                        aria-label={showPassword ? "Hide password" : "Show password"}
                                        title={showPassword ? "Hide password" : "Show password"}
                                        style={S.eyeButton}
                                        onClick={() => setShowPassword((current) => !current)}
                                        disabled={busy}
                                    >
                                        <EyeIcon hidden={showPassword} />
                                    </button>
                                </div>

                                <label htmlFor="confirm-password" style={S.label}>Confirm Password</label>
                                <div style={S.passwordWrap}>
                                    <input
                                        id="confirm-password"
                                        type={showConfirmPassword ? "text" : "password"}
                                        autoComplete="new-password"
                                        value={confirmPassword}
                                        onChange={(event) => setConfirmPassword(event.target.value)}
                                        style={S.passwordInput}
                                        disabled={busy}
                                    />
                                    <button
                                        type="button"
                                        aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                                        title={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                                        style={S.eyeButton}
                                        onClick={() => setShowConfirmPassword((current) => !current)}
                                        disabled={busy}
                                    >
                                        <EyeIcon hidden={showConfirmPassword} />
                                    </button>
                                </div>

                                <button type="submit" style={S.button} disabled={busy}>
                                    {busy ? "Activating..." : "Activate account"}
                                </button>
                            </form>
                        ) : null}

                        <Link to="/login" style={{ color: "#174d43", fontWeight: 700 }}>
                            Back to sign in
                        </Link>
                    </>
                )}
            </section>
        </main>
    );
}
