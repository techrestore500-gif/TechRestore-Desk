import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { login, type AuthUser } from "../api/auth";
import { setAuthTokenProvider, setUnauthorizedHandler } from "../api/client";
import { queryClient } from "../lib/queryClient";
import { AUTH_ENABLED } from "./config";
import { clearSession, loadSession, saveSession } from "./session";

type AuthContextValue = {
    authEnabled: boolean;
    isAuthenticated: boolean;
    isBootstrapping: boolean;
    user: AuthUser | null;
    loginWithCredentials: (identifier: string, password: string) => Promise<void>;
    logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const initialSession = useMemo(() => loadSession(), []);
    const [accessToken, setAccessToken] = useState<string | null>(initialSession.accessToken);
    const [user, setUser] = useState<AuthUser | null>(initialSession.user);
    const [isBootstrapping] = useState(false);

    useEffect(() => {
        setAuthTokenProvider(() => accessToken);

        if (AUTH_ENABLED) {
            setUnauthorizedHandler(() => {
                setAccessToken(null);
                setUser(null);
                clearSession();
                queryClient.clear();
            });
        } else {
            setUnauthorizedHandler(null);
        }

        return () => {
            setAuthTokenProvider(null);
            setUnauthorizedHandler(null);
        };
    }, [accessToken]);

    async function loginWithCredentials(identifier: string, password: string) {
        const nextIdentifier = identifier.trim();
        const nextPassword = password.trim();
        if (!nextIdentifier) {
            throw new Error("Username or email is required.");
        }
        if (!nextPassword) {
            throw new Error("Password is required.");
        }

        const response = await login(nextIdentifier, nextPassword);
        const nextToken = response.access_token;
        const nextUser = response.user;

        setAccessToken(nextToken);
        setUser(nextUser);
        saveSession({ accessToken: nextToken, user: nextUser });
        queryClient.clear();
    }

    function logout() {
        setAccessToken(null);
        setUser(null);
        clearSession();
        queryClient.clear();
    }

    const value = useMemo<AuthContextValue>(
        () => ({
            authEnabled: AUTH_ENABLED,
            isAuthenticated: !AUTH_ENABLED || Boolean(accessToken),
            isBootstrapping,
            user,
            loginWithCredentials,
            logout,
        }),
        [accessToken, isBootstrapping, user]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within AuthProvider");
    }
    return context;
}
