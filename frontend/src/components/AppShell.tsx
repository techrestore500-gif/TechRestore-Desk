import { type FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

import { changePassword, type AuthRole } from "../api/auth";
import { CommandPalette } from "./CommandPalette";
import { useAuth } from "../auth/AuthProvider";
import { canAccessSettings, canManageInvites, roleLabel } from "../auth/roles";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts";

type NavItem = {
    to: string;
    label: string;
    group: "Core" | "Operations" | "Administration";
    hiddenFor?: AuthRole[];
    visibleFor?: AuthRole[];
};

const navItems: NavItem[] = [
    { to: "/", label: "Dashboard", group: "Core" },
    { to: "/intake", label: "New Repair", group: "Core", hiddenFor: ["viewer"] },
    { to: "/tickets", label: "Tickets", group: "Core" },
    { to: "/voicemail", label: "Voicemail", group: "Core", hiddenFor: ["viewer"] },
    { to: "/inventory", label: "Inventory", group: "Operations", hiddenFor: ["viewer"] },
    { to: "/pricing", label: "Pricing", group: "Operations" },
    { to: "/operations", label: "Shop Tools", group: "Operations", hiddenFor: ["viewer"] },
    { to: "/reports", label: "Reports", group: "Operations" },
    { to: "/settings", label: "Settings", group: "Administration", visibleFor: ["owner", "admin"] },
    { to: "/users-invites", label: "Team Access", group: "Administration", visibleFor: ["owner"] },
];

const S = {
    root: {
        display: "flex" as const,
        minHeight: "100vh",
        fontFamily: '"Segoe UI", "Inter", "Helvetica Neue", Arial, sans-serif',
        color: "#111827",
        background: "#f3f4f6",
    },
    sidebar: {
        width: "252px",
        flexShrink: 0,
        display: "flex" as const,
        flexDirection: "column" as const,
        background: "#ffffff",
        borderRight: "1px solid #e5e7eb",
        position: "sticky" as const,
        top: 0,
        height: "100vh",
        overflowY: "auto" as const,
        zIndex: 30,
    },
    brand: {
        padding: "20px 18px 16px",
        borderBottom: "1px solid #e5e7eb",
    },
    appName: {
        fontSize: "1.08rem",
        fontWeight: 700,
        letterSpacing: "0.01em",
        color: "#0f172a",
        lineHeight: 1.2,
        margin: 0,
    },
    tagLine: {
        marginTop: "4px",
        fontSize: "0.78rem",
        color: "#6b7280",
        lineHeight: 1.4,
    },
    nav: {
        display: "flex" as const,
        flexDirection: "column" as const,
        gap: "18px",
        padding: "16px 10px",
        flex: 1,
    },
    navGroup: {
        display: "grid" as const,
        gap: "6px",
    },
    navGroupLabel: {
        margin: "0 8px",
        fontSize: "0.69rem",
        letterSpacing: "0.08em",
        textTransform: "uppercase" as const,
        fontWeight: 700,
        color: "#6b7280",
    },
    linkBase: {
        display: "flex" as const,
        alignItems: "center" as const,
        padding: "10px 12px",
        borderRadius: "9px",
        textDecoration: "none",
        color: "#111827",
        fontWeight: 600,
        fontSize: "0.9rem",
        border: "1px solid transparent",
        transition: "background-color 140ms ease, border-color 140ms ease, color 140ms ease",
    },
    main: {
        flex: 1,
        minWidth: 0,
        padding: "16px 20px 24px",
        display: "grid" as const,
        gridTemplateRows: "auto 1fr",
        gap: "16px",
    },
    topBar: {
        display: "flex" as const,
        alignItems: "center" as const,
        justifyContent: "space-between",
        gap: "12px",
        border: "1px solid #e5e7eb",
        borderRadius: "10px",
        background: "#ffffff",
        padding: "10px 12px",
    },
    menuBtn: {
        border: "1px solid #d1d5db",
        borderRadius: "8px",
        background: "#ffffff",
        color: "#111827",
        cursor: "pointer",
        padding: "8px 11px",
        fontWeight: 600,
        minWidth: "72px",
    },
    pageTitle: {
        margin: 0,
        fontSize: "1rem",
        color: "#111827",
        fontWeight: 700,
    },
    overlay: {
        position: "fixed" as const,
        inset: 0,
        background: "rgba(15, 23, 42, 0.25)",
        border: "none",
        zIndex: 20,
    },
    accountButton: {
        border: "1px solid #d1d5db",
        borderRadius: "8px",
        background: "#ffffff",
        color: "#111827",
        cursor: "pointer",
        padding: "6px 10px",
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        fontWeight: 600,
    },
    avatar: {
        width: "24px",
        height: "24px",
        borderRadius: "999px",
        background: "#334155",
        color: "#ffffff",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: "0.74rem",
        fontWeight: 700,
    },
    accountMenu: {
        position: "absolute" as const,
        right: 0,
        top: "calc(100% + 6px)",
        width: "280px",
        border: "1px solid #e5e7eb",
        borderRadius: "10px",
        background: "#ffffff",
        boxShadow: "0 14px 30px rgba(2, 6, 23, 0.14)",
        padding: "10px",
        display: "grid",
        gap: "8px",
        zIndex: 40,
    },
    accountInfo: {
        borderBottom: "1px solid #e5e7eb",
        paddingBottom: "8px",
        display: "grid",
        gap: "2px",
    },
    accountName: {
        margin: 0,
        fontSize: "0.9rem",
        fontWeight: 700,
        color: "#111827",
    },
    accountEmail: {
        margin: 0,
        fontSize: "0.8rem",
        color: "#6b7280",
        overflow: "hidden",
        textOverflow: "ellipsis",
    },
    accountRole: {
        margin: 0,
        fontSize: "0.78rem",
        color: "#374151",
    },
    menuAction: {
        border: "1px solid #e5e7eb",
        borderRadius: "8px",
        background: "#ffffff",
        color: "#111827",
        textAlign: "left" as const,
        padding: "8px 10px",
        textDecoration: "none",
        fontWeight: 600,
        cursor: "pointer",
    },
    content: {
        minWidth: 0,
    },
    modalOverlay: {
        position: "fixed" as const,
        inset: 0,
        background: "rgba(15, 23, 42, 0.35)",
        display: "grid",
        placeItems: "center",
        zIndex: 80,
        padding: "18px",
    },
    modalCard: {
        width: "min(480px, 100%)",
        borderRadius: "12px",
        border: "1px solid #e5e7eb",
        background: "#ffffff",
        padding: "16px",
        display: "grid",
        gap: "12px",
        boxShadow: "0 18px 42px rgba(2, 6, 23, 0.18)",
    },
    label: {
        display: "grid",
        gap: "6px",
        fontWeight: 600,
        color: "#1f2937",
        fontSize: "0.88rem",
    },
    input: {
        border: "1px solid #d1d5db",
        borderRadius: "8px",
        padding: "10px 12px",
        fontSize: "0.95rem",
    },
    modalActions: {
        display: "flex",
        justifyContent: "flex-end",
        gap: "8px",
        flexWrap: "wrap" as const,
    },
    dangerText: {
        margin: 0,
        color: "#b91c1c",
        fontSize: "0.85rem",
    },
    okText: {
        margin: 0,
        color: "#166534",
        fontSize: "0.85rem",
    },
};

export function AppShell() {
    useKeyboardShortcuts();
    const { authEnabled, isAuthenticated, user, logout } = useAuth();
    const location = useLocation();
    const [isMobile, setIsMobile] = useState(() => window.innerWidth < 960);
    const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth >= 960);
    const [accountMenuOpen, setAccountMenuOpen] = useState(false);
    const [passwordModalOpen, setPasswordModalOpen] = useState(false);
    const [currentPassword, setCurrentPassword] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [passwordBusy, setPasswordBusy] = useState(false);
    const [passwordError, setPasswordError] = useState<string | null>(null);
    const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
    const accountMenuRef = useRef<HTMLDivElement | null>(null);

    const visibleNavItems = useMemo(
        () =>
            navItems.filter((item) => {
                if (item.visibleFor && (!user?.role || !item.visibleFor.includes(user.role))) {
                    return false;
                }
                if (item.hiddenFor && user?.role && item.hiddenFor.includes(user.role)) {
                    return false;
                }
                if (item.to === "/users-invites" && !canManageInvites(user)) {
                    return false;
                }
                if (item.to === "/settings" && !canAccessSettings(user)) {
                    return false;
                }
                return true;
            }),
        [user]
    );

    const groupedNav = useMemo(
        () =>
            ["Core", "Operations", "Administration"]
                .map((group) => ({
                    label: group,
                    items: visibleNavItems.filter((item) => item.group === group),
                }))
                .filter((group) => group.items.length > 0),
        [visibleNavItems]
    );

    // Derive current page label for mobile top bar
    const pageLabel = (() => {
        if (location.pathname === "/") return "Dashboard";
        const match = visibleNavItems.find((item) => item.to !== "/" && location.pathname.startsWith(item.to));
        if (match) return match.label;
        if (location.pathname.startsWith("/account")) return "Account";
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

    useEffect(() => {
        function handleOutsideClick(event: MouseEvent) {
            if (!accountMenuRef.current) {
                return;
            }
            if (!accountMenuRef.current.contains(event.target as Node)) {
                setAccountMenuOpen(false);
            }
        }

        function handleEsc(event: KeyboardEvent) {
            if (event.key === "Escape") {
                setAccountMenuOpen(false);
                setPasswordModalOpen(false);
            }
        }

        window.addEventListener("mousedown", handleOutsideClick);
        window.addEventListener("keydown", handleEsc);
        return () => {
            window.removeEventListener("mousedown", handleOutsideClick);
            window.removeEventListener("keydown", handleEsc);
        };
    }, []);

    async function submitPasswordChange(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setPasswordError(null);
        setPasswordSuccess(null);
        if (!currentPassword.trim()) {
            setPasswordError("Current password is required.");
            return;
        }
        if (!newPassword.trim()) {
            setPasswordError("New password is required.");
            return;
        }
        if (newPassword.trim() !== confirmPassword.trim()) {
            setPasswordError("New password and confirm password must match.");
            return;
        }

        try {
            setPasswordBusy(true);
            const response = await changePassword(currentPassword, newPassword, confirmPassword);
            setPasswordSuccess(response.message);
            setCurrentPassword("");
            setNewPassword("");
            setConfirmPassword("");
            logout("Password changed. Please sign in again.");
        } catch (requestError) {
            setPasswordError(requestError instanceof Error ? requestError.message : "Unable to change password.");
        } finally {
            setPasswordBusy(false);
        }
    }

    const sidebarStyle = {
        ...S.sidebar,
        ...(isMobile
            ? {
                position: "fixed" as const,
                left: 0,
                top: 0,
                transform: sidebarOpen ? "translateX(0)" : "translateX(-108%)",
                transition: "transform 180ms ease",
                boxShadow: sidebarOpen ? "0 8px 28px rgba(2, 6, 23, 0.18)" : "none",
            }
            : null),
    };

    const mainStyle = {
        ...S.main,
        ...(isMobile ? { padding: "12px" } : null),
    };

    const userInitials = user?.name
        ? user.name
            .split(" ")
            .map((part) => part.charAt(0).toUpperCase())
            .join("")
            .slice(0, 2)
        : "U";

    return (
        <div style={S.root}>
            <CommandPalette />
            {isMobile && sidebarOpen ? <button type="button" aria-label="Close navigation" style={S.overlay} onClick={() => setSidebarOpen(false)} /> : null}

            <aside style={sidebarStyle}>
                <div style={S.brand}>
                    <div style={S.appName}>Tech Restore Desk</div>
                    <div style={S.tagLine}>Repair operations workspace</div>
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
                                        background: isActive ? "#0f172a" : "transparent",
                                        color: isActive ? "#ffffff" : "#111827",
                                        borderColor: isActive ? "#0f172a" : "transparent",
                                    })}
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
            </aside>

            <main style={mainStyle}>
                <div style={S.topBar}>
                    <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        {isMobile ? (
                            <button type="button" style={S.menuBtn} onClick={() => setSidebarOpen((current) => !current)}>
                                {sidebarOpen ? "Close" : "Menu"}
                            </button>
                        ) : null}
                        <h2 style={S.pageTitle}>{pageLabel}</h2>
                    </div>

                    {authEnabled && isAuthenticated && user ? (
                        <div style={{ position: "relative" }} ref={accountMenuRef}>
                            <button
                                type="button"
                                aria-label="Open account menu"
                                style={S.accountButton}
                                onClick={() => setAccountMenuOpen((open) => !open)}
                            >
                                <span style={S.avatar}>{userInitials}</span>
                                <span style={{ fontSize: "0.86rem" }}>{user.name}</span>
                            </button>

                            {accountMenuOpen ? (
                                <div role="menu" style={S.accountMenu}>
                                    <div style={S.accountInfo}>
                                        <p style={S.accountName}>{user.name}</p>
                                        <p style={S.accountEmail}>{user.email}</p>
                                        <p style={S.accountRole}>Role: {roleLabel(user.role)}</p>
                                    </div>
                                    <NavLink to="/account" style={S.menuAction} onClick={() => setAccountMenuOpen(false)}>
                                        Account / Profile
                                    </NavLink>
                                    <button
                                        type="button"
                                        style={S.menuAction}
                                        onClick={() => {
                                            setAccountMenuOpen(false);
                                            setPasswordModalOpen(true);
                                        }}
                                    >
                                        Change password
                                    </button>
                                    <button
                                        type="button"
                                        style={S.menuAction}
                                        onClick={() => {
                                            setAccountMenuOpen(false);
                                            logout("You have been signed out.");
                                        }}
                                    >
                                        Logout
                                    </button>
                                </div>
                            ) : null}
                        </div>
                    ) : null}
                </div>

                <div style={S.content}>
                    <Outlet />
                </div>
            </main>

            {passwordModalOpen ? (
                <div style={S.modalOverlay}>
                    <div style={S.modalCard}>
                        <h3 style={{ margin: 0 }}>Change password</h3>
                        <p style={{ margin: 0, color: "#6b7280", fontSize: "0.9rem" }}>
                            Enter your current password and set a new one.
                        </p>
                        <form onSubmit={(event) => void submitPasswordChange(event)} style={{ display: "grid", gap: "10px" }}>
                            <label style={S.label}>
                                Current password
                                <input
                                    type="password"
                                    autoComplete="current-password"
                                    style={S.input}
                                    value={currentPassword}
                                    onChange={(event) => setCurrentPassword(event.target.value)}
                                    disabled={passwordBusy}
                                />
                            </label>
                            <label style={S.label}>
                                New password
                                <input
                                    type="password"
                                    autoComplete="new-password"
                                    style={S.input}
                                    value={newPassword}
                                    onChange={(event) => setNewPassword(event.target.value)}
                                    disabled={passwordBusy}
                                />
                            </label>
                            <label style={S.label}>
                                Confirm new password
                                <input
                                    type="password"
                                    autoComplete="new-password"
                                    style={S.input}
                                    value={confirmPassword}
                                    onChange={(event) => setConfirmPassword(event.target.value)}
                                    disabled={passwordBusy}
                                />
                            </label>
                            {passwordError ? <p style={S.dangerText}>{passwordError}</p> : null}
                            {passwordSuccess ? <p style={S.okText}>{passwordSuccess}</p> : null}
                            <div style={S.modalActions}>
                                <button
                                    type="button"
                                    style={S.menuAction}
                                    onClick={() => {
                                        setPasswordModalOpen(false);
                                        setPasswordError(null);
                                        setPasswordSuccess(null);
                                        setCurrentPassword("");
                                        setNewPassword("");
                                        setConfirmPassword("");
                                    }}
                                >
                                    Cancel
                                </button>
                                <button type="submit" style={S.menuAction} disabled={passwordBusy}>
                                    {passwordBusy ? "Updating..." : "Change password"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            ) : null}
        </div>
    );
}
