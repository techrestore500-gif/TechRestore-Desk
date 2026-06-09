import { FormEvent, ReactNode, useState } from "react";

import { useAuth } from "./AuthProvider";

const MARKET_HOSTNAME = "market.techrestoredesk.com";

function isMarketHost(): boolean {
    return window.location.hostname.toLowerCase() === MARKET_HOSTNAME;
}

export function AuthGate({ children }: { children: ReactNode }) {
    const { authEnabled, isAuthenticated, isBootstrapping, authMessage, loginWithCredentials, dismissAuthMessage } = useAuth();
    const isInvitePath = typeof window !== "undefined" && window.location.pathname.startsWith("/invite/");
    const marketHost = typeof window !== "undefined" && isMarketHost();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!authEnabled) {
        return <>{children}</>;
    }

    if (isInvitePath) {
        return <>{children}</>;
    }

    if (isBootstrapping) {
        return (
            <main style={S.page}>
                <section style={S.card}>
                    <h1 style={S.title}>{marketHost ? "Tech Restore Market" : "Tech Restore Desk"}</h1>
                    <p style={S.copy}>Checking session...</p>
                </section>
            </main>
        );
    }

    if (!isAuthenticated) {
        async function handleLoginSubmit(event: FormEvent<HTMLFormElement>) {
            event.preventDefault();
            if (!email.trim()) {
                setError("Enter your email.");
                return;
            }
            if (!password.trim()) {
                setError("Enter your password.");
                return;
            }

            setSubmitting(true);
            setError(null);
            dismissAuthMessage();
            try {
                await loginWithCredentials(email, password);
                setEmail("");
                setPassword("");
            } catch (requestError) {
                const message = requestError instanceof Error ? requestError.message : "Login failed";
                setError(message);
            } finally {
                setSubmitting(false);
            }
        }

        return (
            <main style={S.page}>
                <section style={S.card}>
                    <h1 style={S.title}>{marketHost ? "Tech Restore Market" : "Tech Restore Desk"}</h1>
                    <p style={S.copy}>
                        {marketHost
                            ? "Sign in to manage market SMS controls."
                            : "Sign in with your invited Tech Restore account."}
                    </p>
                    <form style={S.form} onSubmit={handleLoginSubmit}>
                        <label style={S.label} htmlFor="email">Email</label>
                        <input
                            id="email"
                            type="email"
                            autoComplete="email"
                            value={email}
                            onChange={(event) => {
                                setEmail(event.target.value);
                                if (authMessage) {
                                    dismissAuthMessage();
                                }
                            }}
                            style={S.input}
                            placeholder="you@techrestoredesk.com"
                            disabled={submitting}
                        />
                        <label style={S.label} htmlFor="password">Password</label>
                        <div style={S.passwordWrap}>
                            <input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                autoComplete="current-password"
                                value={password}
                                onChange={(event) => {
                                    setPassword(event.target.value);
                                    if (authMessage) {
                                        dismissAuthMessage();
                                    }
                                }}
                                style={S.passwordInput}
                                placeholder="Enter your password"
                                disabled={submitting}
                            />
                            <button
                                type="button"
                                aria-label={showPassword ? "Hide password" : "Show password"}
                                title={showPassword ? "Hide password" : "Show password"}
                                style={S.eyeButton}
                                onClick={() => setShowPassword((current) => !current)}
                                disabled={submitting}
                            >
                                <EyeIcon hidden={showPassword} />
                            </button>
                        </div>
                        {error ? <p style={S.error}>{error}</p> : null}
                        {!error && authMessage ? <p style={S.error}>{authMessage}</p> : null}
                        <button type="submit" style={S.button} disabled={submitting}>
                            {submitting ? "Signing in..." : "Sign in"}
                        </button>
                    </form>
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
        background: "radial-gradient(circle at 10% 10%, #faf5ec 0%, #e7dac5 45%, #d7cebe 100%)",
        fontFamily: '"Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif',
    },
    card: {
        width: "min(420px, 100%)",
        borderRadius: "18px",
        border: "1px solid rgba(89, 69, 58, 0.18)",
        background: "rgba(255,255,255,0.82)",
        boxShadow: "0 20px 44px rgba(69, 51, 41, 0.18)",
        padding: "26px 24px",
        display: "grid",
        gap: "12px",
    },
    title: {
        margin: 0,
        fontSize: "1.5rem",
        color: "#2a221c",
        letterSpacing: "0.01em",
    },
    copy: {
        margin: 0,
        color: "#6d5a4f",
        lineHeight: 1.4,
    },
    form: {
        display: "grid",
        gap: "10px",
    },
    label: {
        fontSize: "0.85rem",
        color: "#604d42",
        fontWeight: 700,
    },
    input: {
        border: "1px solid #d2c0b2",
        borderRadius: "10px",
        padding: "10px 12px",
        fontSize: "1rem",
        background: "#ffffff",
    },
    passwordWrap: {
        position: "relative" as const,
        display: "flex",
        alignItems: "center",
    },
    passwordInput: {
        border: "1px solid #d2c0b2",
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
        color: "#775e4f",
        cursor: "pointer",
        lineHeight: 0,
    },
    button: {
        border: "none",
        borderRadius: "10px",
        padding: "11px 12px",
        background: "linear-gradient(145deg, var(--brand-600) 0%, var(--brand-700) 100%)",
        color: "#f6f9ff",
        fontSize: "0.95rem",
        fontWeight: 700,
        cursor: "pointer",
    },
    error: {
        margin: 0,
        color: "var(--danger-ink)",
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
