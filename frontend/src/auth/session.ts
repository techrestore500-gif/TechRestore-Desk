import type { AuthRole, AuthUser } from '../api/auth';

export type AuthSession = {
    accessToken: string | null;
    user: AuthUser | null;
};

const AUTH_STORAGE_KEY = 'techRestore.auth.session';

export function loadSession(): AuthSession {
    try {
        const raw = localStorage.getItem(AUTH_STORAGE_KEY);
        if (!raw) {
            return { accessToken: null, user: null };
        }
        const parsed = JSON.parse(raw) as AuthSession;
        return {
            accessToken: parsed.accessToken ?? null,
            user: parsed.user ?? null,
        };
    } catch {
        return { accessToken: null, user: null };
    }
}

export function saveSession(session: AuthSession): void {
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session));
}

export function clearSession(): void {
    localStorage.removeItem(AUTH_STORAGE_KEY);
}

export function canAccessRole(user: AuthUser | null, allowedRoles: AuthRole[]): boolean {
    if (!user) {
        return false;
    }
    return allowedRoles.includes(user.role);
}
