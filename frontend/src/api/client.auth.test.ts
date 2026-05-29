import { describe, expect, it, vi, afterEach } from "vitest";

import { apiFetch, setAuthTokenProvider, setUnauthorizedHandler } from "./client";

describe("api client auth integration", () => {
    afterEach(() => {
        setAuthTokenProvider(null);
        setUnauthorizedHandler(null);
        vi.restoreAllMocks();
    });

    it("attaches bearer token from shared provider", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
        setAuthTokenProvider(() => "token-123");

        await apiFetch("/api/tickets");

        expect(fetchSpy).toHaveBeenCalledTimes(1);
        const init = fetchSpy.mock.calls[0]?.[1] as RequestInit;
        const headers = new Headers(init.headers);
        expect(headers.get("Authorization")).toBe("Bearer token-123");
    });

    it("does not overwrite explicit authorization header", async () => {
        const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 200 }));
        setAuthTokenProvider(() => "token-123");

        await apiFetch("/api/auth/me", {
            headers: {
                Authorization: "Bearer explicit-token",
            },
        });

        const init = fetchSpy.mock.calls[0]?.[1] as RequestInit;
        const headers = new Headers(init.headers);
        expect(headers.get("Authorization")).toBe("Bearer explicit-token");
    });

    it("invokes unauthorized handler on 401", async () => {
        const onUnauthorized = vi.fn();
        vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 401 }));
        setUnauthorizedHandler(onUnauthorized);
        setAuthTokenProvider(() => "token-123");

        await apiFetch("/api/tickets");

        expect(onUnauthorized).toHaveBeenCalledTimes(1);
    });

    it("does not invoke unauthorized handler on 401 when no token is sent", async () => {
        const onUnauthorized = vi.fn();
        vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 401 }));
        setUnauthorizedHandler(onUnauthorized);
        setAuthTokenProvider(() => null);

        await apiFetch("/api/tickets");

        expect(onUnauthorized).not.toHaveBeenCalled();
    });

    it("invokes unauthorized handler on 401 with explicit authorization header", async () => {
        const onUnauthorized = vi.fn();
        vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("{}", { status: 401 }));
        setUnauthorizedHandler(onUnauthorized);

        await apiFetch("/api/auth/me", {
            headers: {
                Authorization: "Bearer explicit-token",
            },
        });

        expect(onUnauthorized).toHaveBeenCalledTimes(1);
    });
});
