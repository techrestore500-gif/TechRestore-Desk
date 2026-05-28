import { FormEvent, ReactNode, useState } from "react";

import { useAuth } from "./AuthProvider";

export function AuthGate({ children }: { children: ReactNode }) {
    const { authEnabled, isAuthenticated, isBootstrapping, loginWithPassword } = useAuth();
    const [password, setPassword] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

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
        async function handleSubmit(event: FormEvent<HTMLFormElement>) {
            event.preventDefault();
            if (!password.trim()) {
                setError("Enter your repair desk password.");
                return;
            }

            setSubmitting(true);
            setError(null);
            try {
                await loginWithPassword(password);
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
                    <h1 style={S.title}>Tech Restore Desk</h1>
                    <p style={S.copy}>Enter the shared repair desk password to continue.</p>
                    <form style={S.form} onSubmit={handleSubmit}>
                        <label style={S.label} htmlFor="shared-password">Password</label>
                        <input
                            id="shared-password"
                            type="password"
                            autoComplete="current-password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            style={S.input}
                            placeholder="Repair desk password"
                            disabled={submitting}
                        />
                        {error ? <p style={S.error}>{error}</p> : null}
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
};
