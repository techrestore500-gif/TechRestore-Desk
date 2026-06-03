import type { AuthRole, AuthUser } from "../api/auth";

export const ROLE_LEVEL: Record<AuthRole, number> = {
    viewer: 10,
    technician: 20,
    front_desk: 30,
    admin: 40,
    owner: 50,
};

export function hasRole(user: AuthUser | null, allowed: AuthRole[]): boolean {
    if (!user?.role) {
        return false;
    }
    return allowed.includes(user.role);
}

export function canViewPricing(user: AuthUser | null): boolean {
    return hasRole(user, ["owner", "admin", "front_desk", "technician", "viewer"]);
}

export function canEditPricing(user: AuthUser | null): boolean {
    return hasRole(user, ["owner", "admin"]);
}

export function canManageInvites(user: AuthUser | null): boolean {
    return hasRole(user, ["owner"]);
}

export function canAccessSettings(user: AuthUser | null): boolean {
    return hasRole(user, ["owner", "admin"]);
}

export function canEditTickets(user: AuthUser | null): boolean {
    return hasRole(user, ["owner", "admin", "front_desk", "technician"]);
}

export function roleLabel(role: AuthRole | null | undefined): string {
    if (!role) {
        return "Unknown";
    }
    if (role === "front_desk") {
        return "Front Desk";
    }
    return role.charAt(0).toUpperCase() + role.slice(1);
}
