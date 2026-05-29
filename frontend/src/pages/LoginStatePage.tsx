import { Link } from "react-router-dom";

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
        fontSize: "1.35rem",
        color: "#16322c",
    },
    copy: {
        margin: 0,
        color: "#365a52",
        lineHeight: 1.4,
    },
    link: {
        color: "#174d43",
        fontWeight: 700,
        textDecoration: "none",
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
        width: "fit-content",
    },
};

export default function LoginStatePage() {
    const { isAuthenticated, user, logout } = useAuth();

    if (!isAuthenticated) {
        return null;
    }

    return (
        <main style={S.page}>
            <section style={S.card}>
                <h1 style={S.title}>You are already signed in</h1>
                <p style={S.copy}>
                    Signed in as {user?.name || "Tech Restore user"} ({user?.email || "no-email"}).
                </p>
                <Link to="/" style={S.link}>
                    Go to dashboard
                </Link>
                <button type="button" style={S.button} onClick={() => logout("You have been signed out.")}>
                    Sign out
                </button>
            </section>
        </main>
    );
}
