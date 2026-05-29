import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { fetchCurrentUser, login, type AuthUser } from "../api/auth";
import { setAuthTokenProvider, setUnauthorizedHandler } from "../api/client";
import { queryClient } from "../lib/queryClient";
import { AUTH_ENABLED } from "./config";
import { clearSession, loadSession, saveSession } from "./session";

type AuthContextValue = {
    authEnabled: boolean;
    isAuthenticated: boolean;
    isBootstrapping: boolean;
    user: AuthUser | null;
    authMessage: string | null;
    loginWithCredentials: (email: string, password: string) => Promise<void>;
    logout: (reason?: string) => void;
    dismissAuthMessage: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
    const initialSession = useMemo(() => loadSession(), []);
    const [accessToken, setAccessToken] = useState<string | null>(initialSession.accessToken);
    const [user, setUser] = useState<AuthUser | null>(initialSession.user);
    const [isBootstrapping, setIsBootstrapping] = useState(AUTH_ENABLED);
    const [authMessage, setAuthMessage] = useState<string | null>(null);

    function clearAuthState(message: string | null = null) {
        setAccessToken(null);
        setUser(null);
        clearSession();
        queryClient.clear();
        setAuthMessage(message);
    }

    useEffect(() => {
        setAuthTokenProvider(() => accessToken);

        if (AUTH_ENABLED) {
            setUnauthorizedHandler(() => {
                clearAuthState("Your session expired. Please sign in again.");
            });
        } else {
            setUnauthorizedHandler(null);
        }

        return () => {
            setAuthTokenProvider(null);
            setUnauthorizedHandler(null);
        };
    }, [accessToken]);

    useEffect(() => {
        if (!AUTH_ENABLED) {
            setIsBootstrapping(false);
            return;
        }

        const token = initialSession.accessToken?.trim() ?? "";
        if (!token) {
            setIsBootstrapping(false);
            return;
        }

        let active = true;
        setAuthTokenProvider(() => token);
        fetchCurrentUser(token)
            .then((sessionUser) => {
                if (!active) {
                    return;
                }
                setAccessToken(token);
                setUser(sessionUser);
                saveSession({ accessToken: token, user: sessionUser });
            })
            .catch(() => {
                if (!active) {
                    return;
                }
                clearAuthState("Your session expired. Please sign in again.");
            })
            .finally(() => {
                if (active) {
                    setIsBootstrapping(false);
                }
            });

        return () => {
            active = false;
        };
    }, [initialSession.accessToken]);

    async function loginWithCredentials(email: string, password: string) {
        const nextEmail = email.trim();
        const nextPassword = password.trim();
        if (!nextEmail) {
            throw new Error("Email is required.");
        }
        if (!nextPassword) {
            throw new Error("Password is required.");
        }

        const response = await login(nextEmail, nextPassword);
        const nextToken = response.access_token?.trim();
        const nextUser = response.user;

        if (!nextToken) {
            throw new Error("Login response did not include an access token.");
        }

        // Avoid a race where protected queries fire before the useEffect refreshes
        // the provider after state updates.
        setAuthTokenProvider(() => nextToken);

        setAccessToken(nextToken);
        setUser(nextUser);
        setAuthMessage(null);
        saveSession({ accessToken: nextToken, user: nextUser });
        queryClient.clear();
    }

    function logout(reason?: string) {
        clearAuthState(reason ?? null);
    }

    function dismissAuthMessage() {
        setAuthMessage(null);
    }

    const value = useMemo<AuthContextValue>(
        () => ({
            authEnabled: AUTH_ENABLED,
            isAuthenticated: !AUTH_ENABLED || Boolean(accessToken),
            isBootstrapping,
            user,
            authMessage,
            loginWithCredentials,
            logout,
            dismissAuthMessage,
        }),
        [accessToken, authMessage, isBootstrapping, user]
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
