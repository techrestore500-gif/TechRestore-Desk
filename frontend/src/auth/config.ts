const runtimeEnv = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;

function toBool(value: string | undefined, defaultValue: boolean): boolean {
    if (typeof value !== "string") {
        return defaultValue;
    }
    const normalized = value.trim().toLowerCase();
    if (["1", "true", "yes", "on"].includes(normalized)) {
        return true;
    }
    if (["0", "false", "no", "off"].includes(normalized)) {
        return false;
    }
    return defaultValue;
}

export const AUTH_ENABLED = toBool(runtimeEnv?.VITE_AUTH_ENABLED, false);
