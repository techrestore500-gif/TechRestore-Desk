import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { CommandPalette } from "./CommandPalette";
import { useAuth } from "../auth/AuthProvider";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";

const navItems = [
    { to: "/", label: "Dashboard" },
    { to: "/intake", label: "New Repair" },
    { to: "/tickets", label: "Tickets" },
    { to: "/queue", label: "Queue" },
    { to: "/hours", label: "Hours" },
    { to: "/reports", label: "Reports" },
    { to: "/inventory", label: "Inventory" },
    { to: "/donors", label: "Donors" },
    { to: "/loaners", label: "Loaners" },
    { to: "/voicemail", label: "Voicemail" },
    { to: "/settings", label: "Settings" },
];

const S = {
    root: {
        display: "flex" as const,
        minHeight: "100vh",
        fontFamily: '"Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif',
        color: "#15211e",
        background: "radial-gradient(circle at 16% 8%, #f9f2df 0%, #efe1c8 38%, #e4d3bd 100%)",
        position: "relative" as const,
    },
    sidebar: {
        width: "210px",
        flexShrink: 0,
        display: "flex" as const,
        flexDirection: "column" as const,
        background: "linear-gradient(180deg, rgba(255,255,255,0.55) 0%, rgba(240,232,218,0.45) 100%)",
        borderRight: "1px solid rgba(24, 34, 30, 0.1)",
        backdropFilter: "blur(4px)",
        position: "sticky" as const,
        top: 0,
        height: "100vh",
        overflowY: "auto" as const,
        zIndex: 20,
    },
    brand: {
        padding: "22px 18px 16px",
        borderBottom: "1px solid rgba(24, 34, 30, 0.08)",
    },
    phase: {
        fontSize: "0.65rem",
        letterSpacing: "0.2em",
        textTransform: "uppercase" as const,
        color: "#5a7268",
        fontWeight: 700,
        marginBottom: "6px",
    },
    appName: {
        fontSize: "1.22rem",
        fontWeight: 800,
        letterSpacing: "0.01em",
        color: "#13312b",
        lineHeight: 1.2,
        margin: 0,
    },
    tagLine: {
        marginTop: "5px",
        fontSize: "0.75rem",
        color: "#4d6760",
        lineHeight: 1.4,
    },
    logoutBtn: {
        marginTop: "10px",
        border: "1px solid rgba(19, 49, 42, 0.24)",
        borderRadius: "9px",
        background: "rgba(255,255,255,0.76)",
        color: "#23443d",
        cursor: "pointer",
        fontSize: "0.78rem",
        fontWeight: 700,
        padding: "6px 10px",
    },
    nav: {
        display: "flex" as const,
        flexDirection: "column" as const,
        gap: "2px",
        padding: "12px 10px",
        flex: 1,
    },
    linkBase: {
        display: "flex" as const,
        alignItems: "center" as const,
        padding: "9px 14px",
        borderRadius: "12px",
        textDecoration: "none",
        color: "#1c3830",
        fontWeight: 600,
        fontSize: "0.92rem",
        letterSpacing: "0.01em",
        transition: "background 140ms ease, color 140ms ease, box-shadow 140ms ease",
        border: "1px solid transparent",
    },
    main: {
        flex: 1,
        minWidth: 0,
        padding: "28px 32px 40px",
    },
    mobileTopBar: {
        display: "flex" as const,
        alignItems: "center" as const,
        justifyContent: "space-between" as const,
        gap: "12px",
        border: "1px solid rgba(19, 49, 42, 0.12)",
        borderRadius: "14px",
        background: "rgba(255,255,255,0.58)",
        padding: "10px 12px",
        marginBottom: "14px",
        boxShadow: "0 8px 18px rgba(19, 47, 41, 0.09)",
        backdropFilter: "blur(4px)",
    },
    menuBtn: {
        border: "1px solid rgba(19, 49, 42, 0.2)",
        borderRadius: "10px",
        background: "linear-gradient(145deg, #1f6657 0%, #184e42 100%)",
        color: "#f4efe4",
        cursor: "pointer",
        padding: "8px 10px",
        fontWeight: 700,
        letterSpacing: "0.01em",
        minWidth: "72px",
    },
    mobilePageTitle: {
        margin: 0,
        fontSize: "0.95rem",
        color: "#1d3a33",
        fontWeight: 700,
    },
    overlay: {
        position: "fixed" as const,
        inset: 0,
        background: "rgba(16, 28, 24, 0.28)",
        border: "none",
        zIndex: 15,
    },
};

export function AppShell() {
    useKeyboardShortcuts();
    const { authEnabled, isAuthenticated, logout } = useAuth();
    const location = useLocation();
    const [isMobile, setIsMobile] = useState(() => window.innerWidth < 960);
    const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 960);

    // Derive current page label for mobile top bar
    const pageLabel = (() => {
        if (location.pathname === "/") return "Dashboard";
        const match = navItems.find((item) => item.to !== "/" && location.pathname.startsWith(item.to));
        return match ? match.label : "Tech Restore Desk";
    })();

    useEffect(() => {
        function handleResize() {
            const mobile = window.innerWidth < 960;
            setIsMobile(mobile);
            setSidebarOpen(!mobile);
        }

        window.addEventListener("resize", handleResize);
        return () => {
            window.removeEventListener("resize", handleResize);
        };
    }, []);

    useEffect(() => {
        if (isMobile) {
            setSidebarOpen(false);
        }
    }, [location.pathname, isMobile]);

    const sidebarStyle = {
        ...S.sidebar,
        ...(isMobile
            ? {
                position: "fixed" as const,
                left: 0,
                top: 0,
                transform: sidebarOpen ? "translateX(0)" : "translateX(-108%)",
                transition: "transform 180ms ease",
                boxShadow: sidebarOpen ? "0 16px 32px rgba(19, 47, 41, 0.24)" : "none",
            }
            : null),
    };

    const mainStyle = {
        ...S.main,
        ...(isMobile ? { padding: "14px 14px 24px" } : null),
    };

    return (
        <div style={S.root}>
            <CommandPalette />
            {isMobile && sidebarOpen ? <button type="button" aria-label="Close navigation" style={S.overlay} onClick={() => setSidebarOpen(false)} /> : null}

            <aside style={sidebarStyle}>
                <div style={S.brand}>
                    <div style={S.phase}>Phase 5 In Progress</div>
                    <div style={S.appName}>Tech Restore<br />Desk</div>
                    <div style={S.tagLine}>Local-first repair workflow</div>
                    {authEnabled && isAuthenticated ? (
                        <button type="button" style={S.logoutBtn} onClick={logout}>
                            Logout
                        </button>
                    ) : null}
                </div>
                <nav style={S.nav}>
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === "/"}
                            style={({ isActive }) => ({
                                ...S.linkBase,
                                background: isActive
                                    ? "linear-gradient(135deg, #1b5045 0%, #163f37 100%)"
                                    : item.to === "/intake"
                                        ? "linear-gradient(145deg, rgba(255,243,217,0.92) 0%, rgba(246,222,180,0.86) 100%)"
                                        : "transparent",
                                color: isActive ? "#f4efe4" : item.to === "/intake" ? "#6b4200" : "#1c3830",
                                boxShadow: isActive
                                    ? "0 6px 14px rgba(17, 54, 47, 0.22)"
                                    : item.to === "/intake"
                                        ? "0 4px 10px rgba(138, 95, 0, 0.15)"
                                        : "none",
                                borderColor: isActive ? "#173f37" : item.to === "/intake" ? "rgba(140, 97, 0, 0.24)" : "transparent",
                            })}
                            onMouseEnter={(e) => {
                                const el = e.currentTarget;
                                if (!el.classList.contains("active")) {
                                    el.style.background = item.to === "/intake"
                                        ? "linear-gradient(145deg, rgba(255,243,217,1) 0%, rgba(246,222,180,0.95) 100%)"
                                        : "rgba(255,255,255,0.6)";
                                }
                            }}
                            onMouseLeave={(e) => {
                                const el = e.currentTarget;
                                if (!el.classList.contains("active")) {
                                    el.style.background = item.to === "/intake"
                                        ? "linear-gradient(145deg, rgba(255,243,217,0.92) 0%, rgba(246,222,180,0.86) 100%)"
                                        : "transparent";
                                }
                            }}
                            onClick={() => {
                                if (isMobile) {
                                    setSidebarOpen(false);
                                }
                            }}
                        >
                            {item.label}
                        </NavLink>
                    ))}
                </nav>
            </aside>

            <main style={mainStyle}>
                {isMobile ? (
                    <div style={S.mobileTopBar}>
                        <button type="button" style={S.menuBtn} onClick={() => setSidebarOpen((current) => !current)}>
                            {sidebarOpen ? "Close" : "Menu"}
                        </button>
                        <h2 style={S.mobilePageTitle}>{pageLabel}</h2>
                    </div>
                ) : null}
                <Outlet />
            </main>
        </div>
    );
}
