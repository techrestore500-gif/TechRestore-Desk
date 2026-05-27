export type AuthRole = 'admin' | 'technician' | 'front_desk';

export type AuthUser = {
    id: number;
    username: string;
    role: AuthRole;
    is_active: boolean;
    created_at: string;
    updated_at: string;
};

export type LoginResponse = {
    access_token: string;
    token_type: 'bearer';
    expires_at: string;
    user: AuthUser;
};

export async function login(username: string, password: string): Promise<LoginResponse> {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail ?? 'Login failed');
    }

    return response.json() as Promise<LoginResponse>;
}

export async function fetchCurrentUser(accessToken: string): Promise<AuthUser> {
    const response = await fetch('/api/auth/me', {
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
