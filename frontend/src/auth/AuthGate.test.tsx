import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi, afterEach } from "vitest";

import { apiFetch } from "../api/client";
import { AuthGate } from "./AuthGate";
import { AuthProvider } from "./AuthProvider";

vi.mock("./config", () => ({
    AUTH_ENABLED: true,
}));

vi.mock("../api/auth", () => ({
    login: vi.fn(),
    signupRequest: vi.fn(),
}));

import { login, signupRequest } from "../api/auth";

const STORAGE_KEY = "techRestore.auth.session";

const storageStore = new Map<string, string>();

const storageShim = {
    getItem: (key: string) => storageStore.get(key) ?? null,
    setItem: (key: string, value: string) => {
        storageStore.set(key, value);
    },
    removeItem: (key: string) => {
        storageStore.delete(key);
    },
    clear: () => {
        storageStore.clear();
    },
};

function renderGate() {
    const client = new QueryClient();

    return render(
        <QueryClientProvider client={client}>
            <AuthProvider>
                <AuthGate>
                    <div>Protected desk</div>
                </AuthGate>
            </AuthProvider>
        </QueryClientProvider>
    );
}

describe("AuthGate", () => {
    beforeEach(() => {
        Object.defineProperty(globalThis, "localStorage", {
            configurable: true,
            value: storageShim,
        });
    });

    afterEach(() => {
        cleanup();
        localStorage.removeItem(STORAGE_KEY);
        vi.restoreAllMocks();
    });

    it("shows login screen before authentication", async () => {
        renderGate();

        expect(await screen.findByText("Sign in with your Tech Restore account.")).toBeInTheDocument();
        expect(screen.queryByText("Protected desk")).not.toBeInTheDocument();
    });

    it("authenticates with username or email and renders protected app", async () => {
        vi.mocked(login).mockResolvedValue({
            access_token: "shared-token",
            token_type: "bearer",
            expires_at: new Date(Date.now() + 60_000).toISOString(),
            user: {
                id: 0,
                name: "Desk User",
                email: "desk@example.com",
                username: "desk",
                role: "admin",
                status: "active",
                is_active: true,
                approved_at: new Date().toISOString(),
                approved_by: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
            },
        });

        renderGate();

        fireEvent.change(await screen.findByLabelText("Username or Email"), { target: { value: "desk@example.com" } });
        fireEvent.change(await screen.findByLabelText("Password"), { target: { value: "super-secret-password" } });
        fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

        expect(await screen.findByText("Protected desk")).toBeInTheDocument();
        expect(login).toHaveBeenCalledWith("desk@example.com", "super-secret-password");
    });

    it("submits signup request and returns to login with success message", async () => {
        vi.mocked(signupRequest).mockResolvedValue({
            message: "Your access request was submitted. Tech Restore will review it.",
        });

        renderGate();

        fireEvent.click(await screen.findByRole("button", { name: "Request access / Sign up" }));
        fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Pending User" } });
        fireEvent.change(screen.getByLabelText("Email"), { target: { value: "pending@example.com" } });
        fireEvent.change(screen.getByLabelText("Password"), { target: { value: "pending-pass-123" } });
        fireEvent.change(screen.getByLabelText("Confirm Password"), { target: { value: "pending-pass-123" } });
        fireEvent.click(screen.getByRole("button", { name: "Submit access request" }));

        expect(await screen.findByText("Your access request was submitted. Tech Restore will review it.")).toBeInTheDocument();
        expect(signupRequest).toHaveBeenCalledWith("Pending User", "pending@example.com", "pending-pass-123");
    });

    it("returns to login screen when a request gets 401", async () => {
        localStorage.setItem(
            STORAGE_KEY,
            JSON.stringify({
                accessToken: "expired-token",
                user: {
                    id: 0,
                    name: "Desk User",
                    email: "desk@example.com",
                    username: "desk",
                    role: "admin",
                    status: "active",
                    is_active: true,
                    approved_at: new Date().toISOString(),
                    approved_by: null,
                    created_at: new Date().toISOString(),
                    updated_at: new Date().toISOString(),
                },
            })
        );

        vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 401 }));

        renderGate();

        expect(await screen.findByText("Protected desk")).toBeInTheDocument();

        await act(async () => {
            await apiFetch("/api/tickets");
        });

        await waitFor(() => {
            expect(screen.getByText("Sign in with your Tech Restore account.")).toBeInTheDocument();
        });
        expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    });
});
