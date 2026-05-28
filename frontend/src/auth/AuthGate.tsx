import { FormEvent, ReactNode, useState } from "react";

import { signupRequest } from "../api/auth";
import { useAuth } from "./AuthProvider";

export function AuthGate({ children }: { children: ReactNode }) {
    const { authEnabled, isAuthenticated, isBootstrapping, loginWithCredentials } = useAuth();
    const [mode, setMode] = useState<"login" | "signup">("login");
    const [identifier, setIdentifier] = useState("");
    const [password, setPassword] = useState("");
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [notice, setNotice] = useState<string | null>(null);

    if (!authEnabled) {
        return <>{children}</>;
    }

    if (isBootstrapping) {
        return (
            <main style={S.page}>
                <section style={S.card}>
                    <h1 style={S.title}>Tech Restore Desk</h1>
                    <p style={S.copy}>Checking session...</p>
                </section>
            </main>
        );
    }

    if (!isAuthenticated) {
        async function handleLoginSubmit(event: FormEvent<HTMLFormElement>) {
            event.preventDefault();
            if (!identifier.trim()) {
                setError("Enter your username or email.");
                return;
            }
            if (!password.trim()) {
                setError("Enter your password.");
                return;
            }

            setSubmitting(true);
            setError(null);
            setNotice(null);
            try {
                await loginWithCredentials(identifier, password);
                setIdentifier("");
                setPassword("");
            } catch (requestError) {
                const message = requestError instanceof Error ? requestError.message : "Login failed";
                setError(message);
            } finally {
                setSubmitting(false);
            }
        }

        async function handleSignupSubmit(event: FormEvent<HTMLFormElement>) {
            event.preventDefault();
            if (!name.trim()) {
                setError("Name is required.");
                return;
            }
            if (!email.trim()) {
                setError("Email is required.");
                return;
            }
            if (!password.trim()) {
                setError("Password is required.");
                return;
            }
            if (password !== confirmPassword) {
                setError("Passwords do not match.");
                return;
            }

            setSubmitting(true);
            setError(null);
            setNotice(null);
            try {
                const response = await signupRequest(name, email, password);
                setNotice(response.message);
                setName("");
                setEmail("");
                setPassword("");
                setConfirmPassword("");
                setMode("login");
            } catch (requestError) {
                const message = requestError instanceof Error ? requestError.message : "Could not submit access request";
                setError(message);
            } finally {
                setSubmitting(false);
            }
        }

        return (
            <main style={S.page}>
                <section style={S.card}>
                    <h1 style={S.title}>Tech Restore Desk</h1>
                    {mode === "login" ? (
                        <>
                            <p style={S.copy}>Sign in with your Tech Restore account.</p>
                            <form style={S.form} onSubmit={handleLoginSubmit}>
                                <label style={S.label} htmlFor="identifier">Username or Email</label>
                                <input
                                    id="identifier"
                                    type="text"
                                    autoComplete="username"
                                    value={identifier}
                                    onChange={(event) => setIdentifier(event.target.value)}
                                    style={S.input}
                                    placeholder="you@techrestoredesk.com"
                                    disabled={submitting}
                                />
                                <label style={S.label} htmlFor="password">Password</label>
                                <input
                                    id="password"
                                    type="password"
                                    autoComplete="current-password"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    style={S.input}
                                    placeholder="Enter your password"
                                    disabled={submitting}
                                />
                                {error ? <p style={S.error}>{error}</p> : null}
                                {notice ? <p style={S.success}>{notice}</p> : null}
                                <button type="submit" style={S.button} disabled={submitting}>
                                    {submitting ? "Signing in..." : "Sign in"}
                                </button>
                            </form>
                            <button
                                type="button"
                                style={S.linkButton}
                                onClick={() => {
                                    setMode("signup");
                                    setError(null);
                                }}
                            >
                                Request access / Sign up
                            </button>
                        </>
                    ) : (
                        <>
                            <p style={S.copy}>Submit an access request. Tech Restore will review and approve your role.</p>
                            <form style={S.form} onSubmit={handleSignupSubmit}>
                                <label style={S.label} htmlFor="signup-name">Name</label>
                                <input
                                    id="signup-name"
                                    type="text"
                                    autoComplete="name"
                                    value={name}
                                    onChange={(event) => setName(event.target.value)}
                                    style={S.input}
                                    placeholder="Your full name"
                                    disabled={submitting}
                                />
                                <label style={S.label} htmlFor="signup-email">Email</label>
                                <input
                                    id="signup-email"
                                    type="email"
                                    autoComplete="email"
                                    value={email}
                                    onChange={(event) => setEmail(event.target.value)}
                                    style={S.input}
                                    placeholder="you@techrestoredesk.com"
                                    disabled={submitting}
                                />
                                <label style={S.label} htmlFor="signup-password">Password</label>
                                <input
                                    id="signup-password"
                                    type="password"
                                    autoComplete="new-password"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    style={S.input}
                                    placeholder="Choose a password"
                                    disabled={submitting}
                                />
                                <label style={S.label} htmlFor="signup-confirm-password">Confirm Password</label>
                                <input
                                    id="signup-confirm-password"
                                    type="password"
                                    autoComplete="new-password"
                                    value={confirmPassword}
                                    onChange={(event) => setConfirmPassword(event.target.value)}
                                    style={S.input}
                                    placeholder="Re-enter your password"
                                    disabled={submitting}
                                />
                                {error ? <p style={S.error}>{error}</p> : null}
                                <button type="submit" style={S.button} disabled={submitting}>
                                    {submitting ? "Submitting..." : "Submit access request"}
                                </button>
                            </form>
                            <button
                                type="button"
                                style={S.linkButton}
                                onClick={() => {
                                    setMode("login");
                                    setError(null);
                                }}
                            >
                                Back to login
                            </button>
                        </>
                    )}
                </section>
            </main>
        );
    }

    return <>{children}</>;
}

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
        width: "min(420px, 100%)",
        borderRadius: "18px",
        border: "1px solid rgba(22, 52, 45, 0.18)",
        background: "rgba(255,255,255,0.82)",
        boxShadow: "0 20px 44px rgba(19, 47, 41, 0.22)",
        padding: "26px 24px",
        display: "grid",
        gap: "12px",
    },
    title: {
        margin: 0,
        fontSize: "1.5rem",
        color: "#16322c",
        letterSpacing: "0.01em",
    },
    copy: {
        margin: 0,
        color: "#365a52",
        lineHeight: 1.4,
    },
    form: {
        display: "grid",
        gap: "10px",
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
    linkButton: {
        marginTop: "4px",
        border: "none",
        background: "transparent",
        padding: 0,
        color: "#174d43",
        textAlign: "left" as const,
        fontWeight: 700,
        cursor: "pointer",
        textDecoration: "underline",
    },
};
