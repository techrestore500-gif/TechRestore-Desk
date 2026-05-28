import { apiFetch } from './client';

export type AuthRole = 'owner' | 'admin' | 'technician' | 'front_desk' | 'viewer';
export type AuthStatus = 'pending' | 'active' | 'denied' | 'disabled';

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

export type AccessRequest = {
    id: number;
    name: string;
    email: string;
    username: string;
    status: AuthStatus;
    created_at: string;
};

export type AuthDecisionResponse = {
    message: string;
    user: AuthUser;
};

export async function login(identifier: string, password: string): Promise<LoginResponse> {
    const response = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier, password }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Login failed');
    }

    return response.json() as Promise<LoginResponse>;
}

export async function signupRequest(name: string, email: string, password: string): Promise<{ message: string }> {
    const response = await apiFetch('/api/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Could not submit access request');
    }

    return response.json() as Promise<{ message: string }>;
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

export async function fetchAccessRequests(): Promise<AccessRequest[]> {
    const response = await apiFetch('/api/auth/access-requests');
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to load access requests');
    }
    return response.json() as Promise<AccessRequest[]>;
}

export async function approveAccessRequest(userId: number, role: AuthRole): Promise<AuthDecisionResponse> {
    const response = await apiFetch(`/api/auth/access-requests/${userId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to approve request');
    }
    return response.json() as Promise<AuthDecisionResponse>;
}

export async function denyAccessRequest(userId: number): Promise<AuthDecisionResponse> {
    const response = await apiFetch(`/api/auth/access-requests/${userId}/deny`, {
        method: 'POST',
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Unable to deny request');
    }
    return response.json() as Promise<AuthDecisionResponse>;
}
