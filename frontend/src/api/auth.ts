import { apiFetch } from './client';

export type AuthRole = 'owner' | 'admin' | 'technician' | 'front_desk' | 'viewer';
export type AuthStatus = 'pending' | 'active' | 'denied' | 'disabled';
export type InviteStatus = 'pending' | 'accepted' | 'revoked' | 'expired';

export type AuthUser = {
    id: number;
    name: string;
    email: string;
    username: string;
    role: AuthRole | null;
    status: AuthStatus;
    is_active: boolean;
    approved_at: string | null;
    approved_by: number | null;
    created_at: string;
    updated_at: string;
};

export type LoginResponse = {
    access_token: string;
    token_type: 'bearer';
    expires_at: string;
    user: AuthUser;
};

export type AuthInvite = {
    id: number;
    name: string | null;
    email: string;
    role: AuthRole;
    status: InviteStatus;
    expires_at: string;
    created_at: string;
    created_by: number | null;
    accepted_at: string | null;
    accepted_user_id: number | null;
    revoked_at: string | null;
    invite_link?: string | null;
};

export type AuthDecisionResponse = {
    message: string;
    user: AuthUser;
};

export type InviteResolveResponse = {
    email: string;
    name: string | null;
    role: AuthRole;
    expires_at: string;
};

export async function login(email: string, password: string): Promise<LoginResponse> {
    const response = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Login failed');
    }

    return response.json() as Promise<LoginResponse>;
}

export async function fetchCurrentUser(accessToken: string): Promise<AuthUser> {
    const response = await apiFetch('/api/auth/me', {
        headers: {
            Authorization: `Bearer ${accessToken}`,
        },
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to load session user');
    }

    return response.json() as Promise<AuthUser>;
}

export async function fetchInvites(): Promise<AuthInvite[]> {
    const response = await apiFetch('/api/auth/invites');
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to load invites');
    }
    return response.json() as Promise<AuthInvite[]>;
}

export async function createInvite(email: string, role: AuthRole, name?: string): Promise<AuthInvite> {
    const response = await apiFetch('/api/auth/invites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, role, name: name?.trim() ? name.trim() : undefined }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to create invite');
    }

    return response.json() as Promise<AuthInvite>;
}

export async function revokeInvite(inviteId: number): Promise<AuthInvite> {
    const response = await apiFetch(`/api/auth/invites/${inviteId}/revoke`, {
        method: 'POST',
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to revoke invite');
    }
    return response.json() as Promise<AuthInvite>;
}

export async function resolveInvite(token: string): Promise<InviteResolveResponse> {
    const response = await apiFetch(`/api/auth/invites/${token}`);
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Invite is invalid');
    }
    return response.json() as Promise<InviteResolveResponse>;
}

export async function acceptInvite(token: string, password: string): Promise<AuthDecisionResponse> {
    const response = await apiFetch(`/api/auth/invites/${token}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to accept invite');
    }
    return response.json() as Promise<AuthDecisionResponse>;
}
