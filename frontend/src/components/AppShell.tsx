import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { CommandPalette } from "./CommandPalette";
import { useAuth } from "../auth/AuthProvider";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";

const navItems = [
    { to: "/", label: "Dashboard" },
    { to: "/intake", label: "New Repair" },
    { to: "/tickets", label: "Tickets" },
    { to: "/voicemail", label: "Voicemail" },
    { to: "/inventory", label: "Inventory" },
    { to: "/pricing", label: "Pricing" },
    { to: "/operations", label: "Shop Tools" },
    { to: "/reports", label: "Reports" },
    { to: "/users-invites", label: "Team Access" },
    { to: "/settings", label: "Settings" },
];

const navGroups = [
    { label: "Daily Work", items: ["/", "/intake", "/tickets", "/voicemail", "/inventory"] },
    { label: "Shop Tools", items: ["/pricing", "/operations", "/reports"] },
    { label: "Admin", items: ["/users-invites", "/settings"] },
];

const S = {
    root: {
        display: "flex" as const,
        minHeight: "100vh",
        fontFamily: '"Sora", "Plus Jakarta Sans", "Avenir Next", "Trebuchet MS", "Segoe UI", sans-serif',
        color: "#2a221c",
        background: "transparent",
        position: "relative" as const,
        isolation: "isolate" as const,
    },
    auraLayer: {
        position: "fixed" as const,
        inset: 0,
        pointerEvents: "none" as const,
        zIndex: 0,
    },
    auraPrimary: {
        position: "absolute" as const,
        width: "36vw",
        height: "36vw",
        minWidth: "340px",
        minHeight: "340px",
        borderRadius: "50%",
        left: "-8vw",
        top: "-12vw",
        background: "radial-gradient(circle, rgba(124, 135, 100, 0.2) 0%, rgba(124, 135, 100, 0) 70%)",
        filter: "blur(2px)",
        animation: "auraShift 13s ease-in-out infinite",
    },
    auraSecondary: {
        position: "absolute" as const,
        width: "42vw",
        height: "42vw",
        minWidth: "360px",
        minHeight: "360px",
        borderRadius: "50%",
        right: "-12vw",
        bottom: "-20vw",
        background: "radial-gradient(circle, rgba(201, 138, 100, 0.22) 0%, rgba(201, 138, 100, 0) 68%)",
        animation: "auraShift 16s ease-in-out infinite reverse",
    },
    sidebar: {
        width: "286px",
        flexShrink: 0,
        display: "flex" as const,
        flexDirection: "column" as const,
        background: "linear-gradient(180deg, rgba(46, 34, 28, 0.97) 0%, rgba(33, 25, 21, 0.99) 100%)",
        borderRight: "1px solid rgba(201, 138, 100, 0.2)",
        backdropFilter: "blur(14px)",
        position: "sticky" as const,
        top: 0,
        height: "100vh",
        overflowY: "auto" as const,
        zIndex: 20,
        boxShadow: "16px 0 32px rgba(32, 23, 19, 0.34)",
    },
    brand: {
        padding: "24px 18px 17px",
        borderBottom: "1px solid rgba(201, 138, 100, 0.24)",
        background: "linear-gradient(180deg, rgba(155, 95, 69, 0.34) 0%, rgba(16, 31, 37, 0) 100%)",
    },
    phase: {
        fontSize: "0.63rem",
        letterSpacing: "0.24em",
        textTransform: "uppercase" as const,
        color: "#dbc0a9",
        fontWeight: 800,
        marginBottom: "6px",
    },
    appName: {
        fontSize: "1.36rem",
        fontWeight: 800,
        letterSpacing: "-0.02em",
        color: "#fff7f0",
        lineHeight: 1.14,
        margin: 0,
    },
    tagLine: {
        marginTop: "7px",
        fontSize: "0.76rem",
        color: "#d8c7ba",
        lineHeight: 1.4,
    },
    logoutBtn: {
        marginTop: "8px",
        border: "1px solid rgba(167, 176, 141, 0.36)",
        borderRadius: "10px",
        background: "rgba(255,255,255,0.04)",
        color: "#eff0df",
        cursor: "pointer",
        fontSize: "0.78rem",
        fontWeight: 700,
        padding: "6px 10px",
    },
    nav: {
        display: "flex" as const,
        flexDirection: "column" as const,
        gap: "16px",
        padding: "16px 12px 10px",
        flex: 1,
    },
    navGroup: {
        display: "grid" as const,
        gap: "8px",
    },
    navGroupLabel: {
        margin: "0 6px",
        fontSize: "0.64rem",
        letterSpacing: "0.2em",
        textTransform: "uppercase" as const,
        fontWeight: 800,
        color: "#bdaa98",
    },
    profileCard: {
        margin: "12px",
        padding: "12px 12px",
        borderRadius: "14px",
        border: "1px solid rgba(201, 138, 100, 0.2)",
        background: "linear-gradient(160deg, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0.04) 100%)",
        display: "grid" as const,
        gap: "5px",
    },
    profileName: {
        margin: 0,
        fontSize: "0.86rem",
        fontWeight: 750,
        color: "#fff7ef",
        lineHeight: 1.2,
    },
    profileMeta: {
        margin: 0,
        fontSize: "0.74rem",
        color: "#d8c6ba",
        lineHeight: 1.35,
        overflow: "hidden",
        textOverflow: "ellipsis",
    },
    profileActions: {
        marginTop: "6px",
        display: "flex" as const,
        gap: "6px",
        flexWrap: "wrap" as const,
    },
    profileLink: {
        border: "1px solid rgba(167, 176, 141, 0.24)",
        borderRadius: "8px",
        padding: "5px 8px",
        color: "#f2efe8",
        textDecoration: "none",
        fontSize: "0.74rem",
        fontWeight: 700,
        background: "rgba(255,255,255,0.05)",
    },
    linkBase: {
        display: "flex" as const,
        alignItems: "center" as const,
        padding: "11px 13px",
        borderRadius: "12px",
        textDecoration: "none",
        color: "#eadfd6",
        fontWeight: 650,
        fontSize: "0.9rem",
        letterSpacing: "0.01em",
        transition: "background 170ms ease, color 170ms ease, box-shadow 170ms ease, border-color 170ms ease",
        border: "1px solid rgba(201, 138, 100, 0.1)",
        position: "relative" as const,
    },
    main: {
        flex: 1,
        minWidth: 0,
        padding: "28px 30px 40px",
        position: "relative" as const,
        zIndex: 1,
    },
    mobileTopBar: {
        display: "flex" as const,
        alignItems: "center" as const,
        justifyContent: "space-between" as const,
        gap: "12px",
        border: "1px solid rgba(95, 73, 61, 0.16)",
        borderRadius: "14px",
        background: "linear-gradient(150deg, rgba(255,252,247,0.92) 0%, rgba(245,238,228,0.82) 100%)",
        padding: "10px 11px",
        marginBottom: "14px",
        boxShadow: "0 12px 26px rgba(70, 52, 41, 0.14)",
        backdropFilter: "blur(8px)",
    },
    menuBtn: {
        border: "1px solid rgba(111, 63, 47, 0.24)",
        borderRadius: "10px",
        background: "linear-gradient(145deg, var(--brand-500) 0%, var(--brand-700) 100%)",
        color: "#fff8f2",
        cursor: "pointer",
        padding: "8px 10px",
        fontWeight: 700,
        letterSpacing: "0.01em",
        minWidth: "72px",
    },
    mobilePageTitle: {
        margin: 0,
        fontSize: "0.9rem",
        color: "#46352a",
        fontWeight: 750,
    },
    overlay: {
        position: "fixed" as const,
        inset: 0,
        background: "rgba(28, 22, 18, 0.42)",
        border: "none",
        zIndex: 15,
    },
};

export function AppShell() {
    useKeyboardShortcuts();
    const { authEnabled, isAuthenticated, user, logout } = useAuth();
    const location = useLocation();
    const [isMobile, setIsMobile] = useState(() => window.innerWidth < 960);
    const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 960);
    const canManageInvites = user?.role === "owner" || user?.role === "admin";
    const visibleNavItems = navItems.filter((item) => item.to !== "/users-invites" || canManageInvites);
    const groupedNav = useMemo(
        () =>
            navGroups
                .map((group) => ({
                    label: group.label,
                    items: visibleNavItems.filter((item) => group.items.includes(item.to)),
                }))
                .filter((group) => group.items.length > 0),
        [visibleNavItems]
    );

    // Derive current page label for mobile top bar
    const pageLabel = (() => {
        if (location.pathname === "/") return "Dashboard";
        const match = visibleNavItems.find((item) => item.to !== "/" && location.pathname.startsWith(item.to));
        if (match) return match.label;
        if (location.pathname.startsWith("/users-invites")) return "Team Access";
        if (location.pathname.startsWith("/inventory")) return "Inventory";
        if (location.pathname.startsWith("/pricing")) return "Pricing";
        return "Tech Restore Desk";
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
                boxShadow: sidebarOpen ? "0 16px 32px rgba(44, 31, 24, 0.3)" : "none",
            }
            : null),
    };

    const mainStyle = {
        ...S.main,
        ...(isMobile ? { padding: "14px 14px 24px" } : null),
    };

    return (
        <div style={S.root}>
            <div style={S.auraLayer}>
                <div style={S.auraPrimary} />
                <div style={S.auraSecondary} />
            </div>
            <CommandPalette />
            {isMobile && sidebarOpen ? <button type="button" aria-label="Close navigation" style={S.overlay} onClick={() => setSidebarOpen(false)} /> : null}

            <aside style={sidebarStyle}>
                <div style={S.brand}>
                    <div style={S.phase}>Repair Desk Mode</div>
                    <div style={S.appName}>Tech Restore Desk</div>
                    <div style={S.tagLine}>Fast counter workflow for real repair work</div>
                </div>
                <nav style={S.nav}>
                    {groupedNav.map((group) => (
                        <div key={group.label} style={S.navGroup}>
                            <div style={S.navGroupLabel}>{group.label}</div>
                            {group.items.map((item) => (
                                <NavLink
                                    key={item.to}
                                    to={item.to}
                                    end={item.to === "/"}
                                    style={({ isActive }) => ({
                                        ...S.linkBase,
                                        background: isActive
                                            ? "linear-gradient(145deg, #c98a64 0%, #9b5f45 62%, #6f3f2f 100%)"
                                            : item.to === "/intake"
                                                ? "linear-gradient(145deg, rgba(226, 230, 207, 0.98) 0%, rgba(167, 176, 141, 0.92) 100%)"
                                                : "transparent",
                                        color: isActive ? "#fff8f2" : item.to === "/intake" ? "#4f553e" : "#eadfd6",
                                        boxShadow: isActive
                                            ? "0 10px 20px rgba(111, 63, 47, 0.32)"
                                            : item.to === "/intake"
                                                ? "0 9px 17px rgba(93, 102, 71, 0.24)"
                                                : "none",
                                        borderColor: isActive ? "rgba(229, 191, 165, 0.5)" : item.to === "/intake" ? "rgba(167, 176, 141, 0.52)" : "rgba(201, 138, 100, 0.1)",
                                    })}
                                    onMouseEnter={(e) => {
                                        const el = e.currentTarget;
                                        if (!el.classList.contains("active")) {
                                            el.style.background = item.to === "/intake"
                                                ? "linear-gradient(145deg, rgba(233,236,216,1) 0%, rgba(167, 176, 141, 0.96) 100%)"
                                                : "rgba(201, 138, 100, 0.14)";
                                            el.style.borderColor = "rgba(201, 138, 100, 0.3)";
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        const el = e.currentTarget;
                                        if (!el.classList.contains("active")) {
                                            el.style.background = item.to === "/intake"
                                                ? "linear-gradient(145deg, rgba(226, 230, 207, 0.98) 0%, rgba(167, 176, 141, 0.92) 100%)"
                                                : "transparent";
                                            el.style.borderColor = "rgba(201, 138, 100, 0.1)";
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
                        </div>
                    ))}
                </nav>
                {authEnabled && isAuthenticated && user ? (
                    <div style={S.profileCard}>
                        <p style={S.profileName}>{user.name}</p>
                        <p style={S.profileMeta}>{user.email}</p>
                        <p style={S.profileMeta}>Role: {user.role ?? "none"}</p>
                        <div style={S.profileActions}>
                            <NavLink to="/account" style={S.profileLink}>
                                View account
                            </NavLink>
                            <button type="button" style={S.logoutBtn} onClick={() => logout("You have been signed out.")}>
                                Logout
                            </button>
                        </div>
                    </div>
                ) : null}
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
