const runtimeEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;

function inferRuntimeApiBaseUrl(): string {
    const configured = (runtimeEnv?.VITE_API_BASE_URL ?? "").trim();
    if (configured) {
        return configured;
    }

    if (runtimeEnv?.DEV === "true" || runtimeEnv?.MODE === "development") {
        return "http://127.0.0.1:8787";
    }

    if (typeof window !== "undefined") {
        const host = window.location.hostname;
        if (host.startsWith("desk.")) {
            return `${window.location.protocol}//api.${host.slice("desk.".length)}`;
        }
    }

    return "/api";
}

const RAW_API_BASE_URL = inferRuntimeApiBaseUrl();

export function apiUrl(path: string): string {
    const normalizedPath = path.startsWith("/") ? path : `/${path}`;

    if (/^https?:\/\//i.test(RAW_API_BASE_URL)) {
        const base = RAW_API_BASE_URL.replace(/\/+$/, "");
        const suffix = normalizedPath.startsWith("/api/")
            ? normalizedPath
            : normalizedPath === "/api"
                ? "/api"
                : `/api${normalizedPath}`;
        return `${base}${suffix}`;
    }

    const base = RAW_API_BASE_URL
        ? `/${RAW_API_BASE_URL.replace(/^\/+|\/+$/g, "")}`
        : "/api";

    if (base === "/api" && (normalizedPath === "/api" || normalizedPath.startsWith("/api/"))) {
        return normalizedPath;
    }

    return `${base}${normalizedPath}`.replace(/\/{2,}/g, "/");
}

export function apiFetch(path: string, init?: RequestInit): Promise<Response> {
    return fetch(apiUrl(path), init);
}

export async function getJson<T>(path: string): Promise<T> {
    const response = await apiFetch(path);

    if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
    }

    return (await response.json()) as T;
}